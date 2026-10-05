# -*- coding: utf-8 -*-
"""sgp4_audit — independent accuracy audit of SGP4 implementations against Vallado's official SGP4-VER verification
output (tcppver.out, AIAA 2006-6753 companion data), S.T.A.R., 2026-10-04.

Reference: the 33 SGP4-VER test satellites and Vallado's C++ reference positions (TEME, km) at the listed tsince
(minutes). Each implementation is driven in its own interpreter through a tiny driver defining
propagate(line1, line2, tsince_list) -> [[x, y, z] or None, ...]. Per implementation: max and median 3-D position error,
satellites where it refuses/errors, and the worst satellite. Implementations of the SAME code lineage as the reference
(e.g. python-sgp4, a port of Vallado's code) are expected to match to ~mm and VALIDATE the probe before others are read.
"""
from __future__ import annotations

import json
import math
import statistics
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


def load_reference(tle_path: Path, out_path: Path) -> List[Dict]:
    """[{satnum, line1, line2, epochs: [tsince...], ref: [[x,y,z]...]}] for the satellites present in both files."""
    # pair TLEs and reference blocks by ORDER, not by satellite number: SGP4-VER lists NORAD 20413 twice with two
    # different TLEs (found 2026-10-04: keying by number silently mixed them)
    lines = [l.rstrip() for l in tle_path.read_text(encoding="utf-8", errors="replace").splitlines()]
    tles = [(lines[i][:69], lines[i + 1][:69]) for i, l in enumerate(lines)
            if l.startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 ")]
    cases, cur = [], None
    for l in out_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = l.split()
        if len(parts) == 2 and parts[1] == "xx":
            k = len(cases)
            if k >= len(tles) or int(tles[k][0][2:7]) != int(parts[0]):
                raise ValueError(f"reference block {k} (sat {parts[0]}) does not match TLE order")
            cur = {"satnum": int(parts[0]), "case": k, "line1": tles[k][0], "line2": tles[k][1], "epochs": [], "ref": []}
            cases.append(cur)
            continue
        if cur is not None and len(parts) >= 4:
            try:
                cur["epochs"].append(float(parts[0]))
                cur["ref"].append([float(parts[1]), float(parts[2]), float(parts[3])])
            except ValueError:
                pass
    return cases


RUNNER = ("\nimport json, sys\ncases = json.loads(sys.stdin.read())\nout = []\nfor c in cases:\n"
          "    try:\n        out.append({'r': propagate(c['line1'], c['line2'], c['epochs'])})\n"
          "    except Exception as e:\n        out.append({'error': type(e).__name__ + ': ' + str(e)[:80]})\n"
          "print(json.dumps(out))\n")


def audit(command: List[str], driver: str, cases: List[Dict]) -> Dict:
    """command = interpreter argv prefix, e.g. [python.exe, '-c'] (driver + RUNNER appended)."""
    # driver code travels on stdin with the cases (a long driver on the command line breaks Windows' argv limit)
    boot = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
    r = subprocess.run(command + [boot], input=json.dumps({"code": driver + RUNNER.replace("json.loads(sys.stdin.read())", "payload['cases']"),
                                                           "cases": cases}),
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    res = json.loads(r.stdout.strip().splitlines()[-1])
    per_sat, all_err, refused = {}, [], []
    for c, x in zip(cases, res):
        if "error" in x:
            refused.append({"case": c["case"], "satnum": c["satnum"], "error": x["error"]})
            continue
        errs = [math.dist(a, b) for a, b in zip(x["r"], c["ref"]) if a is not None]
        missing = sum(1 for a in x["r"] if a is None)
        if errs:
            per_sat[f"{c['case']}:{c['satnum']}"] = {"max_km": max(errs), "n": len(errs), "missing": missing}
            all_err += errs
    worst = max(per_sat.items(), key=lambda kv: kv[1]["max_km"]) if per_sat else (None, {})
    return {"satellites": len(cases), "audited": len(per_sat), "refused": refused,
            "max_err_km": max(all_err) if all_err else None, "median_err_km": statistics.median(all_err) if all_err else None,
            "worst_sat": worst[0], "per_sat": per_sat}
