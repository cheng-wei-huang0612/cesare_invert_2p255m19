/* Native Linux/AArch64 user-cycle measurements with paired empty subtraction. */
#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <linux/perf_event.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>

#ifndef BENCH_SAMPLES
#define BENCH_SAMPLES 501
#endif
#ifndef BENCH_BATCH
#define BENCH_BATCH 1000
#endif
#if BENCH_SAMPLES < 3 || BENCH_SAMPLES % 2 != 1 || BENCH_BATCH < 1
#error "Use an odd sample count >= 3 and a positive batch size"
#endif

enum { NF = 4, EMPTY = NF - 1, WARMUP = 20 };
typedef void (*inversion_fn)(uint64_t *, const uint64_t *);
extern void bench_65a210bb6a4c(uint64_t *, const uint64_t *);
extern void bench_043d7a693cb3(uint64_t *, const uint64_t *);
extern void bench_f8a6dea8cb0e(uint64_t *, const uint64_t *);
extern void bench_empty(uint64_t *, const uint64_t *);
static const inversion_fn functions[NF] = {
    bench_65a210bb6a4c, bench_043d7a693cb3, bench_f8a6dea8cb0e, bench_empty,
};
static const char *const names[NF] = {
    "65a210bb6a4c", "043d7a693cb3", "f8a6dea8cb0e", "empty",
};
static const char *const input_names[] = { "main", "one", "max255" };
static const uint64_t inputs[][4] = {
    { UINT64_C(0x0123456789abcdef), UINT64_C(0xfedcba9876543210),
      UINT64_C(0x0f1e2d3c4b5a6978), UINT64_C(0x7766554433221100) },
    { 1, 0, 0, 0 },
    { UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_C(0x7fffffffffffffff) },
};
static uint64_t output[4] __attribute__((aligned(16)));
static uint64_t raw[NF][BENCH_SAMPLES];
static volatile uint64_t sink;
static int perf_fd = -1;

static void fail(const char *message)
{
    fprintf(stderr, "benchmark: %s\n", message);
    exit(EXIT_FAILURE);
}

static void syscall_failure(const char *operation)
{
    fprintf(stderr, "benchmark: %s: %s\n", operation, strerror(errno));
    exit(EXIT_FAILURE);
}

static void counter_ioctl(unsigned long request, const char *operation)
{
    if (ioctl(perf_fd, request, 0) == -1) syscall_failure(operation);
}

static void enable_counter(void)
{
    struct perf_event_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.size = sizeof(attr);
    attr.type = PERF_TYPE_HARDWARE;
    attr.config = PERF_COUNT_HW_CPU_CYCLES;
    attr.disabled = 1;
    attr.pinned = 1;
    attr.exclude_kernel = 1;
    attr.exclude_hv = 1;
    attr.read_format = PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
    perf_fd = (int)syscall(SYS_perf_event_open, &attr, 0, -1, -1, PERF_FLAG_FD_CLOEXEC);
    if (perf_fd == -1) {
        fprintf(stderr, "Cannot open the user-space hardware cycle counter. "
                "Check perf_event permissions and PMU availability; no timer fallback is used.\n");
        syscall_failure("perf_event_open");
    }
    counter_ioctl(PERF_EVENT_IOC_RESET, "PERF_EVENT_IOC_RESET");
    counter_ioctl(PERF_EVENT_IOC_ENABLE, "PERF_EVENT_IOC_ENABLE");
}

static uint64_t get_counter(void)
{
    struct { uint64_t value, enabled, running; } reading;
    ssize_t bytes;
    /* Match the research harness's disable/read/enable counter boundaries. */
    counter_ioctl(PERF_EVENT_IOC_DISABLE, "PERF_EVENT_IOC_DISABLE");
    do {
        bytes = read(perf_fd, &reading, sizeof(reading));
    } while (bytes == -1 && errno == EINTR);
    if (bytes == -1) syscall_failure("read cycle counter");
    if (bytes != (ssize_t)sizeof(reading)) fail("short/empty hardware counter read");
    if (reading.running == 0 || reading.enabled != reading.running)
        fail("hardware cycle counter did not run continuously; refusing multiplexed results");
    counter_ioctl(PERF_EVENT_IOC_ENABLE, "PERF_EVENT_IOC_ENABLE");
    return reading.value;
}

__attribute__((noinline)) static uint64_t measure(inversion_fn fn, const uint64_t *input)
{
    uint64_t start = get_counter();
    for (int i = 0; i < BENCH_BATCH; ++i) fn(output, input);
    uint64_t end = get_counter();
    sink ^= output[0];
    if (end <= start || end - start > INT64_MAX) fail("invalid/non-advancing cycle counter");
    return end - start;
}

static int compare_i64(const void *a, const void *b)
{
    int64_t x = *(const int64_t *)a, y = *(const int64_t *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv)
{
    int input = 0;
    if (argc == 2 && strlen(argv[1]) == 1 && argv[1][0] >= '0' && argv[1][0] <= '2') {
        input = argv[1][0] - '0';
    } else if (argc != 1) {
        fprintf(stderr, "usage: %s [0=main|1=one|2=max255]\n", argv[0]);
        return EXIT_FAILURE;
    }
    enable_counter();
    for (int j = 0; j < WARMUP; ++j)
        for (int k = 0; k < NF; ++k) (void)measure(functions[k], inputs[input]);
    for (int j = 0; j < BENCH_SAMPLES; ++j)
        for (int k = 0; k < NF; ++k) {
            int f = (j + k) % NF;
            raw[f][j] = measure(functions[f], inputs[input]);
        }
    counter_ioctl(PERF_EVENT_IOC_DISABLE, "PERF_EVENT_IOC_DISABLE");
    if (close(perf_fd) == -1) syscall_failure("close cycle counter");

    printf("{\"input\":\"%s\",\"input_words_le\":[", input_names[input]);
    for (int j = 0; j < 4; ++j)
        printf("%s\"0x%016" PRIx64 "\"", j ? "," : "", inputs[input][j]);
    printf("],\"samples\":%d,\"batch\":%d,\"warmup_batches_per_function\":%d,"
           "\"counter\":\"PERF_COUNT_HW_CPU_CYCLES:user:pinned\",\"measurements\":[\n",
           BENCH_SAMPLES, BENCH_BATCH, WARMUP);
    for (int f = 0; f < NF; ++f) {
        int64_t net[BENCH_SAMPLES], raw_sorted[BENCH_SAMPLES], delta[BENCH_SAMPLES];
        for (int j = 0; j < BENCH_SAMPLES; ++j) {
            raw_sorted[j] = (int64_t)raw[f][j];
            net[j] = (int64_t)raw[f][j] - (int64_t)raw[EMPTY][j];
            delta[j] = (int64_t)raw[f][j] - (int64_t)raw[0][j];
        }
        qsort(net, BENCH_SAMPLES, sizeof(net[0]), compare_i64);
        qsort(raw_sorted, BENCH_SAMPLES, sizeof(raw_sorted[0]), compare_i64);
        qsort(delta, BENCH_SAMPLES, sizeof(delta[0]), compare_i64);
        printf("%s{\"name\":\"%s\",\"net_p10\":%.6f,\"net_p50\":%.6f,"
               "\"net_p90\":%.6f,\"raw_p10\":%.6f,\"raw_p50\":%.6f,"
               "\"raw_p90\":%.6f,\"delta_baseline_p50\":%.6f,\"raw_batch_cycles\":[",
               f ? ",\n" : "", names[f], net[BENCH_SAMPLES / 10] / (double)BENCH_BATCH,
               net[BENCH_SAMPLES / 2] / (double)BENCH_BATCH,
               net[9 * BENCH_SAMPLES / 10] / (double)BENCH_BATCH,
               raw_sorted[BENCH_SAMPLES / 10] / (double)BENCH_BATCH,
               raw_sorted[BENCH_SAMPLES / 2] / (double)BENCH_BATCH,
               raw_sorted[9 * BENCH_SAMPLES / 10] / (double)BENCH_BATCH,
               delta[BENCH_SAMPLES / 2] / (double)BENCH_BATCH);
        for (int j = 0; j < BENCH_SAMPLES; ++j)
            printf("%s%" PRIu64, j ? "," : "", raw[f][j]);
        printf("]}");
    }
    printf("\n]}\n");
    return EXIT_SUCCESS;
}
