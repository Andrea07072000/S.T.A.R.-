# -*- coding: utf-8 -*-
"""star-xc — command line of star_crosscheck.

  star-xc run <campaign.py>            run a campaign script (it writes its evidence bundles)
  star-xc verify-bundle <evidence.json> recompute the sha256 of every bundle and report altered ones
  star-xc summary <evidence.json>      verdicts, lineages and max pairwise difference per bundle
"""
from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

from .core import bundle_sha256


def _bundles(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in ("run", "verify-bundle", "summary"):
        print(__doc__)
        return 2
    cmd, path = argv
    if cmd == "run":
        sys.argv = [path]
        runpy.run_path(path, run_name="__main__")
        return 0
    bad = 0
    for i, b in enumerate(_bundles(path)):
        if cmd == "verify-bundle":
            ok = bundle_sha256(b) == b.get("sha256")
            bad += not ok
            print(f"[{i}] {'OK     ' if ok else 'ALTERED'} {b.get('quantity')} {b.get('verdict')} {b.get('sha256', '')[:16]}")
        else:
            mx = max((p["diff"] for p in b.get("pairs", [])), default=None)
            print(f"[{i}] {b.get('verdict'):26} {b.get('quantity')} | lineages {len(b.get('independent_lineages', []))}"
                  f" | max pair diff {mx} {b.get('unit')} | failed {b.get('n_failed')}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
