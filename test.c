#define _GNU_SOURCE

#include <errno.h>
#include <gmp.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define DEFAULT_RANDOM_TESTS UINT64_C(1000000)
#define DEFAULT_SEED UINT64_C(0x25519)
#define FERMAT_RANDOM_TESTS UINT64_C(1024)

void invert25519(uint64_t out[4], const uint64_t in[4]);

struct test_context {
    mpz_t modulus;
    mpz_t exponent;
    mpz_t input;
    mpz_t residue;
    mpz_t expected;
    mpz_t actual;
    mpz_t product;
    mpz_t fermat;
    uint64_t cases;
    uint64_t calls;
};

static void print_words(const char *name, const uint64_t value[4])
{
    fprintf(stderr,
            "%s = 0x%016" PRIx64 "%016" PRIx64 "%016" PRIx64
            "%016" PRIx64 "\n",
            name, value[3], value[2], value[1], value[0]);
}

static int fail_case(const char *label, const char *reason,
                     const uint64_t input[4], const uint64_t expected[4],
                     const uint64_t actual[4])
{
    fprintf(stderr, "FAIL [%s]: %s\n", label, reason);
    print_words("input   ", input);
    print_words("expected", expected);
    print_words("actual  ", actual);
    return -1;
}

static void import_words(mpz_t value, const uint64_t words[4])
{
    mpz_import(value, 4, -1, sizeof(words[0]), 0, 0, words);
}

static void export_words(uint64_t words[4], const mpz_t value)
{
    size_t count = 0;
    memset(words, 0, 4 * sizeof(words[0]));
    mpz_export(words, &count, -1, sizeof(words[0]), 0, 0, value);
}

static int run_case(struct test_context *ctx, const char *label,
                    const uint64_t input[4], int check_fermat)
{
    uint64_t input_copy[4];
    uint64_t output[4];
    uint64_t expected_words[4];
    uint64_t alias[4];

    memcpy(input_copy, input, sizeof(input_copy));
    import_words(ctx->input, input);
    mpz_mod(ctx->residue, ctx->input, ctx->modulus);

    if (mpz_sgn(ctx->residue) == 0) {
        mpz_set_ui(ctx->expected, 0);
    } else if (mpz_invert(ctx->expected, ctx->residue, ctx->modulus) == 0) {
        fprintf(stderr, "GMP unexpectedly found no inverse [%s]\n", label);
        return -1;
    }
    export_words(expected_words, ctx->expected);

    invert25519(output, input);
    ctx->calls++;
    if (memcmp(input, input_copy, sizeof(input_copy)) != 0) {
        return fail_case(label, "input was modified", input_copy,
                         expected_words, output);
    }
    if (memcmp(output, expected_words, sizeof(output)) != 0) {
        return fail_case(label, "GMP inverse mismatch", input_copy,
                         expected_words, output);
    }

    import_words(ctx->actual, output);
    if (mpz_cmp(ctx->actual, ctx->modulus) >= 0) {
        return fail_case(label, "output is not canonical", input_copy,
                         expected_words, output);
    }

    if (mpz_sgn(ctx->residue) != 0) {
        mpz_mul(ctx->product, ctx->residue, ctx->actual);
        mpz_mod(ctx->product, ctx->product, ctx->modulus);
        if (mpz_cmp_ui(ctx->product, 1) != 0) {
            return fail_case(label, "input * output is not 1 modulo p",
                             input_copy, expected_words, output);
        }
    } else if (mpz_sgn(ctx->actual) != 0) {
        return fail_case(label, "zero residue did not return zero",
                         input_copy, expected_words, output);
    }

    if (check_fermat) {
        mpz_powm(ctx->fermat, ctx->residue, ctx->exponent, ctx->modulus);
        if (mpz_cmp(ctx->actual, ctx->fermat) != 0) {
            return fail_case(label, "Fermat inverse mismatch", input_copy,
                             expected_words, output);
        }
    }

    memcpy(alias, input, sizeof(alias));
    invert25519(alias, alias);
    ctx->calls++;
    if (memcmp(alias, expected_words, sizeof(alias)) != 0) {
        return fail_case(label, "in-place alias mismatch", input_copy,
                         expected_words, alias);
    }

    ctx->cases++;
    return 0;
}

static uint64_t splitmix64(uint64_t *state)
{
    uint64_t value;
    *state += UINT64_C(0x9e3779b97f4a7c15);
    value = *state;
    value = (value ^ (value >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    value = (value ^ (value >> 27)) * UINT64_C(0x94d049bb133111eb);
    return value ^ (value >> 31);
}

static int run_fixed_cases(struct test_context *ctx)
{
    static const char *const labels[] = {
        "zero", "one", "p-1", "p", "p+1", "2p-1", "2p", "2p+1",
        "2^255-1", "2^255", "2^256-1"
    };
    mpz_t values[sizeof(labels) / sizeof(labels[0])];
    uint64_t words[4];
    size_t i;
    int result = 0;

    for (i = 0; i < sizeof(values) / sizeof(values[0]); i++) {
        mpz_init(values[i]);
    }

    mpz_set_ui(values[0], 0);
    mpz_set_ui(values[1], 1);
    mpz_sub_ui(values[2], ctx->modulus, 1);
    mpz_set(values[3], ctx->modulus);
    mpz_add_ui(values[4], ctx->modulus, 1);
    mpz_mul_ui(values[5], ctx->modulus, 2);
    mpz_sub_ui(values[5], values[5], 1);
    mpz_mul_ui(values[6], ctx->modulus, 2);
    mpz_add_ui(values[7], values[6], 1);
    mpz_ui_pow_ui(values[8], 2, 255);
    mpz_sub_ui(values[8], values[8], 1);
    mpz_ui_pow_ui(values[9], 2, 255);
    mpz_ui_pow_ui(values[10], 2, 256);
    mpz_sub_ui(values[10], values[10], 1);

    for (i = 0; i < sizeof(values) / sizeof(values[0]); i++) {
        export_words(words, values[i]);
        if (run_case(ctx, labels[i], words, 1) != 0) {
            result = -1;
            break;
        }
    }

    for (i = 0; i < sizeof(values) / sizeof(values[0]); i++) {
        mpz_clear(values[i]);
    }
    return result;
}

static int run_integer_patterns(struct test_context *ctx)
{
    int64_t value;
    uint64_t words[4];

    for (value = -4000; value <= 4000; value++) {
        const uint64_t extension = value < 0 ? UINT64_MAX : 0;
        words[0] = (uint64_t)value;
        words[1] = extension;
        words[2] = extension;
        words[3] = extension;
        if (run_case(ctx, "integer-bit-pattern", words, 1) != 0) {
            fprintf(stderr, "integer value = %" PRId64 "\n", value);
            return -1;
        }
    }
    return 0;
}

static int run_random_cases(struct test_context *ctx, uint64_t count,
                            uint64_t seed)
{
    uint64_t state = seed;
    uint64_t words[4];
    uint64_t i;

    for (i = 0; i < count; i++) {
        words[0] = splitmix64(&state);
        words[1] = splitmix64(&state);
        words[2] = splitmix64(&state);
        words[3] = splitmix64(&state);
        if (run_case(ctx, "random", words, i < FERMAT_RANDOM_TESTS) != 0) {
            fprintf(stderr, "random case = %" PRIu64 ", seed = 0x%016"
                            PRIx64 "\n",
                    i, seed);
            return -1;
        }
    }
    return 0;
}

static void *guarded_page(size_t page_size)
{
    unsigned char *mapping = mmap(NULL, 3 * page_size, PROT_NONE,
                                  MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping == MAP_FAILED) {
        return NULL;
    }
    if (mprotect(mapping + page_size, page_size, PROT_READ | PROT_WRITE) != 0) {
        const int saved_errno = errno;
        munmap(mapping, 3 * page_size);
        errno = saved_errno;
        return NULL;
    }
    return mapping;
}

static int run_guard_page_tests(struct test_context *ctx)
{
    static const uint64_t one[4] = {1, 0, 0, 0};
    const long page_size_long = sysconf(_SC_PAGESIZE);
    size_t page_size;
    unsigned char *input_mapping;
    unsigned char *output_mapping;
    size_t placement;

    if (page_size_long <= 0) {
        fprintf(stderr, "sysconf(_SC_PAGESIZE) failed\n");
        return -1;
    }
    page_size = (size_t)page_size_long;
    input_mapping = guarded_page(page_size);
    output_mapping = guarded_page(page_size);
    if (input_mapping == NULL || output_mapping == NULL) {
        perror("guard-page allocation");
        if (input_mapping != NULL) {
            munmap(input_mapping, 3 * page_size);
        }
        if (output_mapping != NULL) {
            munmap(output_mapping, 3 * page_size);
        }
        return -1;
    }

    for (placement = 0; placement < 2; placement++) {
        const size_t offset = placement == 0 ? 0 : page_size - sizeof(one);
        uint64_t *input = (uint64_t *)(input_mapping + page_size + offset);
        uint64_t *output = (uint64_t *)(output_mapping + page_size + offset);

        memcpy(input, one, sizeof(one));
        memset(output, 0, sizeof(one));
        invert25519(output, input);
        ctx->calls++;
        if (memcmp(input, one, sizeof(one)) != 0 ||
            memcmp(output, one, sizeof(one)) != 0) {
            fprintf(stderr, "FAIL [guard-page]: out-of-place mismatch\n");
            munmap(input_mapping, 3 * page_size);
            munmap(output_mapping, 3 * page_size);
            return -1;
        }

        memcpy(input, one, sizeof(one));
        invert25519(input, input);
        ctx->calls++;
        if (memcmp(input, one, sizeof(one)) != 0) {
            fprintf(stderr, "FAIL [guard-page]: in-place mismatch\n");
            munmap(input_mapping, 3 * page_size);
            munmap(output_mapping, 3 * page_size);
            return -1;
        }
    }

    munmap(input_mapping, 3 * page_size);
    munmap(output_mapping, 3 * page_size);
    return 0;
}

static int parse_u64(const char *text, uint64_t *value)
{
    char *end = NULL;
    unsigned long long parsed;

    errno = 0;
    parsed = strtoull(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0') {
        return -1;
    }
    *value = (uint64_t)parsed;
    return 0;
}

int main(int argc, char **argv)
{
    struct test_context ctx;
    uint64_t random_tests = DEFAULT_RANDOM_TESTS;
    uint64_t seed = DEFAULT_SEED;
    int result = EXIT_FAILURE;

    if (argc != 1 && argc != 3) {
        fprintf(stderr, "usage: %s [random-tests seed]\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (argc == 3 &&
        (parse_u64(argv[1], &random_tests) != 0 ||
         parse_u64(argv[2], &seed) != 0)) {
        fprintf(stderr, "invalid random test count or seed\n");
        return EXIT_FAILURE;
    }

    mpz_inits(ctx.modulus, ctx.exponent, ctx.input, ctx.residue, ctx.expected,
              ctx.actual, ctx.product, ctx.fermat, NULL);
    mpz_ui_pow_ui(ctx.modulus, 2, 255);
    mpz_sub_ui(ctx.modulus, ctx.modulus, 19);
    mpz_sub_ui(ctx.exponent, ctx.modulus, 2);
    ctx.cases = 0;
    ctx.calls = 0;

    printf("Testing invert25519 with GMP reference\n");
    printf("Random inputs: %" PRIu64 ", seed: 0x%016" PRIx64 "\n",
           random_tests, seed);
    fflush(stdout);

    if (run_fixed_cases(&ctx) != 0 ||
        run_integer_patterns(&ctx) != 0 ||
        run_random_cases(&ctx, random_tests, seed) != 0 ||
        run_guard_page_tests(&ctx) != 0) {
        goto cleanup;
    }

    printf("PASS: %" PRIu64 " inputs, %" PRIu64
           " assembly calls, including guard-page checks\n",
           ctx.cases, ctx.calls);
    result = EXIT_SUCCESS;

cleanup:
    mpz_clears(ctx.modulus, ctx.exponent, ctx.input, ctx.residue, ctx.expected,
               ctx.actual, ctx.product, ctx.fermat, NULL);
    return result;
}
