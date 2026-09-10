#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <inttypes.h>

void invert25519(uint64_t out[4], const uint64_t in[4]);
static void empty_call(uint64_t out[4], const uint64_t in[4])
    __attribute__((noinline, noclone));
static void empty_call(uint64_t out[4], const uint64_t in[4]) {
    __asm__ volatile("" : : "r"(out), "r"(in) : "memory");
}
static uint64_t ns(clockid_t clock) {
    struct timespec t;
    if (clock_gettime(clock, &t)) { perror("clock_gettime"); exit(1); }
    return (uint64_t)t.tv_sec * 1000000000 + (uint64_t)t.tv_nsec;
}
static void control(int ctl, int ack, const char *cmd) {
    if (write(ctl, cmd, strlen(cmd)) != (ssize_t)strlen(cmd)) exit(2);
    char c;
    do { if (read(ack, &c, 1) != 1) exit(3); } while (c != '\n');
}
int main(int argc, char **argv) {
    if (argc != 5) return 1;
    const uint64_t count = strtoull(argv[2], NULL, 0);
    const int baseline = !strcmp(argv[1], "empty");
    const uint64_t input[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    const uint64_t expected[4] = {UINT64_C(0x7c8a60dd67c8a600), UINT64_C(0x8a60dd67c8a60dd6), UINT64_C(0x60dd67c8a60dd67c), UINT64_C(0x5d67c8a60dd67c8a)};
    uint64_t out[4] = {0};
    invert25519(out, input);
    if (memcmp(out, expected, sizeof out)) return 4;
    for (unsigned i=0; i<10000; ++i) {
        empty_call(out,input); invert25519(out,input);
    }
    int ctl = open(argv[3], O_RDWR), ack = open(argv[4], O_RDWR);
    if (ctl < 0 || ack < 0) return 5;
    control(ctl, ack, "enable\n");
    uint64_t cpu0 = ns(CLOCK_THREAD_CPUTIME_ID);
    uint64_t wall0 = ns(CLOCK_MONOTONIC_RAW);
    if (baseline) {
        for (uint64_t i=0; i<count; ++i) empty_call(out,input);
    } else {
        for (uint64_t i=0; i<count; ++i) invert25519(out,input);
    }
    uint64_t wall1 = ns(CLOCK_MONOTONIC_RAW);
    uint64_t cpu1 = ns(CLOCK_THREAD_CPUTIME_ID);
    control(ctl, ack, "disable\n");
    printf("{\"mode\":\"%s\",\"calls\":%" PRIu64 ",\"wall_ns\":%" PRIu64 ",\"cpu_ns\":%" PRIu64 ",\"check\":%" PRIu64 "}\n", argv[1],count,wall1-wall0,cpu1-cpu0,out[0]);
    return memcmp(out, expected, sizeof out) != 0;
}
