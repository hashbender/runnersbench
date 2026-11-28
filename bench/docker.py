#!/usr/bin/env python3
"""Time a cold and a cached Docker build of bench/docker with the GitHub Actions cache (type=gha).

The workflow runs this after docker/setup-buildx-action and crazy-max/ghaction-github-runtime, which
exposes the cache token to run steps. Providers that redirect the Actions cache serve type=gha too.

  docker.py <scope>   cold build that exports its layers to the cache under <scope>, then empty the
                      builder, edit one source file and rebuild from the cache; writes docker.json
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time

OUTPUT = os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "docker.json")
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docker")


def build(context, *args):
    start = time.monotonic()
    proc = subprocess.run(["docker", "buildx", "build", "--progress=plain", *args, context],
                          capture_output=True, text=True)
    seconds = time.monotonic() - start
    if proc.returncode:
        raise RuntimeError(f"docker buildx build exited {proc.returncode}: {proc.stderr[-600:]}")
    return seconds, proc.stderr


def main(scope):
    context = os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "docker-bench")
    shutil.rmtree(context, ignore_errors=True)
    shutil.copytree(SOURCE, context)
    cache = f"type=gha,scope={scope}"
    try:
        cold, _ = build(context, "--no-cache", "--cache-to", f"{cache},mode=max")
        subprocess.run(["docker", "buildx", "prune", "--all", "--force"], check=True, capture_output=True)
        with open(os.path.join(context, "src", "App.tsx"), "a") as f:
            f.write("// edited by bench/docker.py\n")
        cached, log = build(context, "--cache-from", cache)
        result = {"cold_seconds": cold, "cached_seconds": cached}
        step = re.search(r"^(#\d+) \[[^\]]*\] RUN npm ci", log, re.M)
        if not step or f"\n{step.group(1)} CACHED" not in log:
            result["error"] = "the cached build didn't reuse the npm ci layer"
            result["log_tail"] = log[-1500:]
    except Exception as e:
        result = {"error": str(e)}
    with open(OUTPUT, "w") as f:
        json.dump(result, f)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:])
