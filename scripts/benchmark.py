#!/usr/bin/env python3
"""Compile, validate and compare all three inversions on Linux/AArch64.

This runner reads user-space hardware CPU cycles through perf_event_open; it
does not require the perf executable or change governor/frequency settings.
GMP headers/libraries, cc, objcopy and taskset must already be installed.
"""
import argparse
from collections import defaultdict
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import signal
from statistics import median
import subprocess
import time


REPO = Path(__file__).resolve().parents[1]
VARIANTS = ("65a210bb6a4c", "043d7a693cb3", "f8a6dea8cb0e")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, data):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def read_optional(path):
    try:
        return Path(path).read_bytes().rstrip(b"\x00\n").decode(errors="replace")
    except OSError as exc:
        return {"unavailable": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", type=int, default=3, help="benchmark/test CPU (default: 3)")
    parser.add_argument("--control-cpu", type=int, default=0, help="runner/compiler CPU (default: 0)")
    parser.add_argument("--rounds", type=int, default=3, help="rounds, each using both link orders")
    parser.add_argument("--samples", type=int, default=501, help="odd sample count >= 3")
    parser.add_argument("--batch", type=int, default=1000, help="calls per sample")
    parser.add_argument("--tests", type=int, default=1_000_000, help="GMP random cases per variant")
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x25519)
    parser.add_argument("--timeout", type=float, default=600, help="seconds per subprocess")
    parser.add_argument("--output", type=Path, help="new output directory; must not exist")
    args = parser.parse_args()
    if args.rounds <= 0 or args.batch <= 0 or args.tests < 0 or args.timeout <= 0:
        parser.error("rounds, batch and timeout must be positive; tests must be nonnegative")
    if args.samples < 3 or args.samples % 2 != 1:
        parser.error("samples must be odd and >= 3")
    if args.samples > 100_001 or args.batch > 2_147_483_647:
        parser.error("samples or batch exceeds the C harness limits")
    if not 0 <= args.seed <= 2**64 - 1 or args.tests > 2**64 - 1:
        parser.error("seed and tests must fit unsigned 64-bit integers")
    if platform.system() != "Linux" or platform.machine() != "aarch64":
        parser.error("run directly on a Linux/AArch64 host, such as Pi 4 or Pi 5")
    allowed = os.sched_getaffinity(0)
    if args.cpu == args.control_cpu or {args.cpu, args.control_cpu} - allowed:
        parser.error(f"choose distinct CPUs from the available set: {sorted(allowed)}")
    for executable in ("cc", "objcopy", "taskset"):
        if not shutil.which(executable):
            parser.error(f"missing prerequisite: {executable}")
    relative_sources = [Path(f"invert25519_{variant}.s") for variant in VARIANTS]
    relative_sources += [Path("test.c"), Path("scripts/benchmark.py"),
                         Path("scripts/bench_paired.c"), Path("scripts/bench_empty.s")]
    for relative in relative_sources:
        if not (REPO / relative).is_file():
            parser.error(f"missing source: {relative}")

    # Prevent overlapping copies of this runner owned by the same user.
    lock = open(f"/tmp/cesare-invert-paired-{os.getuid()}.lock", "a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("another benchmark.py run is active for this user")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S-%fZ")
    out = (args.output or REPO / "build" / f"paired-{stamp}").resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in ("sources", "objects", "validation", "runs", "logs"):
        (out / name).mkdir()
    commands = []
    results = {
        "schema_version": 1,
        "status": "running",
        "arguments": vars(args) | {"output": str(out)},
        "variants": list(VARIANTS),
        "method": {
            "counter": "PERF_COUNT_HW_CPU_CYCLES", "exclude_kernel": True,
            "exclude_hypervisor": True, "pinned_counter": True,
            "multiplexing": "rejected", "units": "user CPU cycles per inversion",
            "governor_or_frequency_changes": False, "paired_empty_subtraction": True,
            "rotation": "function (sample + offset) modulo 4",
            "warmup_batches_per_function": 20,
            "main_runs": args.rounds * 2, "link_orders": ["forward", "reverse"],
            "controls": ["one", "max255"], "control_link_order": "forward",
            "main_input_words_le": ["0x0123456789abcdef", "0xfedcba9876543210",
                                    "0x0f1e2d3c4b5a6978", "0x7766554433221100"],
        },
        "source_sha256": {}, "tests": [], "runs": [], "controls": [],
    }
    original_affinity = set(allowed)

    def save():
        write_json(out / "commands.json", commands)
        write_json(out / "results.json", results)

    def command(argv, label, *, required=True):
        argv = list(map(str, argv))
        started = time.time()
        prefix = out / "logs" / f"{len(commands):03d}-{label}"
        record = {"argv": argv, "cwd": str(out), "started_unix": started,
                  "stdout": str(prefix.relative_to(out)) + ".stdout.txt",
                  "stderr": str(prefix.relative_to(out)) + ".stderr.txt"}
        commands.append(record)
        write_json(out / "commands.json", commands)
        proc = None
        stdout, stderr = "", ""
        try:
            proc = subprocess.Popen(argv, cwd=out, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, start_new_session=True,
                                    env=os.environ | {"LC_ALL": "C"})
            stdout, stderr = proc.communicate(timeout=args.timeout)
            record["returncode"] = proc.returncode
        except BaseException as exc:
            record["error"] = repr(exc)
            if proc is not None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, stderr = proc.communicate()
                record["returncode"] = proc.returncode
            raise
        finally:
            record["elapsed_seconds"] = time.time() - started
            (out / record["stdout"]).write_text(stdout)
            (out / record["stderr"]).write_text(stderr)
            write_json(out / "commands.json", commands)
        if required and proc.returncode:
            raise RuntimeError(f"{label} failed ({proc.returncode}); see {prefix}.stderr.txt\n"
                               + stdout[-2000:] + stderr[-2000:])
        return stdout, stderr, proc.returncode

    def environment(label):
        policy = Path(f"/sys/devices/system/cpu/cpu{args.cpu}/cpufreq")
        data = {
            "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "uname": platform.uname()._asdict(),
            "model": read_optional("/proc/device-tree/model"),
            "cpuinfo": read_optional("/proc/cpuinfo"),
            "perf_event_paranoid": read_optional("/proc/sys/kernel/perf_event_paranoid"),
            "cpu": args.cpu, "control_cpu": args.control_cpu,
            "available_affinity": sorted(original_affinity),
            "frequency": {field: read_optional(policy / field) for field in
                          ("scaling_governor", "scaling_cur_freq", "scaling_min_freq",
                           "scaling_max_freq", "cpuinfo_max_freq")},
            "temperature_millidegrees": read_optional("/sys/class/thermal/thermal_zone0/temp"),
            "loadavg": read_optional("/proc/loadavg"),
        }
        for key, argument in (("throttled", "get_throttled"), ("clock", "measure_clock")):
            if shutil.which("vcgencmd"):
                argv = ["vcgencmd", argument] + (["arm"] if key == "clock" else [])
                stdout, stderr, code = command(argv, f"{label}-{key}", required=False)
                data[key] = stdout.strip() if code == 0 else {"returncode": code, "stderr": stderr}
            else:
                data[key] = {"unavailable": "vcgencmd is not installed"}
        return data

    def interrupt(signum, _frame):
        raise RuntimeError(f"interrupted by signal {signum}")

    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupt)
    try:
        os.sched_setaffinity(0, {args.control_cpu})
        results["before"] = environment("before")
        results["compiler"] = command(["cc", "--version"], "compiler-version")[0]
        results["objcopy"] = command(["objcopy", "--version"], "objcopy-version")[0]
        # Honor an unpacked GMP sysroot without changing system packages.
        # Popen preserves PKG_CONFIG_PATH and PKG_CONFIG_SYSROOT_DIR from the caller.
        if shutil.which("pkg-config"):
            gmp_cflags = shlex.split(command(["pkg-config", "--cflags", "gmp"], "gmp-cflags")[0])
            gmp_libs = shlex.split(command(["pkg-config", "--libs", "gmp"], "gmp-libs")[0])
        else:
            if os.environ.get("PKG_CONFIG_SYSROOT_DIR") or os.environ.get("PKG_CONFIG_PATH"):
                raise RuntimeError("pkg-config is required to use the configured GMP sysroot")
            gmp_cflags, gmp_libs = [], ["-lgmp"]
        results["gmp"] = {"cflags": gmp_cflags, "libs": gmp_libs,
                          "pkg_config_path": os.environ.get("PKG_CONFIG_PATH"),
                          "pkg_config_sysroot_dir": os.environ.get("PKG_CONFIG_SYSROOT_DIR")}
        for relative in relative_sources:
            target = out / "sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, target)
            results["source_sha256"][str(relative)] = sha256(target)
        save()
        print(f"Native build and GMP validation on CPU {args.cpu}: {out}", flush=True)
        common = ["-O3", "-g", "-fno-pie", "-Wall", "-Wextra"]
        objects = out / "objects"
        source = out / "sources"
        # Test and benchmark the exact same assembly object before symbol renaming.
        command(["cc", *common, "-std=c11", *gmp_cflags, "-c", source / "test.c", "-o", objects / "test.o"],
                "compile-test")
        benchmark_objects = []
        for variant in VARIANTS:
            original = objects / f"{variant}.o"
            renamed = objects / f"{variant}-bench.o"
            command(["cc", *common, "-c", source / f"invert25519_{variant}.s", "-o", original],
                    f"compile-{variant}")
            binary = out / "validation" / f"test-{variant}"
            command(["cc", "-no-pie", objects / "test.o", original, *gmp_libs, "-o", binary],
                    f"link-test-{variant}")
            stdout, stderr, code = command(["taskset", "-c", args.cpu, binary, args.tests, hex(args.seed)],
                                           f"test-{variant}")
            (out / "validation" / f"{variant}.txt").write_text(stdout + stderr)
            match = re.search(r"PASS: (\d+) inputs, (\d+) assembly calls, including guard-page checks", stdout)
            if match is None:
                raise RuntimeError(f"test {variant} did not report a complete PASS")
            entry = {"variant": variant, "returncode": code, "random_cases": args.tests,
                     "inputs": int(match[1]), "assembly_calls": int(match[2]),
                     "binary_sha256": sha256(binary), "seed": hex(args.seed)}
            results["tests"].append(entry)
            write_json(out / "validation" / "validation.json", results["tests"])
            save()
            print(f"PASS {variant}: {entry['inputs']} inputs, {entry['assembly_calls']} calls", flush=True)
            command(["objcopy", "--redefine-sym", f"invert25519=bench_{variant}",
                     "--redefine-sym", f"_invert25519=_bench_{variant}", original, renamed],
                    f"rename-{variant}")
            # Symbol renaming must not change executable .text bytes.
            text_before, text_after = objects / f"{variant}.text", objects / f"{variant}-bench.text"
            command(["objcopy", "-O", "binary", "--only-section=.text", original, text_before],
                    f"text-original-{variant}")
            command(["objcopy", "-O", "binary", "--only-section=.text", renamed, text_after],
                    f"text-renamed-{variant}")
            if text_before.read_bytes() != text_after.read_bytes() or text_before.stat().st_size == 0:
                raise RuntimeError(f"symbol renaming changed .text for {variant}")
            entry["text_sha256"] = sha256(text_before)
            benchmark_objects.append(renamed)
        write_json(out / "validation" / "validation.json", results["tests"])
        command(["cc", *common, "-std=c11", f"-DBENCH_SAMPLES={args.samples}",
                 f"-DBENCH_BATCH={args.batch}", "-c", source / "scripts/bench_paired.c",
                 "-o", objects / "bench.o"], "compile-benchmark")
        command(["cc", *common, "-c", source / "scripts/bench_empty.s", "-o", objects / "empty.o"],
                "compile-empty")
        for order, ordering in (("forward", benchmark_objects), ("reverse", benchmark_objects[::-1])):
            command(["cc", "-no-pie", objects / "bench.o", objects / "empty.o", *ordering,
                     "-o", out / f"compare-{order}"], f"link-{order}")
        results["benchmark_before"] = environment("benchmark-before")
        save()

        def run_one(round_number, order, input_index):
            label = f"round-{round_number}-{order}-input-{input_index}"
            entry = {"round": round_number, "link_order": order,
                     "input_index": input_index, "before": environment(label + "-before")}
            stdout, _, _ = command(["taskset", "-c", args.cpu, out / f"compare-{order}", input_index], label)
            measured = json.loads(stdout)
            expected_names = set(VARIANTS) | {"empty"}
            if (len(measured["measurements"]) != 4 or
                    {row["name"] for row in measured["measurements"]} != expected_names or
                    measured["samples"] != args.samples or measured["batch"] != args.batch):
                raise RuntimeError(f"unexpected benchmark output in {label}")
            for row in measured["measurements"]:
                if len(row["raw_batch_cycles"]) != args.samples:
                    raise RuntimeError(f"incomplete raw cycles in {label}")
            entry["after"] = environment(label + "-after")
            entry["measurement_file"] = f"runs/{label}.json"
            write_json(out / entry["measurement_file"], measured)
            entry["measurements"] = [
                {key: value for key, value in row.items() if key != "raw_batch_cycles"}
                for row in measured["measurements"]]
            results["controls" if input_index else "runs"].append(entry)
            save()
            print(label + ": " + ", ".join(
                f"{row['name']}={row['net_p50']:.3f}" for row in measured["measurements"]
                if row["name"] != "empty"), flush=True)

        for round_number in range(1, args.rounds + 1):
            for order in ("forward", "reverse"):
                run_one(round_number, order, 0)
        for input_index in (1, 2):
            run_one(0, "forward", input_index)
        grouped = defaultdict(list)
        for run in results["runs"]:
            for row in run["measurements"]:
                grouped[row["name"]].append(row)
        summary = {"units": "user CPU cycles per inversion", "runs_per_variant": args.rounds * 2,
                   "aggregation": "median of per-run paired net medians", "results": {}}
        for name, rows in grouped.items():
            net = [row["net_p50"] for row in rows]
            summary["results"][name] = {
                "net_median": median(net), "net_range": [min(net), max(net)],
                "raw_median": median(row["raw_p50"] for row in rows),
                "delta_baseline_median": median(row["delta_baseline_p50"] for row in rows),
                "per_run_net_medians": net,
            }
        summary["ranking"] = sorted(VARIANTS, key=lambda name: summary["results"][name]["net_median"])
        results["summary"] = summary
        results["status"] = "complete"
        write_json(out / "summary.json", summary)
        print("Ranking: " + ", ".join(summary["ranking"]), flush=True)
    except BaseException as exc:
        results["status"] = "failed"
        results["error"] = repr(exc)
        raise
    finally:
        try:
            results["after"] = environment("after")
        except BaseException as exc:
            results["after"] = {"error": repr(exc)}
        os.sched_setaffinity(0, original_affinity)
        save()
        hashes = {str(path.relative_to(out)): sha256(path) for path in sorted(out.rglob("*"))
                  if path.is_file() and path.name not in ("SHA256SUMS", "SHA256SUMS.json")}
        write_json(out / "SHA256SUMS.json", hashes)
        (out / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in hashes.items()))
        lock.close()
        print(f"Saved {results['status']} run: {out}", flush=True)


if __name__ == "__main__":
    main()
