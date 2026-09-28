# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""Run the test suite and write a small, reproducible evidence record.

Usage (from the repository root):  python verification/run_verification.py

Writes verification/evidence/:
  junit.xml         pytest results (machine name and timestamps removed)
  environment.json  interpreter, platform, package versions, git commit
  SHA256SUMS        digests of the two files above

Anyone can re-run it and compare: the test outcomes must match; digests change only if the
environment, the code or the results change.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "verification" / "evidence"


def _version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except OSError:
        return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    junit = OUT / "junit.xml"
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider",
                             f"--junitxml={junit}"], cwd=ROOT)
    xml = junit.read_text(encoding="utf-8")
    # Remove what identifies the machine or the moment, keep what identifies the result.
    xml = re.sub(r'\s(hostname|timestamp)="[^"]*"', "", xml)
    xml = re.sub(r'\stime="[^"]*"', "", xml)
    junit.write_bytes(xml.encode("utf-8"))
    env = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "os": platform.system(),
        "pytest": _version("pytest"),
        "astropy": _version("astropy"),
        "pyerfa": _version("pyerfa"),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "src", "tests")),
        "pytest_exit_code": result.returncode,
    }
    (OUT / "environment.json").write_bytes((json.dumps(env, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    sums = "".join(f"{hashlib.sha256((OUT / n).read_bytes()).hexdigest()}  {n}\n"
                   for n in ("junit.xml", "environment.json"))
    (OUT / "SHA256SUMS").write_bytes(sums.encode("ascii"))
    print(f"evidence written to {OUT.relative_to(ROOT)} (pytest exit code {result.returncode})")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
