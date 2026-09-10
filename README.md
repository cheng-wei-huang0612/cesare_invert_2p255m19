# cesare_invert_2p255m19

## Abstract

We currently achieve modular inversion modulo 2²⁵⁵ − 19 (`2p255m19`) in
approximately **3300 CPU cycles on Raspberry Pi 5 (Cortex-A76)**. Our fastest
implementation measures about **3280 cycles per inversion** in warm-cache,
repeated-call benchmarks, with agreement between hardware cycle counts and
elapsed time measured at fixed CPU frequencies. Serial calls that feed each
output into the next inversion measure about **3306 cycles**. The repository
includes correctness tests and a rerunnable benchmark script.

AArch64/NEON implementations of canonical modular inversion modulo
**p = 2²⁵⁵ − 19**, currently optimized and benchmarked on Raspberry Pi 5
(Cortex-A76). The repository name does not encode a target microarchitecture
or a particular cycle count.

The implementations have fixed control flow and accept unsigned 256-bit inputs.
An input congruent to zero modulo p returns zero; other outputs are the
canonical inverse in [0, p).

## Implementations and ABI

| Source | Exported C function |
|---|---|
| `invert25519_65a210bb6a4c.s` | `invert25519` |
| `invert25519_043d7a693cb3.s` | `invert25519` |

```c
void invert25519(uint64_t out[4], const uint64_t in[4]);
```

Each array contains four 64-bit limbs, least-significant limb first. `out` and
`in` may refer to the same 32-byte buffer. With separate buffers, the input is
preserved.

The filename suffixes are historical identifiers. They no longer match the
SHA-256 prefixes of the complete current files. The benchmark runner records
full content hashes and copies the exact sources used into its output directory.

## Setup

```sh
git clone --recursive https://github.com/cheng-wei-huang0612/cesare_invert_2p255m19.git
cd cesare_invert_2p255m19
```

For an existing clone, initialize the pinned cycle-counter dependency:

```sh
git submodule update --init
```

On Raspberry Pi OS:

```sh
sudo apt install build-essential libgmp-dev pkg-config python3 linux-perf
```

The benchmark runner also requires `taskset` and `vcgencmd`, normally available
on Raspberry Pi OS. Check `perf --version` before running; use a perf installation
compatible with the running kernel.

## Correctness tests

Run both implementations with separate build directories:

```sh
make test CC=cc ASM=invert25519_65a210bb6a4c.s \
    BUILD_DIR=build/test-65a210bb6a4c

make test CC=cc ASM=invert25519_043d7a693cb3.s \
    BUILD_DIR=build/test-043d7a693cb3
```

Both sources export the same function, so link only one implementation into
each executable. The default `make test` selects the first source.

Each test run checks:

- 1,000,000 deterministic full-width random inputs, with seed `0x25519`;
- boundary values around p, 2p, 2²⁵⁵, and 2²⁵⁶;
- the 256-bit two's-complement patterns corresponding to integers −4000 through
  4000, interpreted as **unsigned** inputs;
- GMP reference inverses, canonical output, multiplication modulo p, selected
  Fermat inverses, input preservation, in-place operation, and guard-page bounds.

Both sources passed in `cesare_ce_dev:arm64` Docker and directly on Pi5:

```text
PASS: 1008012 inputs, 2016028 assembly calls, including guard-page checks
```

Override the random count and seed with `TESTS=10000 SEED=0x1234` appended to
either command. Use a fresh build directory, or `make -B`, when changing
compiler flags: Make does not track flag changes as dependencies.

## Raspberry Pi 5 performance

Reference measurements on 2026-09-10 used GCC 14.2.0 with `-O3`, Linux
6.18.39+rpt-rpi-2712, and perf 6.18.39. Both sources were compiled on the Pi5.
The benchmark was pinned to CPU 3; CPU frequency was locked at each setting.

The following table records the actual 2026-09-10 measurements. It is static;
the rerun script does not generate or update it. Values are **baseline-corrected
cycles per call**, summarized as the median of five repetitions:

| Source suffix | Locked frequency | Repository framework | `perf stat` | Elapsed time × frequency |
|---|---:|---:|---:|---:|
| `65a210bb6a4c` | 2.4 GHz | 3584.15 | 3594.71 | 3596.50 |
| `043d7a693cb3` | 2.4 GHz | 3279.80 | 3279.70 | 3281.26 |
| `65a210bb6a4c` | 1.5 GHz | 3584.82 | 3594.90 | 3597.88 |
| `043d7a693cb3` | 1.5 GHz | 3267.41 | 3279.55 | 3282.23 |

The second implementation uses approximately **3280 cycles**, versus **3595
cycles** for the first: about **8.76% fewer cycles** at 2.4 GHz. Baseline-corrected
elapsed time at 2.4 GHz was 1.367 µs versus 1.499 µs per call.

Elapsed-time conversion and `perf stat` agreed within 0.09%; all three methods
agreed within 0.4%. The long-loop perf measurements changed by less than 0.01%
between the two clock settings. Recorded temperature was 55.1–63.9 °C, all
firmware throttling samples were `0x0`, and no measured long loop migrated CPUs.
Hardware counters ran for 100% of the enabled measurement time.

### Measurement method

- Original framework: 500 samples × 300 calls, with 50 warm-up calls per
  sample. The table takes the median of five runs' 50th-percentile values.
- `perf stat`: 2,000,000 calls after warm-up, using `cycles:u`. Counters are
  enabled only around the measurement region; a separate empty-call loop
  supplies the baseline.
- Elapsed time: the same long loop measured with `CLOCK_MONOTONIC_RAW`, minus
  the empty-loop time, then multiplied by the locked CPU frequency.

```text
cycles/call = (inversion cycles − empty-loop cycles) / calls
time-derived cycles/call = (inversion ns − empty-loop ns) / calls × frequency_GHz
```

Both counter methods use the PMU through Linux perf. Wall time also includes
interruptions and descheduling; short-loop percentiles and long-loop averages
can differ slightly. All methods use the original framework's all-one 256-bit
input with warm caches.

## Rerun on Raspberry Pi 5

From the repository directory **on the Pi5**:

```sh
sudo python3 scripts/benchmark_pi5.py
```

This compiles both implementations on the Pi5, pins them to CPU 3, and repeats
all three measurements five times at both 2.4 GHz and 1.5 GHz. It records
raw perf counters, elapsed time, empty-call baselines, source hashes, and
frequency/temperature telemetry in a new `build/benchmark-<timestamp>/` directory.
It also retains the exact source snapshots and compiler commands.

**The script does not generate or update any table.** The table above is the
recorded reference run; inspect new measurements separately. `results.json`
contains the raw timings and metadata; individual log files contain the
original framework's output and perf counters.

The script temporarily changes the shared CPU frequency policy and restores
its original governor and limits when it finishes or receives Ctrl-C/SIGTERM.
SIGKILL or power loss cannot run cleanup. It makes no persistent boot changes.
Avoid other CPU-heavy work during measurement.

Use `python3 scripts/benchmark_pi5.py --help` for options. The original
`make bench` still runs a quick first-implementation benchmark without locking
frequency or performing the additional comparisons. PERF permissions may
require `sudo`.

## Security status

This software is a research artifact. It has been extensively tested, but has
not been formally verified or independently audited. Users are responsible for
independent validation before production use.

## License

Required Notice: Copyright 2026 Cesare Huang

Except for the `aarch64-bench` submodule, this repository is source-available
under the [PolyForm Noncommercial License 1.0.0](LICENSE). Commercial use
requires a separate written license; contact
[Cesarehuang@icloud.com](mailto:Cesarehuang@icloud.com).

The `aarch64-bench` submodule remains under its upstream licenses.
