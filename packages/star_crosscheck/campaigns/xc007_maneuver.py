# -*- coding: utf-8 -*-
"""XC-007: Hohmann orbital transfer Delta-V crosscheck.

Engines:
1. star_maneuver (S.T.A.R. native closed-form vis-viva / Battin formulation)
2. hapsira (OpenAstronomy / Poliastro state-vector orbital maneuver core)
3. sympy (SymPy arbitrary-precision exact symbolic algebra)

Reference:
- Curtis, Howard D. (2014), "Orbital Mechanics for Engineering Students", 3rd ed., Section 6.3, Example 6.1.
- Battin, Richard H. (1999), "An Introduction to the Mathematics and Methods of Astrodynamics".
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
PY = lambda n: str(V / n / "Scripts" / "python.exe")

sys.path.insert(0, str(ROOT / "08_PROTOTYPES" / "star_maneuver"))
import star_maneuver

HAPSIRA_CODE = """
import numpy as np
import astropy.units as u
import hapsira
from hapsira.bodies import Earth
from hapsira.twobody import Orbit
from hapsira.maneuver import Maneuver

VERSION = hapsira.__version__

def compute(i):
    r1 = i["r1_km"] * u.km
    r2 = i["r2_km"] * u.km
    ss_i = Orbit.from_classical(Earth, r1, 0 * u.one, 0 * u.deg, 0 * u.deg, 0 * u.deg, 0 * u.deg)
    man = Maneuver.hohmann(ss_i, r2)
    return round(float(man.get_total_cost().to(u.km / u.s).value), 6)
"""

SYMPY_CODE = """
import sympy as sp

VERSION = sp.__version__

def compute(i):
    r1 = sp.Rational(str(i["r1_km"]))
    r2 = sp.Rational(str(i["r2_km"]))
    mu = sp.Rational(str(i.get("mu", 398600.4418)))
    a = (r1 + r2) / 2
    v1 = sp.sqrt(mu * (2 / r1 - 1 / a))
    vc1 = sp.sqrt(mu / r1)
    dv1 = sp.Abs(v1 - vc1)
    v2 = sp.sqrt(mu * (2 / r2 - 1 / a))
    vc2 = sp.sqrt(mu / r2)
    dv2 = sp.Abs(vc2 - v2)
    dv_tot = float((dv1 + dv2).evalf(30))
    return round(dv_tot, 6)
"""

def star_maneuver_compute(i):
    res = star_maneuver.hohmann(i["r1_km"], i["r2_km"], i.get("mu", 398600.4418))
    return round(float(res["dv_total"]), 6)


ENGINES = [
    Engine(
        name="star_maneuver",
        lineage="S.T.A.R. native vis-viva / Battin 1999",
        func=star_maneuver_compute,
        version="0.1.0",
    ),
    Engine(
        name="hapsira",
        lineage="Poliastro / OpenAstronomy state vectors",
        python=PY("hapsira"),
        code=HAPSIRA_CODE,
    ),
    Engine(
        name="sympy",
        lineage="SymPy exact symbolic CAS",
        python=PY("sympy"),
        code=SYMPY_CODE,
    ),
]

CASES = [
    # Case 1: LEO (6678 km) -> GEO (42164 km) [Curtis Ex. 6.1]
    (
        {"r1_km": 6678, "r2_km": 42164, "mu": 398600.4418},
        {
            "value": 3.8926,
            "source": "Curtis, Orbital Mechanics for Engineering Students (3rd ed. 2014), Ex 6.1",
            "tolerance": 5e-4,
        },
    ),
    # Case 2: LEO (6678 km) -> MEO GPS (26560 km)
    (
        {"r1_km": 6678, "r2_km": 26560, "mu": 398600.4418},
        None,
    ),
    # Case 3: Low LEO (6578 km) -> Higher LEO (7178 km)
    (
        {"r1_km": 6578, "r2_km": 7178, "mu": 398600.4418},
        None,
    ),
    # Case 4: LEO 300 km (6678 km) -> Lunar distance (384400 km)
    (
        {"r1_km": 6678, "r2_km": 384400, "mu": 398600.4418},
        None,
    ),
    # Case 5: Circular 7000 km -> Molniya apogee 40000 km
    (
        {"r1_km": 7000, "r2_km": 40000, "mu": 398600.4418},
        None,
    ),
]


def run():
    out, verdicts = [], {}
    for inp, ref in CASES:
        bnd = crosscheck(
            quantity="Hohmann Transfer Delta-V",
            inputs=inp,
            engines=ENGINES,
            tolerance=1e-5,
            unit="km/s",
            diff_mode="max_abs",
            reference=ref,
        )
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1

    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-007 verdicts: {verdicts} | max diff km/s: {max(diffs) if diffs else 0.0}")
    evidence_path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-007_maneuver_evidence.json"
    evidence_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {evidence_path}")
    return out


if __name__ == "__main__":
    run()
