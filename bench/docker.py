#!/usr/bin/env python3
"""Time a cold and a cached Docker build of bench/docker, in two separate jobs on fresh runners.

With DOCKER_CACHE=gha the layers go through the GitHub Actions cache (type=gha), which needs
crazy-max/ghaction-github-runtime to expose the cache token. Otherwise the provider's own builder keeps
the layers between jobs (a persistent disk or a remote builder), so the builds pass no cache flags.

  docker.py cold <scope>                 build with nothing cached; writes docker-cold.json
  docker.py cached <scope> <cold.json>   edit one source file and rebuild; writes docker.json with both times
  docker.py merge <docker dir> <results dir>   attach each docker.json to its runner's result.json
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

TEMP = os.environ.get("RUNNER_TEMP", "/tmp")
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docker")
GHA = os.environ.get("DOCKER_CACHE", "gha") == "gha"
# Avrea serves type=gha from its own cache only when pointed at it.
GHA_URL = f",url_v2={os.environ['DOCKER_CACHE_URL']}" if os.environ.get("DOCKER_CACHE_URL") else ""


def context():
    path = os.path.join(TEMP, "docker-bench")
    shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(SOURCE, path)
    return path


def build(path, *args):
    start = time.monotonic()
    proc = subprocess.run(["docker", "buildx", "build", "--progress=plain", *args, path], capture_output=True, text=True)
    seconds = time.monotonic() - start
    if proc.returncode:
        raise RuntimeError(f"docker buildx build exited {proc.returncode}: {proc.stderr[-600:]}")
    return seconds, proc.stderr


def write(name, result):
    with open(os.path.join(TEMP, name), "w") as f:
        json.dump(result, f)
    print(json.dumps(result, indent=2))


def cold(scope):
    flags = ["--cache-to", f"type=gha,scope={scope},mode=max{GHA_URL}"] if GHA else []
    try:
        seconds, _ = build(context(), "--no-cache", *flags)
        result = {"cold_seconds": seconds}
    except Exception as e:
        result = {"error": str(e)}
    write("docker-cold.json", result)


def cached(scope, cold_path):
    try:
        with open(cold_path) as f:
            result = json.load(f)
    except (OSError, ValueError):
        result = {"error": "the cold build job didn't finish"}
    result["cache"] = os.environ.get("DOCKER_CACHE", "gha")
    path = context()
    with open(os.path.join(path, "src", "App.tsx"), "a") as f:
        f.write("// edited by bench/docker.py\n")
    try:
        seconds, log = build(path, *(["--cache-from", f"type=gha,scope={scope}{GHA_URL}"] if GHA else []))
        result["cached_seconds"] = seconds
        step = re.search(r"^(#\d+) \[[^\]]*\] RUN npm ci", log, re.M)
        if not step or f"\n{step.group(1)} CACHED" not in log:
            result.setdefault("error", "the cached build didn't reuse the npm ci layer")
            result.pop("cached_seconds")
    except Exception as e:
        result.setdefault("error", str(e))
    write("docker.json", result)


def merge(docker_dir, results_dir):
    found = {}
    for path in glob.glob(os.path.join(docker_dir, "*", "docker.json")):
        # Artifact directories are named docker-<label>-<rep>.
        found[os.path.basename(os.path.dirname(path))] = json.load(open(path))
    for path in glob.glob(os.path.join(results_dir, "*", "result.json")):
        with open(path) as f:
            result = json.load(f)
        spec = result.get("spec", {})
        if spec.get("os") == "macos" or "buildkite" in spec:
            continue
        docker = found.get(f"docker-{spec.get('label')}-{spec.get('rep')}", {"error": "docker jobs didn't finish"})
        result.setdefault("benchmarks", {})["docker"] = docker
        with open(path, "w") as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    command, *args = sys.argv[1:]
    {"cold": cold, "cached": cached, "merge": merge}[command](*args)
