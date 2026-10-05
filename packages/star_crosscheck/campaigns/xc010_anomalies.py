# -*- coding: utf-8 -*-
"""XC-010: Kepler's equation and anomaly conversions (S.T.A.R., 2026-10-03).
Engines: star_elements (S.T.A.R., Newton with Vallado starting guess) vs hapsira (poliastro lineage M_to_E / E_to_nu).
Value: [E, nu] in degrees for (M, e). Reference (case 1): Vallado Example 2-1, E = 220.512074767522 deg."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
PY = lambda n: str(ROOT / ".venvs" / n / "Scripts" / "python.exe")
sys.path.insert(0, str(ROOT / "08_PROTOTYPES" / "star_elements"))
from star_elements import eccentric_to_true, mean_to_eccentric  # noqa: E402

HAPSIRA_CODE = """
import math, hapsira
from hapsira.core.angles import M_to_E, E_to_nu
VERSION = hapsira.__version__
def compute(i):
    E = float(M_to_E(math.radians(i["M_deg"]), i["e"])) % (2 * math.pi)
    nu = float(E_to_nu(E, i["e"])) % (2 * math.pi)
    return [round(math.degrees(E), 9), round(math.degrees(nu), 9)]
"""


def star_compute(i):
    E = mean_to_eccentric(math.radians(i["M_deg"]), i["e"])
    nu = eccentric_to_true(E, i["e"])
    return [round(math.degrees(E), 9), round(math.degrees(nu), 9)]


ENGINES = [Engine(name="star_elements", lineage="S.T.A.R. Newton (Vallado Alg. 2 start)", func=star_compute, version="0.2.0"),
           Engine(name="hapsira", lineage="poliastro/hapsira angles", python=PY("hapsira"), code=HAPSIRA_CODE)]
CASES = [({"M_deg": 235.4, "e": 0.4}, {"value": [220.512074767522], "source": "Vallado, Fundamentals of Astrodynamics, Example 2-1 (E only)", "tolerance": 1e-9})]
CASES += [({"M_deg": M, "e": e}, None) for e in (0.0, 0.1, 0.5, 0.9, 0.99) for M in (5.0, 90.0, 179.0, 300.0)]


def run():
    out, verdicts = [], {}
    for inp, ref in CASES:
        if ref is not None:
            # the reference gives E only: compare it on its own bundle quantity
            bnd = crosscheck(quantity="Eccentric anomaly E", inputs=inp, engines=[
                Engine(name="star_elements", lineage=ENGINES[0].lineage, func=lambda i: star_compute(i)[:1], version="0.2.0"),
                Engine(name="hapsira", lineage=ENGINES[1].lineage, python=PY("hapsira"),
                       code=HAPSIRA_CODE.replace("return [round(math.degrees(E), 9), round(math.degrees(nu), 9)]",
                                                 "return [round(math.degrees(E), 9)]"))],
                tolerance=1e-8, unit="deg", diff_mode="max_abs", reference=ref)
        else:
            bnd = crosscheck(quantity="[E, nu]", inputs=inp, engines=ENGINES, tolerance=1e-8, unit="deg", diff_mode="max_abs")
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1
    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-010 verdicts: {verdicts} | max diff deg: {max(diffs) if diffs else None}")
    path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-010_anomalies_evidence.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {path}")
    return out


if __name__ == "__main__":
    run()
