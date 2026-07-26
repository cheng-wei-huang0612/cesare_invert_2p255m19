#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hal.h"

#define NWARMUP 50
#define NITERATIONS 300
#define NTESTS 500

void invert25519(uint64_t out[4], const uint64_t in[4]);

static void empty_call(uint64_t out[4], const uint64_t in[4])
    __attribute__((noinline, noclone));

static void empty_call(uint64_t out[4], const uint64_t in[4])
{
    __asm__ volatile("" : : "r"(out), "r"(in) : "memory");
}

static int compare_double(const void *left, const void *right)
{
    const double a = *(const double *)left;
    const double b = *(const double *)right;
    return (a > b) - (a < b);
}

static void print_percentiles(const char *name, double samples[NTESTS])
{
    static const unsigned percentiles[] = {
        1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99
    };
    size_t i;

    qsort(samples, NTESTS, sizeof(samples[0]), compare_double);
    printf("%-10s", name);
    for (i = 0; i < sizeof(percentiles) / sizeof(percentiles[0]); i++) {
        const size_t index = (NTESTS * percentiles[i]) / 100;
        printf(" %9.2f", samples[index]);
    }
    putchar('\n');
}

static int sanity_check(void)
{
    static const uint64_t input[4] = {
        UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX
    };
    static const uint64_t expected[4] = {
        UINT64_C(0x7c8a60dd67c8a600),
        UINT64_C(0x8a60dd67c8a60dd6),
        UINT64_C(0x60dd67c8a60dd67c),
        UINT64_C(0x5d67c8a60dd67c8a)
    };
    uint64_t output[4];

    invert25519(output, input);
    if (memcmp(output, expected, sizeof(output)) != 0) {
        fprintf(stderr, "invert25519 sanity check failed\n");
        return -1;
    }
    return 0;
}

int main(void)
{
    static const uint64_t input[4] = {
        UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX
    };
    uint64_t output[4] = {0, 0, 0, 0};
    double raw[NTESTS];
    double baseline[NTESTS];
    double corrected[NTESTS];
    size_t sample;
    unsigned iteration;

    if (sanity_check() != 0) {
        return EXIT_FAILURE;
    }

    enable_cyclecounter();
    for (sample = 0; sample < NTESTS; sample++) {
        uint64_t t0;
        uint64_t t1;
        uint64_t baseline_total;
        uint64_t raw_total;

        for (iteration = 0; iteration < NWARMUP; iteration++) {
            empty_call(output, input);
            invert25519(output, input);
        }

        t0 = get_cyclecounter();
        for (iteration = 0; iteration < NITERATIONS; iteration++) {
            empty_call(output, input);
        }
        t1 = get_cyclecounter();
        baseline_total = t1 - t0;

        t0 = get_cyclecounter();
        for (iteration = 0; iteration < NITERATIONS; iteration++) {
            invert25519(output, input);
        }
        t1 = get_cyclecounter();
        raw_total = t1 - t0;

        raw[sample] = (double)raw_total / NITERATIONS;
        baseline[sample] = (double)baseline_total / NITERATIONS;
        corrected[sample] = raw_total >= baseline_total
                                ? (double)(raw_total - baseline_total) /
                                      NITERATIONS
                                : 0.0;
    }
    disable_cyclecounter();

    printf("invert25519: %d samples, %d calls/sample\n", NTESTS,
           NITERATIONS);
    printf("cycles/call percentiles\n");
    printf("%-10s", "percentile");
    printf(" %9d %9d %9d %9d %9d %9d %9d %9d %9d %9d %9d\n",
           1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99);
    print_percentiles("raw", raw);
    print_percentiles("baseline", baseline);
    print_percentiles("corrected", corrected);

    return EXIT_SUCCESS;
}
