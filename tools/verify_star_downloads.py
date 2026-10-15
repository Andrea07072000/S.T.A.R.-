#!/usr/bin/env python3
"""Check S.T.A.R. files you downloaded against the published SHA-256 fingerprints. Standard library only, works offline.

Usage:
    python verify_star_downloads.py SHA256SUMS.txt FILE [FILE ...]
    python verify_star_downloads.py SHA256SUMS.txt --folder DOWNLOAD_FOLDER

Each file is matched by name to a line of SHA256SUMS.txt (downloaded from the same website, ideally on another day or
network). Exit code 0 only if every file is listed and matches; 1 otherwise. Licence: Apache-2.0.
"""
import hashlib
import sys
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    sums = {}
    for line in Path(argv[1]).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            sums[Path(parts[1]).name] = parts[0].lower()
    if argv[2] == "--folder":
        files = [p for p in Path(argv[3]).rglob("*") if p.is_file() and p.name != Path(argv[1]).name] if len(argv) > 3 else []
    else:
        files = [Path(a) for a in argv[2:]]
    if not files:
        print("No files to check.")
        return 2
    bad = 0
    for f in files:
        want = sums.get(f.name)
        if want is None:
            print(f"NOT LISTED  {f.name}")
            bad += 1
        elif sha256(f) != want:
            print(f"MISMATCH    {f.name}   (do not use this file)")
            bad += 1
        else:
            print(f"OK          {f.name}")
    print(f"{len(files) - bad} of {len(files)} files match the published fingerprints.")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
