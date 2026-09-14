# cesare_invert_2p255m19

## Abstract

AArch64/NEON modular inversion modulo **p = 2²⁵⁵ − 19** (`2p255m19`), with
separate recommended schedules for **Pi 4 / Cortex-A72** and **Pi 5 / Cortex-A76**.
The latest native paired benchmarks measure approximately **3917 cycles on
Pi 4-class hardware** and **3275 cycles on Pi 5**. Each recommendation uses the
same C ABI and supports full-width unsigned 256-bit inputs.

The Pi 4 measurement host is specifically a **Raspberry Pi 400 Rev 1.0 at
1.8 GHz**, sharing the Cortex-A72 core family with Pi 4. Pi 5 measurements use
a **Raspberry Pi 5 Model B Rev 1.0 at 2.4 GHz**. These results are from warm-cache,
repeated calls; the preferred schedule differs between the two cores.

The implementations have fixed control flow. An input congruent to zero modulo
p returns zero; other outputs are the canonical inverse in [0, p).

## Select an implementation

| Source | Recommendation | Exported C function |
| --- | --- | --- |
| `invert25519_65a210bb6a4c.s` | Earlier baseline, retained | `invert25519` |
| `invert25519_043d7a693cb3.s` | **Pi 5 / Cortex-A76** | `invert25519` |
| `invert25519_f8a6dea8cb0e.s` | **Pi 4 / Cortex-A72** | `invert25519` |

```c
void invert25519(uint64_t out[4], const uint64_t in[4]);
```

Each array contains four 64-bit limbs, least-significant limb first. `out` and
`in` may refer to the same 32-byte buffer. With separate buffers, the input is
preserved. **Link exactly one implementation** into an application.

The filename suffixes identify the research artifacts, not the SHA-256 prefixes
of these complete published files. [artifacts.json](artifacts.json) records the
actual hashes and recommendations. The two earlier assembly files are unchanged.

```sh
# Select the A72 schedule explicitly; TARGET does not change CPU settings.
make test TARGET=pi4
make bench TARGET=pi4

# Select the A76 schedule (also the default when TARGET is omitted).
make test TARGET=pi5
make bench TARGET=pi5

# Test all three, or select any retained assembly explicitly.
make test-all
make test ASM=invert25519_65a210bb6a4c.s
```

`TARGET=pi4` and `TARGET=pi5` select source files; there is no runtime dispatch
or automatic board detection. The default build directory is separate for each
assembly. A source-selection stamp also forces rebuilding when `TARGET` or `ASM`
changes within a custom `BUILD_DIR`. Use a fresh directory or `make -B` when
changing compiler flags, which Make does not track.

## Setup

```sh
git clone --recursive https://github.com/cheng-wei-huang0612/cesare_invert_2p255m19.git
cd cesare_invert_2p255m19
# For an existing clone:
git submodule update --init
```

On Raspberry Pi OS:

```sh
sudo apt install build-essential binutils libgmp-dev pkg-config python3
```

The paired runner below uses the Linux PMU directly through `perf_event_open`.
It needs `taskset` and permission to open a user-space cycle counter; it does
**not** need the `perf` executable and does not alter governor or frequency limits.
The quick `make bench` still uses the pinned `aarch64-bench` submodule.
The optional historical frequency-locked Pi 5 runner additionally needs `linux-perf`.

## Pi 4 / Pi 5 performance (2026-09-14)

All three published sources were compiled and tested natively on **both hosts**.
The table is **paired baseline-corrected CPU cycles per inversion**, summarized
as the median of six per-run medians. Each run measures 501 samples of 1,000 calls;
three rounds use forward and reverse object link order.

| Source suffix | Pi 400 / A72, 1.8 GHz | Pi 5 / A76, 2.4 GHz |
| --- | ---: | ---: |
| `65a210bb6a4c` | 4546.236 | 3583.988 |
| `043d7a693cb3` | 3997.761 | 3274.993 |
| `f8a6dea8cb0e` | 3917.222 | 3303.463 |

On A72, the new `f8a6dea8cb0e` schedule reduces cycles by
**13.84% versus the earlier baseline** and
**2.01% versus the Pi 5 recommendation**.
On A76, `043d7a693cb3` remains fastest, reducing cycles by
**8.62% versus the baseline**.
The recommended variant ranked first in all six runs on its respective host.
Cycle ratios across different clock rates are not wall-time ratios.

Both machines used GCC 14.2.0-19, CPU 3, and the same source snapshots. Their
compiled implementation `.text` sections are identical. Governors remained
`ondemand`; no frequency limits were changed. Benchmark-before/after readings
were 1.8 GHz and 40.4–42.4 °C on Pi 400, and
2.4 GHz and 62.8–63.9 °C on Pi 5. All captured throttling flags were `0x0`.
These are sampled telemetry, not continuous frequency locking.

The paired runner warms every function, rotates function order each sample,
and subtracts the empty call from the same sample index before computing
percentiles. It rejects failed or multiplexed hardware counters. The primary
input is a fixed nonzero 255-bit value; controls use 1 and `2^255-1`.
Random full-width inputs are used for correctness, not this throughput workload.

| Evidence | Pi 4 / Pi 400 | Pi 5 |
| --- | --- | --- |
| Median and range summary | [summary](benchmarks/20260914/pi4/summary.json) | [summary](benchmarks/20260914/pi5/summary.json) |
| Per-run results and telemetry | [results](benchmarks/20260914/pi4/results.json) | [results](benchmarks/20260914/pi5/results.json) |
| Commands | [commands](benchmarks/20260914/pi4/commands.json) | [commands](benchmarks/20260914/pi5/commands.json) |
| Full snapshots, binaries, raw batches | [pi4.zip](benchmarks/20260914/pi4.zip) | [pi5.zip](benchmarks/20260914/pi5.zip) |

This table is a fresh three-implementation comparison using this repository's
new paired runner. It is separate from both the broader 12-implementation
research comparison and the older measurements below; their samples are not
combined. Minor cycle differences between those harnesses should not be read
as changes to the assembly itself.

## Correctness and artifact provenance

All three implementations passed the existing GMP suite natively on Pi 400 and
Pi 5 on 2026-09-14. The new Pi 4 source also passed in the AArch64
`cesare_ce_dev:arm64` Docker environment with GCC 13.3.0:

```text
PASS: 1008012 inputs, 2016028 assembly calls, including guard-page checks
```

Each test includes 1,000,000 deterministic full-width random inputs (seed
`0x25519`), boundaries around p/2p/2²⁵⁵/2²⁵⁶, unsigned bit patterns of −4000 through
4000, GMP inversion and multiplication checks, selected Fermat inverses,
canonical output, input preservation, aliasing, and guard-page bounds.
Native test logs and binaries are in each archive; the
[Docker result](benchmarks/20260914/docker-pi4.json) records its source/binary hashes.
The Pi 4 run used matching GMP 6.3.0 development files unpacked into a private
temporary sysroot; its compile flags are recorded. No system package change was needed.

The A72 source comes from the audited `P2048inverse` FF window sweep:
**factor 1.5, repeat 2, bottom-up, stepsize 1/3, seam 0, seed 42**.
Only seven complete public-symbol tokens were changed to export `invert25519`.
Every instruction, internal label, directive, alignment and comment is preserved.
[Import provenance](provenance/pi4-import.json) records the original and published
SHA-256 values; [SLOTHY provenance](provenance/pi4-slothy.json) records the original
three optimization passes and settings. The full symbolic → RA → OPT workflow
remains in `P2048inverse/inversion_mod_p25519/ff/invert25519_x24/`.

Offline checks require only Python's standard library:

```sh
make verify-artifacts
python3 scripts/verify_benchmarks.py
```

The artifact check reverses the public-symbol rename and verifies the exact
original SLOTHY output hash. The benchmark check verifies both archives, source
identity, native correctness records, unchanged machine code, and recomputes
all paired quantiles and medians from the saved raw batch counts.

## Rerun on Pi 4 or Pi 5

Run directly on either Linux/AArch64 host:

```sh
python3 scripts/benchmark.py
```

This compiles all three implementations, runs the full GMP suite for each, and
then performs the paired benchmark. Use `sudo` only if the host's PMU permissions
require it. The runner never changes governor/frequency settings and has no
wall-clock fallback when hardware counters are unavailable.

Results go into a new `build/paired-<timestamp>/` directory, with immutable
sources, compiler commands, test binaries, forward/reverse link-order binaries,
every raw sample, summaries, telemetry and SHA-256 inventories. Existing output
directories are rejected. A failed run keeps its logs and reports `status=failed`.

```sh
python3 scripts/benchmark.py --cpu 3 --rounds 3 --samples 501 --batch 1000     --tests 1000000 --output build/my-new-run
```

Options and output format are documented by `python3 scripts/benchmark.py --help`.
The script does not update the reference table automatically. Avoid concurrent
CPU-heavy work on the measurement host.

## Historical Pi 5 measurements (2026-09-10)

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

## Optional frequency-locked Pi 5 cross-check

From the repository directory **on the Pi5**:

```sh
sudo python3 scripts/benchmark_pi5.py
```

This older script compiles the `65a210bb6a4c` and `043d7a693cb3` implementations on the Pi5, pins them to CPU 3, and repeats
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

Use `python3 scripts/benchmark_pi5.py --help` for options. `make bench TARGET=pi5` runs the selected Pi 5 implementation without locking
frequency or performing the additional comparisons. This historical script
requires the `perf` executable; the new paired runner above does not. PERF
permissions may require `sudo`.

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
