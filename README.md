# invert25519

This repository contains a fast AArch64/NEON implementation of canonical
inversion modulo

\[
p = 2^{255} - 19.
\]

The implementation has fixed control flow and accepts every unsigned 256-bit
input. Inputs congruent to zero modulo \(p\) return zero.

## C ABI

```c
void invert25519(uint64_t out[4], const uint64_t in[4]);
```

`out` and `in` may point to the same 32-byte buffer. The input is not modified
when the buffers do not overlap.

## Clone

The cycle-counter backend is included as a pinned Git submodule:

```sh
git clone --recursive https://github.com/cheng-wei-huang0612/invert25519_3700.git
cd invert25519_3700
```

If the repository was cloned without `--recursive`, initialize it with:

```sh
git submodule update --init
```

## Correctness test

On Raspberry Pi OS, install the build and GMP development packages:

```sh
sudo apt install build-essential libgmp-dev pkg-config
```

Then run:

```sh
make test
```

The default test compares against GMP on 1,000,000 deterministic full-width
random inputs, boundary values around \(p\) and \(2p\), and the 256-bit
two's-complement bit patterns produced by the C integers from -4000 through
4000. These bit patterns are always interpreted as unsigned inputs: for
example, the all-one representation of `-1` is tested as \(2^{256}-1\), not
as the mathematical integer \(-1\).

The test also checks canonical output, multiplication modulo \(p\), selected
Fermat inverses, preservation of a separate input buffer, in-place operation,
and guard-page boundaries. The random count and seed can be overridden:

```sh
make test TESTS=10000 SEED=0x1234
```

The default test on a Raspberry Pi 5 completed with:

```text
PASS: 1008012 inputs, 2016028 assembly calls, including guard-page checks
```

## Raspberry Pi 5 benchmark

Run the benchmark directly on a Raspberry Pi 5:

```sh
make bench
```

The target uses Linux `perf_event_open` through the pinned
[`aarch64-bench`](https://github.com/mkannwischer/aarch64-bench) HAL and pins
the process to CPU 3. It reports raw call cost, an empty-function baseline,
and baseline-corrected cycles per call at the 1st through 99th percentiles.

The benchmark defaults to 500 samples, with 50 warm-up calls and 300 measured
calls per sample. A different core can be selected with, for example,
`make bench BENCH_CPU=2`.

On a Raspberry Pi 5 / Cortex-A76, one reference run produced median values of
3679.56 raw cycles, a 3.30-cycle empty-function baseline, and 3676.26 corrected
cycles per call.

If PERF access is disabled by the system configuration, check
`/proc/sys/kernel/perf_event_paranoid`. The benchmark counts only user-space
cycles and does not require direct user-mode access to the architectural PMU
registers.
