# -*- coding: utf-8 -*-
"""XC-013: Greenwich Mean Sidereal Time, IAU 1982 (S.T.A.R., 2026-10-04).
Engines: star_sidereal (S.T.A.R., Vallado eq. 3-47) vs pyerfa gmst82 (ERFA/SOFA code, different authors, same IAU 1982
model). Reference (case 1): Vallado Example 3-5, 152.578787810 deg (printed to 1e-9 deg; tolerance 1e-7 deg)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
PY = lambda n: str(ROOT / ".venvs" / n / "Scripts" / "python.exe")
sys.path.insert(0, str(ROOT / "08_PROTOTYPES" / "star_sidereal"))
from star_sidereal import gmst82_deg  # noqa: E402

ERFA_CODE = """
import math, erfa
VERSION = erfa.__version__
def compute(i):
    return [round(math.degrees(float(erfa.gmst82(i["jd"], i["frac"]))) % 360.0, 9)]
"""
ENGINES = [Engine(name="star_sidereal", lineage="S.T.A.R. Vallado eq. 3-47", func=lambda i: [round(gmst82_deg(i["jd"], i["frac"]), 9)], version="0.1.0"),
           Engine(name="pyerfa", lineage="ERFA/SOFA gmst82", python=PY("pyerfa"), code=ERFA_CODE)]
CASES = [({"jd": 2448854.5, "frac": (12 + 14 / 60) / 24}, {"value": [152.578787810], "source": "Vallado, Fundamentals of Astrodynamics, Example 3-5", "tolerance": 1e-7})]
CASES += [({"jd": jd, "frac": fr}, None) for jd in (2415020.5, 2440587.5, 2451544.5, 2455197.5, 2460586.5, 2469807.5)
          for fr in (0.0, 0.3, 0.75)]


def run():
    out, verdicts = [], {}
    for inp, ref in CASES:
        b = crosscheck(quantity="GMST (IAU 1982)", inputs=inp, engines=ENGINES, tolerance=1e-7, unit="deg", diff_mode="max_abs", reference=ref)
        out.append(b)
        verdicts[b["verdict"]] = verdicts.get(b["verdict"], 0) + 1
    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-013 verdicts: {verdicts} | max diff deg: {max(diffs) if diffs else None}")
    path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-013_gmst_evidence.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {path}")
    return out


if __name__ == "__main__":
    run()
