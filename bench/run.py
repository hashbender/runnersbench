#!/usr/bin/env python3
"""Collect system information and run benchmarks on a CI runner.

Writes one JSON document to --output. Each benchmark runs independently, so a
failure is recorded as {"error": ...} instead of aborting the whole run.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone

SCHEMA_VERSION = 1
# Bump bench/VERSION when a change makes new results incomparable with stored ones;
# the workflow re-runs every runner whose stored result has an older version.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")) as f:
    BENCHMARK_VERSION = int(f.read())
DURATION = 15  # seconds per sysbench/fio test
WARMUP = 5  # seconds of all-thread CPU load before the CPU tests, so clocks and caches settle
REDIS_VERSION = "8.10.3"
# 1 GB of random data on this repo's download-test release, fetched in byte ranges. Cloudflare's speed
# test can't be used for downloads: it answers 429 for an hour after roughly 1.5 GB from one address.
DOWNLOAD_URL = "https://github.com/lockyer-labs/runnersbench/releases/download/download-test/1g.bin"
DOWNLOAD_CHUNK = 50_000_000
# A single 50 MB request finishes in a fraction of a second on a fast link, which measures burst speed;
# back-to-back requests over several connections reach sustained limits. Each test stops after
# NET_SECONDS or NET_BYTES.
NET_SECONDS = 10
NET_BYTES = 1_000_000_000
NET_STREAMS = 4
FSYNC_SECONDS = 10
REDIS_URL = f"https://github.com/redis/redis/archive/refs/tags/{REDIS_VERSION}.tar.gz"
APT_PACKAGES = ["sysbench", "fio", "build-essential"]
# macOS runners already have the Xcode command line tools, so only the benchmarks come from Homebrew.
BREW_PACKAGES = ["sysbench", "fio"]
MACOS = sys.platform == "darwin"
CPU_FLAGS = ["avx2", "avx512f", "sha_ni", "aes", "vaes", "asimd", "sve", "sve2", "sha2"]
# Buildkite hosted agents run jobs as root without sudo installed.
SUDO = [] if os.geteuid() == 0 else ["sudo"]
DMI_FIELDS = ["sys_vendor", "product_name", "product_version", "board_vendor", "bios_vendor", "chassis_vendor"]


class CommandError(Exception):
    pass


def sh(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str))
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-20:])
        raise CommandError(f"{cmd!r} exited {proc.returncode}: {tail}")
    return proc.stdout


def try_sh(cmd):
    try:
        return sh(cmd).strip() or None
    except (CommandError, OSError):
        return None


def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def cpu_count():
    return len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count()


def sysctl(name):
    return try_sh(["sysctl", "-n", name])


def cpu_counters():
    """Clock, hypervisor steal and cgroup CPU counters, to diff around a workload.

    Adapted from Buildkite's CPU steal probe. Steal is only reported by some hypervisors (KVM, Firecracker;
    not Hyper-V), and macOS has none of these files, so missing counters are left out.
    """
    counters = {"wall": time.monotonic()}
    stat = re.search(r"^cpu\s+(.+)$", read("/proc/stat") or "", re.M)
    fields = [int(x) for x in stat.group(1).split()] if stat else []
    if len(fields) >= 8:
        counters["steal"], counters["total"] = fields[7], sum(fields)
    cgroup = read("/sys/fs/cgroup/cpu.stat") or read("/sys/fs/cgroup/cpu/cpu.stat") or ""
    for key, pattern, scale in [("usage_usec", r"usage_usec", 1), ("nr_throttled", r"nr_throttled", 1),
                                ("throttled_usec", r"throttled_usec", 1), ("throttled_usec", r"throttled_time", 1 / 1000)]:
        m = re.search(rf"^{pattern}\s+(\d+)", cgroup, re.M)
        if m and key not in counters:
            counters[key] = int(m.group(1)) * scale
    return counters


def cpu_accounting(start, end):
    wall = end["wall"] - start["wall"]
    out = {"wall_seconds": wall}
    if "total" in start and end["total"] > start["total"]:
        out["steal_pct"] = (end["steal"] - start["steal"]) / (end["total"] - start["total"]) * 100
    if "usage_usec" in start:
        out["cpu_per_wall"] = (end["usage_usec"] - start["usage_usec"]) / 1e6 / wall
    if "nr_throttled" in start:
        out["nr_throttled"] = end["nr_throttled"] - start["nr_throttled"]
    if "throttled_usec" in start:
        out["throttled_ms"] = (end["throttled_usec"] - start["throttled_usec"]) / 1000
    return out


def flatten_lscpu(entries, out):
    for entry in entries:
        out[entry["field"].rstrip(":")] = entry.get("data")
        flatten_lscpu(entry.get("children", []), out)
    return out


def ip_info():
    try:
        with urllib.request.urlopen("https://ipinfo.io/json", timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        return {"error": str(e)}
    return {k: data.get(k) for k in ("ip", "city", "region", "country", "loc", "org")}


def system_info(workdir):
    cpuinfo = read("/proc/cpuinfo") or ""

    def cpuinfo_field(name):
        m = re.search(rf"^{name}\s*:\s*(.+)$", cpuinfo, re.M)
        return m.group(1).strip() if m else None

    flags = set((cpuinfo_field("flags") or cpuinfo_field("Features") or "").split())
    lscpu_json = try_sh("lscpu -J")
    lscpu = flatten_lscpu(json.loads(lscpu_json)["lscpu"], {}) if lscpu_json else {}
    meminfo = read("/proc/meminfo") or ""
    mem_kb = re.search(r"^MemTotal:\s*(\d+)", meminfo, re.M)
    disk = shutil.disk_usage(workdir)
    os_release = read("/etc/os-release") or ""
    pretty_name = re.search(r'^PRETTY_NAME="?([^"\n]*)', os_release, re.M)
    lsblk = try_sh("lsblk -J -d -o NAME,SIZE,TYPE,ROTA,MODEL")
    if MACOS:
        model, vendor = sysctl("machdep.cpu.brand_string"), "Apple"
        mem_bytes = int(sysctl("hw.memsize") or 0) or None
        os_name = f"macOS {try_sh(['sw_vers', '-productVersion'])}"
        # kern.hv_vmm_present is 1 inside a Virtualization.framework VM.
        virtualization = "apple" if sysctl("kern.hv_vmm_present") == "1" else "none"
        layers = {"vm": virtualization, "container": None}
        dmi = {"product_name": sysctl("hw.model")}
    else:
        model, vendor = lscpu.get("Model name") or cpuinfo_field("model name"), lscpu.get("Vendor ID")
        mem_bytes = int(mem_kb.group(1)) * 1024 if mem_kb else None
        os_name = pretty_name.group(1) if pretty_name else None
        virtualization = try_sh("systemd-detect-virt")
        # Plain systemd-detect-virt reports only the innermost layer, and calls unknown containers "docker".
        layers = {"vm": try_sh(["systemd-detect-virt", "--vm"]), "container": try_sh(["systemd-detect-virt", "--container"])}
        dmi = {f: read(f"/sys/class/dmi/id/{f}") or try_sh(f"sudo -n cat /sys/class/dmi/id/{f}") for f in DMI_FIELDS}

    return {
        "cpu": {
            "model": model,
            "vendor": vendor,
            "arch": platform.machine(),
            "logical_cpus": os.cpu_count(),
            "available_cpus": cpu_count(),
            "threads_per_core": lscpu.get("Thread(s) per core"),
            "sockets": lscpu.get("Socket(s)"),
            "max_mhz": lscpu.get("CPU max MHz"),
            "l3_cache": lscpu.get("L3") or lscpu.get("L3 cache"),
            "hypervisor": lscpu.get("Hypervisor vendor"),
            "flags": None if MACOS else {f: f in flags for f in CPU_FLAGS},
            "cgroup_cpu_max": read("/sys/fs/cgroup/cpu.max"),
            "lscpu": lscpu,
        },
        "memory": {
            "total_bytes": mem_bytes,
            "cgroup_max": read("/sys/fs/cgroup/memory.max"),
        },
        "disk": {
            "workdir": workdir,
            "total_bytes": disk.total,
            "free_bytes": disk.free,
            "mount": try_sh(["findmnt", "-n", "-o", "SOURCE,FSTYPE,OPTIONS", "-T", workdir]),
            "devices": json.loads(lsblk)["blockdevices"] if lsblk else None,
        },
        "os": {
            "pretty_name": os_name,
            "kernel": platform.release(),
            "image_os": os.environ.get("ImageOS"),
            "image_version": os.environ.get("ImageVersion"),
        },
        "virtualization": virtualization,
        "virtualization_layers": layers,
        "dmi": dmi,
        "network": ip_info(),
        "runner": {
            "name": os.environ.get("RUNNER_NAME") or os.environ.get("BUILDKITE_AGENT_NAME"),
            "environment": os.environ.get("RUNNER_ENVIRONMENT") or ("buildkite" if os.environ.get("BUILDKITE") else None),
        },
        "tools": {
            "docker": try_sh("docker --version"),
            "gcc": (try_sh("gcc --version") or "").split("\n")[0] or None,
            "python": platform.python_version(),
        },
    }


def bench_package_install():
    if MACOS:
        start = time.monotonic()
        try:
            sh(["env", "HOMEBREW_NO_AUTO_UPDATE=1", "HOMEBREW_NO_INSTALL_CLEANUP=1", "HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1",
                "brew", "install", "--quiet", *BREW_PACKAGES])
        except CommandError:
            # brew exits 1 when a dependency's post-install step fails, even though the packages installed.
            if not all(shutil.which(p) for p in BREW_PACKAGES):
                raise
        return {"manager": "brew", "seconds": time.monotonic() - start}
    start = time.monotonic()
    sh([*SUDO, "apt-get", "update", "-qq"])
    update = time.monotonic() - start
    sh([*SUDO, "env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", "-qq", *APT_PACKAGES])
    return {"manager": "apt", "update_seconds": update, "seconds": time.monotonic() - start}


def bench_sysbench_cpu(threads, duration=DURATION):
    out = sh(["sysbench", "cpu", f"--threads={threads}", f"--time={duration}", "run"])
    eps = float(re.search(r"events per second:\s*([\d.]+)", out).group(1))
    return {"threads": threads, "events_per_second": eps}


def bench_sysbench_memory():
    out = sh(["sysbench", "memory", "--threads=1", "--memory-block-size=1M", "--memory-total-size=1T",
              f"--time={DURATION}", "run"])
    return {"mib_per_second": float(re.search(r"\(([\d.]+) MiB/sec\)", out).group(1))}


# seq_write goes first so the test file is laid out before the read tests.
FIO_TESTS = {
    "seq_write": ["--rw=write", "--bs=1M", "--iodepth=16"],
    "seq_read": ["--rw=read", "--bs=1M", "--iodepth=16"],
    "rand_read": ["--rw=randread", "--bs=4k", "--iodepth=32"],
    "rand_write": ["--rw=randwrite", "--bs=4k", "--iodepth=32"],
}


def bench_fio(workdir):
    path = os.path.join(workdir, "fio.dat")
    results = {}
    try:
        for name, args in FIO_TESTS.items():
            # Some filesystems (tmpfs, some overlays) reject O_DIRECT, so fall back to buffered IO.
            for direct in (1, 0):
                cmd = ["fio", f"--name={name}", f"--filename={path}", "--size=2G",
                       f"--ioengine={'posixaio' if MACOS else 'libaio'}",
                       f"--direct={direct}", "--time_based", f"--runtime={DURATION}", "--ramp_time=2",
                       "--group_reporting", "--output-format=json", *args]
                try:
                    out = sh(cmd)
                    break
                except CommandError:
                    if not direct:
                        raise
            job = json.loads(out[out.index("{"):])["jobs"][0]
            side = job["write" if "write" in name else "read"]
            p99 = side.get("clat_ns", {}).get("percentile", {}).get("99.000000")
            results[name] = {
                "mb_per_second": side["bw_bytes"] / 1e6,
                "iops": side["iops"],
                "p99_latency_us": p99 / 1000 if p99 else None,
                "direct": bool(direct),
            }
    finally:
        if os.path.exists(path):
            os.remove(path)
    return results


def curl(url, dest="/dev/null"):
    fmt = "%{speed_download} %{size_download} %{time_total} %{time_connect} %{time_starttransfer}"
    out = sh(["curl", "-sS", "-L", "--fail", "-o", dest, "-w", fmt, url])
    speed, size, total, connect, ttfb = (float(x) for x in out.split())
    return {"mb_per_second": speed / 1e6, "bytes": int(size), "seconds": total,
            "connect_seconds": connect, "ttfb_seconds": ttfb}


def bench_transfer(command, chunk):
    """Run command(i) for request i on NET_STREAMS connections until NET_SECONDS or NET_BYTES."""
    start = time.monotonic()
    deadline = start + NET_SECONDS
    streams, errors = [], []
    next_request = [0]
    lock = threading.Lock()

    def take():
        with lock:
            i = next_request[0]
            next_request[0] += 1
            return i if i < NET_BYTES // chunk and time.monotonic() < deadline else None

    def stream():
        moved, requests = 0, 0
        while (i := take()) is not None:
            # Stop at the deadline even mid-request; curl exits 28 but still reports the bytes it got.
            cmd = command(i)
            cmd[1:1] = ["--max-time", f"{max(deadline - time.monotonic(), 0.5):.2f}"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode not in (0, 28) or not proc.stdout.strip():
                errors.append(f"curl exited {proc.returncode}: {proc.stderr.strip()[:200]}")
                break
            moved += float(proc.stdout)
            requests += 1
            if proc.returncode == 28:
                break
        streams.append((moved, requests, time.monotonic()))

    threads = [threading.Thread(target=stream) for _ in range(NET_STREAMS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    moved = sum(s[0] for s in streams)
    if not moved:
        raise CommandError(errors[0] if errors else "nothing transferred")
    seconds = max(s[2] for s in streams) - start
    return {"mb_per_second": moved / seconds / 1e6, "bytes": int(moved), "seconds": seconds,
            "streams": NET_STREAMS, "requests": sum(s[1] for s in streams), "errors": errors}


TRANSFER = ["curl", "-sS", "--fail", "-L", "-o", "/dev/null", "-w", "%{size_download}"]


def bench_download():
    return bench_transfer(
        lambda i: [*TRANSFER, "-r", f"{i * DOWNLOAD_CHUNK}-{(i + 1) * DOWNLOAD_CHUNK - 1}", DOWNLOAD_URL], DOWNLOAD_CHUNK)


def bench_fsync(workdir):
    """4k writes, each followed by fsync, as databases and package managers do.

    Very high rates mean the host acknowledges flushes without reaching stable storage, which is fine for
    throwaway CI machines.
    """
    path = os.path.join(workdir, "fsync.dat")
    try:
        out = sh(["fio", "--name=fsync", f"--filename={path}", "--size=256M", "--rw=write", "--bs=4k",
                  "--ioengine=sync", "--fsync=1", "--time_based", f"--runtime={FSYNC_SECONDS}",
                  "--output-format=json"])
    finally:
        if os.path.exists(path):
            os.remove(path)
    job = json.loads(out[out.index("{"):])["jobs"][0]
    sync = job.get("sync", {}).get("lat_ns", {})
    p99 = sync.get("percentile", {}).get("99.000000")
    return {"writes_per_second": job["write"]["iops"], "sync_mean_us": sync.get("mean", 0) / 1000 or None,
            "sync_p99_us": p99 / 1000 if p99 else None}


def bench_compile_redis(workdir):
    tarball = os.path.join(workdir, "redis.tar.gz")
    download = curl(REDIS_URL, tarball)
    sh(["tar", "xzf", tarball, "-C", workdir])
    src = os.path.join(workdir, f"redis-{REDIS_VERSION}")
    jobs = cpu_count()
    start, counters = time.monotonic(), cpu_counters()
    # The top-level Makefile's module wrapper is broken in release tarballs; build the core directly.
    sh(["make", "-C", "src", f"-j{jobs}", "MALLOC=libc", "BUILD_TLS=no"], cwd=src)
    seconds = time.monotonic() - start
    accounting = cpu_accounting(counters, cpu_counters())
    shutil.rmtree(src, ignore_errors=True)
    return {"version": REDIS_VERSION, "jobs": jobs, "seconds": seconds, "github_download": download,
            "cpu_accounting": accounting}


def run(name, fn, *args):
    print(f"::group::{name}", flush=True)
    start = time.monotonic()
    try:
        result = fn(*args)
    except Exception as e:
        result = {"error": str(e)}
        print(f"::warning title={name} failed::{str(e).splitlines()[0]}", flush=True)
    result["wall_seconds"] = time.monotonic() - start
    print(json.dumps(result, indent=2), flush=True)
    print("::endgroup::", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workdir", default=os.environ.get("RUNNER_TEMP", "/tmp"))
    args = parser.parse_args()
    os.makedirs(args.workdir, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    run_counters = cpu_counters()

    system = run("system info", system_info, args.workdir)
    cpus = cpu_count()
    # Stored as apt_install so older Linux results stay comparable.
    benchmarks = {"apt_install": run("package install", bench_package_install)}
    if MACOS:
        # Homebrew's sysbench reports ~1,000x Linux's events/s on Apple Silicon, so its prime search isn't doing the work.
        skipped = {"skipped": "sysbench's CPU test doesn't do real work on macOS"}
        benchmarks["cpu_single"], benchmarks["cpu_multi"] = skipped, dict(skipped)
    else:
        run("sysbench cpu warm-up", bench_sysbench_cpu, cpus, WARMUP)
        benchmarks["cpu_single"] = run("sysbench cpu (1 thread)", bench_sysbench_cpu, 1)
        counters = cpu_counters()
        benchmarks["cpu_multi"] = run(f"sysbench cpu ({cpus} threads)", bench_sysbench_cpu, cpus)
        benchmarks["cpu_multi"]["cpu_accounting"] = cpu_accounting(counters, cpu_counters())
    benchmarks["memory"] = run("sysbench memory", bench_sysbench_memory)
    benchmarks["disk"] = run("fio", bench_fio, args.workdir)
    if MACOS:
        # A plain fsync on macOS doesn't reach the disk (that needs F_FULLFSYNC), so it isn't comparable.
        benchmarks["fsync"] = {"skipped": "fsync doesn't flush to disk on macOS"}
    else:
        benchmarks["fsync"] = run("fio fsync", bench_fsync, args.workdir)
    benchmarks["download"] = run("download from GitHub", bench_download)
    benchmarks["compile_redis"] = run("compile redis", bench_compile_redis, args.workdir)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # Timed by bench/cache.py around the workflow's actions/cache steps.
        cache = os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "cache.json")
        benchmarks["cache"] = json.load(open(cache)) if os.path.exists(cache) else {"error": "cache steps didn't finish"}

    result = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": BENCHMARK_VERSION,
        "spec": json.loads(os.environ.get("RUNNER_SPEC") or "{}"),
        "github": {
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "sha": os.environ.get("GITHUB_SHA"),
        },
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "system": system,
        "benchmarks": benchmarks,
        "cpu_accounting": cpu_accounting(run_counters, cpu_counters()),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    sys.exit(main())
