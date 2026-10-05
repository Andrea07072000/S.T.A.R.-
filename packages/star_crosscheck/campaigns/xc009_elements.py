# -*- coding: utf-8 -*-
"""XC-009: Cartesian state -> classical orbital elements (S.T.A.R., 2026-10-03).

Engines (different lineages):
1. star_elements — S.T.A.R. implementation of Curtis Algorithm 4.2 (standard library only)
2. hapsira — poliastro lineage rv2coe, run in its own venv
Value compared: [e, i, RAAN, argp, nu] with angles in degrees wrapped to [0, 360).
Reference (case 1): Curtis, Orbital Mechanics for Engineering Students, Example 4.3, printed to 4 significant figures.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
PY = lambda n: str(ROOT / ".venvs" / n / "Scripts" / "python.exe")
sys.path.insert(0, str(ROOT / "08_PROTOTYPES" / "star_elements"))
from star_elements import rv_to_coe  # noqa: E402

HAPSIRA_CODE = """
import math, hapsira
from astropy import units as u
from hapsira.bodies import Earth
from hapsira.twobody import Orbit
VERSION = hapsira.__version__
def compute(i):
    o = Orbit.from_vectors(Earth, i["r"] * u.km, i["v"] * u.km / u.s)
    a, e, inc, raan, argp, nu = o.classical()
    w = lambda x: float(x.to_value(u.deg)) % 360.0
    return [round(float(e.value), 9), round(w(inc), 7), round(w(raan), 7), round(w(argp), 7), round(w(nu), 7)]
"""


def star_compute(i):
    h, e, inc, raan, argp, nu = rv_to_coe(i["r"], i["v"])
    w = lambda x: math.degrees(x) % 360.0
    return [round(e, 9), round(w(inc), 7), round(w(raan), 7), round(w(argp), 7), round(w(nu), 7)]


ENGINES = [
    Engine(name="star_elements", lineage="S.T.A.R. Curtis Algorithm 4.2", func=star_compute, version="0.1.0"),
    Engine(name="hapsira", lineage="poliastro/hapsira rv2coe", python=PY("hapsira"), code=HAPSIRA_CODE),
]

CASES = [
    ({"r": [-6045.0, -3490.0, 2500.0], "v": [-3.457, 6.618, 2.533]},
     {"value": [0.1712, 153.2, 255.3, 20.07, 28.45], "tolerance": 0.05,
      "source": "Curtis, Orbital Mechanics for Engineering Students, Example 4.3"}),
    ({"r": [7000.0, 0.0, 0.0], "v": [0.0, 6.5, 3.8]}, None),
    ({"r": [-2000.0, 6800.0, 1200.0], "v": [-7.1, -1.9, 2.2]}, None),
    ({"r": [12000.0, -3000.0, -5000.0], "v": [1.5, 5.2, -1.1]}, None),
    ({"r": [6578.0, 100.0, -50.0], "v": [-0.2, 10.4, 1.9]}, None),
]


def run():
    out, verdicts = [], {}
    for inp, ref in CASES:
        bnd = crosscheck(quantity="Classical elements [e, i, RAAN, argp, nu]", inputs=inp, engines=ENGINES,
                         tolerance=1e-6, unit="deg (e dimensionless)", diff_mode="max_abs", reference=ref)
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1
    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-009 verdicts: {verdicts} | max diff: {max(diffs) if diffs else None}")
    path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-009_elements_evidence.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {path}")
    return out


if __name__ == "__main__":
    run()
