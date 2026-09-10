#!/usr/bin/env python3
"""Build and cross-check both implementations on a frequency-locked Pi 5."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import threading
import time

VARIANTS = ("65a210bb6a4c", "043d7a693cb3")
REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--calls", type=int, default=2_000_000)
    parser.add_argument("--frequencies", type=int, nargs="+", default=[2400000, 1500000], help="kHz")
    parser.add_argument("--cpu", type=int, default=3)
    parser.add_argument("--control-cpu", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=120, help="seconds per subprocess")
    parser.add_argument("--output", type=Path, help="new output directory (must not exist)")
    args = parser.parse_args()
    if args.calls <= 0 or args.repeats <= 0 or args.timeout <= 0:
        parser.error("calls, repeats, and timeout must be positive")
    if platform.system() != "Linux" or platform.machine() != "aarch64":
        parser.error("run directly on an AArch64 Linux Raspberry Pi 5")
    if os.geteuid() != 0:
        parser.error("run with sudo: frequency locking and perf require root")
    allowed = os.sched_getaffinity(0)
    if args.cpu not in allowed or args.control_cpu not in allowed or args.cpu == args.control_cpu:
        parser.error("choose distinct available benchmark and control CPUs")
    for tool in ["cc", "perf", "taskset", "vcgencmd"]:
        if not shutil.which(tool):
            parser.error(f"missing prerequisite: {tool}")
    policy = (Path(f"/sys/devices/system/cpu/cpu{args.cpu}/cpufreq")).resolve()
    fields = ["scaling_governor", "scaling_min_freq", "scaling_max_freq"]
    available = [int(x) for x in (policy / "scaling_available_frequencies").read_text().split()]
    if any(f not in available for f in args.frequencies):
        parser.error(f"requested frequency unavailable; available kHz: {available}")
    # Avoid two copies of this runner changing the same policy at once.
    lock = open("/run/lock/cesare-invert-benchmark.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("another benchmark_pi5.py run holds the frequency lock")
    saved = {f: (policy / f).read_text().strip() for f in fields}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out = (args.output or REPO / "build" / f"benchmark-{stamp}").resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {args.control_cpu})
    data = {"arguments": vars(args) | {"output": str(out)}, "original_frequency": saved,
            "policy": str(policy), "runs": [], "monitor": [], "hashes": {}}
    stop = threading.Event()

    def command(argv):
        # Kill the whole subprocess group on timeout/interruption, including the
        # measured child of perf, before restoring machine-wide CPU settings.
        proc = subprocess.Popen([str(x) for x in argv], cwd=out, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True, env=os.environ | {"LC_ALL": "C"})
        try:
            stdout, stderr = proc.communicate(timeout=args.timeout)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate()
            raise
        if proc.returncode:
            raise RuntimeError(f"command failed ({proc.returncode}): {argv}\n{stdout}\n{stderr}")
        return stdout, stderr

    def telemetry():
        return {"time": time.time(), "freq_khz": (policy / "scaling_cur_freq").read_text().strip(),
                "temperature_mC": Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip(),
                "clock": command(["vcgencmd", "measure_clock", "arm"])[0].strip(),
                "throttled": command(["vcgencmd", "get_throttled"])[0].strip()}

    def monitor():
        while not stop.is_set():
            try:
                data["monitor"].append(telemetry())
            except Exception as exc:
                data["monitor"].append({"error": str(exc)})
            stop.wait(1)

    def write(field, value):
        (policy / field).write_text(str(value))

    def save():
        temporary = out / "results.json.tmp"
        temporary.write_text(json.dumps(data, indent=2))
        temporary.replace(out / "results.json")

    def interrupted(signum, _frame):
        raise RuntimeError(f"interrupted by signal {signum}")

    for signum in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
        signal.signal(signum, interrupted)
    data["environment"] = {"uname": command(["uname", "-a"])[0],
                           "compiler": command(["cc", "--version"])[0],
                           "perf": command(["perf", "--version"])[0]}
    sources = [REPO / f"invert25519_{v}.s" for v in VARIANTS]
    sources += [REPO / "bench.c", REPO / "scripts/bench_timed.c",
                REPO / "scripts/benchmark_pi5.py", REPO / "aarch64-bench/hal/hal.c",
                REPO / "aarch64-bench/hal/hal.h"]
    # Compile immutable snapshots and retain them with the results.
    snapshot = out / "sources"
    for source in sources:
        relative = source.relative_to(REPO)
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        data["hashes"][str(relative)] = hashlib.sha256(target.read_bytes()).hexdigest()
    for variant in VARIANTS:
        flags = ["-O3", "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-Werror"]
        asm = snapshot / f"invert25519_{variant}.s"
        hal = snapshot / "aarch64-bench/hal"
        for kind, inputs, extra in [
            ("repo", [snapshot / "bench.c", hal / "hal.c", asm], ["-DPERF_CYCLES", f"-I{hal}"]),
            ("timed", [snapshot / "scripts/bench_timed.c", asm], [])
        ]:
            argv = ["cc"] + flags + extra + inputs + ["-o", out / f"{kind}_{variant}"]
            stdout, stderr = command(argv)
            (out / f"compile_{kind}_{variant}.txt").write_text(" ".join(map(str, argv)) + "\n" + stdout + stderr)
    print(f"Compiled both implementations on Pi5. Results: {out}", flush=True)
    save()  # Preserve original settings before the first frequency write.
    thread = threading.Thread(target=monitor, daemon=True)
    try:
        write("scaling_governor", "performance")
        thread.start()
        for freq in args.frequencies:
            write("scaling_min_freq", min(available))
            write("scaling_max_freq", freq)
            write("scaling_min_freq", freq)
            time.sleep(1)
            assert int((policy / "scaling_min_freq").read_text()) == freq
            assert int((policy / "scaling_max_freq").read_text()) == freq
            for repeat in range(args.repeats):
                variants = list(VARIANTS)
                for variant in (variants if repeat % 2 == 0 else variants[::-1]):
                    prefix = f"{freq}_{repeat}_{variant}"
                    entry = {"freq_khz": freq, "repeat": repeat, "variant": variant,
                             "before": telemetry(), "measurements": {}}
                    stdout, stderr = command(["taskset", "-c", args.cpu, out / f"repo_{variant}"])
                    entry["repo"] = stdout
                    (out / f"{prefix}_repo.txt").write_text(stdout + stderr)
                    for mode in (["empty", "invert"] if repeat % 2 == 0 else ["invert", "empty"]):
                        ctl, ack = out / "ctl.fifo", out / "ack.fifo"
                        try:
                            for fifo in [ctl, ack]:
                                os.mkfifo(fifo)
                            perfout = out / f"{prefix}_{mode}_perf.csv"
                            argv = ["perf", "stat", "-x", ";", "--no-big-num", "-o", perfout,
                                    "-D", "-1", "--control", f"fifo:{ctl},{ack}", "-e",
                                    "cycles:u,instructions:u,task-clock,context-switches,cpu-migrations",
                                    "--", "taskset", "-c", args.cpu, out / f"timed_{variant}",
                                    mode, args.calls, ctl, ack]
                            stdout, stderr = command(argv)
                            entry["measurements"][mode] = {"timing": json.loads(stdout),
                                "perf": perfout.read_text(), "stderr": stderr, "command": list(map(str, argv))}
                        finally:
                            ctl.unlink(missing_ok=True)
                            ack.unlink(missing_ok=True)
                    entry["after"] = telemetry()
                    data["runs"].append(entry)
                    save()
                    print(f"Completed {prefix}", flush=True)
    except BaseException as exc:
        data["error"] = repr(exc)
        raise
    finally:
        # Ignore further termination requests only during the brief restoration.
        for signum in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
            signal.signal(signum, signal.SIG_IGN)
        stop.set()
        if thread.is_alive():
            thread.join(timeout=args.timeout + 1)
        errors = []
        for field, value in [("scaling_min_freq", min(available)),
                             ("scaling_max_freq", saved["scaling_max_freq"]),
                             ("scaling_min_freq", saved["scaling_min_freq"]),
                             ("scaling_governor", saved["scaling_governor"])]:
            try:
                write(field, value)
            except OSError as exc:
                errors.append(str(exc))
        data["restored_frequency"] = {f: (policy / f).read_text().strip() for f in fields}
        if errors or data["restored_frequency"] != saved:
            data["restoration_errors"] = errors or ["settings differ from original"]
        save()
        print("Final frequency settings: " + json.dumps(data["restored_frequency"]), flush=True)
        if "restoration_errors" in data:
            raise RuntimeError(f"frequency restoration failed: {data['restoration_errors']}")
    print(f"Raw measurements saved in {out}", flush=True)


if __name__ == "__main__":
    main()
