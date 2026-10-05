# -*- coding: utf-8 -*-
"""XC-012: TDB - TT (S.T.A.R., 2026-10-04).
Engines (different METHODS): star_tdb = 7-term USNO Circular 179 series; pyerfa = ERFA dtdb, full Fairhead &
Bretagnon (1990) series (~800 terms), geocentre. Tolerance 10 us = the stated accuracy of the short series.
astropy and skyfield are NOT added: astropy calls the same erfa.dtdb, skyfield implements the same 7-term series
as star_tdb, so either would be the same witness twice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
PY = lambda n: str(ROOT / ".venvs" / n / "Scripts" / "python.exe")
sys.path.insert(0, str(ROOT / "08_PROTOTYPES" / "star_tdb"))
from star_tdb import tdb_minus_tt  # noqa: E402

ERFA_CODE = """
import erfa
VERSION = erfa.__version__
def compute(i):
    return [round(float(erfa.dtdb(i["jd_tt"], 0.0, 0.0, 0.0, 0.0, 0.0)), 12)]
"""
ENGINES = [Engine(name="star_tdb", lineage="USNO Circular 179 eq. 2.6 (7-term series)", func=lambda i: [round(tdb_minus_tt(i["jd_tt"]), 12)], version="0.1.0"),
           Engine(name="pyerfa", lineage="ERFA dtdb (Fairhead & Bretagnon 1990 full series)", python=PY("pyerfa"), code=ERFA_CODE)]
CASES = [{"jd_tt": jd} for jd in (2305447.5, 2342000.5, 2378496.5, 2415020.5, 2433282.5, 2444239.5, 2451545.0,
                                  2455197.5, 2459959.5, 2460586.5, 2469807.5, 2488070.5, 2524593.5)]


def run():
    out, verdicts = [], {}
    for inp in CASES:
        b = crosscheck(quantity="TDB - TT", inputs=inp, engines=ENGINES, tolerance=1e-5, unit="s", diff_mode="max_abs")
        out.append(b)
        verdicts[b["verdict"]] = verdicts.get(b["verdict"], 0) + 1
    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-012 verdicts: {verdicts} | max diff s: {max(diffs) if diffs else None}")
    path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-012_tdb_evidence.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {path}")
    return out


if __name__ == "__main__":
    run()
