# -*- coding: utf-8 -*-
"""XC-008: Cowell numerical orbit propagation with Earth J2 geopotential perturbation.

Engines:
1. star_orbit (S.T.A.R. native fixed-step 4th-order Runge-Kutta numerical integrator)
2. scipy_dop853 (SciPy Dormand-Prince 8th-order adaptive step ODE integrator; same J2 formula as star_orbit, written by the same agent)
3. hapsira_cowell_j2 (poliastro/hapsira J2_perturbation force model, independent code; added 2026-10-03)

References:
- Vallado, D. A. (2013), "Fundamentals of Astrodynamics and Applications", 4th ed., Section 8.6 & Eq. 9-37.
- Battin, R. H. (1999), "An Introduction to the Mathematics and Methods of Astrodynamics", AIAA.
- WGS-84 / EGM96 Earth gravitational parameters: mu = 3.986004418e14 m^3/s^2, Re = 6378137.0 m, J2 = 1.08262668e-3.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
import sys

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
PY = lambda n: str(V / n / "Scripts" / "python.exe")

sys.path.insert(0, str(ROOT / "08_PROTOTYPES"))
from star_orbit import OrbitState, propagate_orbit, MU_EARTH, R_EARTH, J2_EARTH

SCIPY_CODE = """
import json, math, scipy
from scipy.integrate import solve_ivp

VERSION = scipy.__version__
MU_EARTH = 3.986004418e14
R_EARTH = 6378137.0
J2_EARTH = 1.08262668e-3

def eom(t, y):
    r, v = y[:3], y[3:]
    rmag = math.sqrt(sum(x**2 for x in r))
    a_grav = [-MU_EARTH * x / (rmag**3) for x in r]
    fac = 1.5 * J2_EARTH * MU_EARTH * (R_EARTH**2) / (rmag**5)
    z2_r2 = 5.0 * (r[2]**2) / (rmag**2)
    a_j2 = [fac * r[0] * (z2_r2 - 1.0), fac * r[1] * (z2_r2 - 1.0), fac * r[2] * (z2_r2 - 3.0)]
    return list(v) + [ag + aj for ag, aj in zip(a_grav, a_j2)]

def compute(i):
    r_mag = float(i["r_mag_m"])
    inc = math.radians(float(i["inc_deg"]))
    duration = float(i["duration_s"])
    v_circ = math.sqrt(MU_EARTH / r_mag)
    y0 = [r_mag, 0.0, 0.0, 0.0, v_circ * math.cos(inc), v_circ * math.sin(inc)]
    sol = solve_ivp(eom, [0, duration], y0, method="DOP853", rtol=1e-11, atol=1e-11)
    rf = [float(x) for x in sol.y[:3, -1]]
    return [round(x, 4) for x in rf]
"""


HAPSIRA_CODE = """
import math, numpy as np, hapsira
from astropy import units as u
from hapsira.bodies import Earth
from hapsira.twobody import Orbit
from hapsira.twobody.propagation import CowellPropagator
from hapsira.core.perturbations import J2_perturbation
from hapsira.core.propagation import func_twobody
VERSION = hapsira.__version__
MU_EARTH = 3.986004418e14
R_EARTH = 6378137.0
J2_EARTH = 1.08262668e-3
def _f(t0, u_, k_):
    du = func_twobody(t0, u_, k_)
    ax, ay, az = J2_perturbation(t0, u_, k_, J2=J2_EARTH, R=R_EARTH / 1e3)
    return du + np.array([0, 0, 0, ax, ay, az])
def compute(i):
    r_mag = float(i["r_mag_m"]); inc = math.radians(float(i["inc_deg"])); duration = float(i["duration_s"])
    v_circ = math.sqrt(MU_EARTH / r_mag)
    assert abs(Earth.k.to_value(u.m**3 / u.s**2) - MU_EARTH) < 1.0
    o = Orbit.from_vectors(Earth, [r_mag / 1e3, 0, 0] * u.km,
                           [0, v_circ * math.cos(inc) / 1e3, v_circ * math.sin(inc) / 1e3] * u.km / u.s)
    o2 = o.propagate(duration * u.s, method=CowellPropagator(rtol=1e-12, f=_f))
    return [round(float(x) * 1e3, 4) for x in o2.r.to_value(u.km)]
"""


def star_orbit_compute(i):
    r_mag = float(i["r_mag_m"])
    inc = math.radians(float(i["inc_deg"]))
    duration = float(i["duration_s"])
    v_circ = math.sqrt(MU_EARTH / r_mag)
    epoch = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
    init = OrbitState(epoch=epoch, r=(r_mag, 0.0, 0.0), v=(0.0, v_circ * math.cos(inc), v_circ * math.sin(inc)))
    traj = propagate_orbit(init, duration_sec=duration, step_sec=10.0, include_j2=True)
    rf = traj[-1].r
    return [round(float(x), 4) for x in rf]


ENGINES = [
    Engine(
        name="star_orbit",
        lineage="S.T.A.R. Cowell fixed-step RK4 numerical integrator",
        func=star_orbit_compute,
        version="0.2.0",
    ),
    Engine(
        name="hapsira_cowell_j2",
        lineage="poliastro/hapsira force model (J2_perturbation) and Cowell propagator",
        python=PY("hapsira"),
        code=HAPSIRA_CODE,
    ),
    Engine(
        name="scipy_dop853",
        lineage="SciPy Dormand-Prince 8(5,3) adaptive numerical integrator",
        python=PY("scipy"),
        code=SCIPY_CODE,
    ),
]

CASES = [
    # Case 1: LEO 7000 km, inc=45 deg, 1 full orbit (5828.5 s)
    (
        {"r_mag_m": 7000000.0, "inc_deg": 45.0, "duration_s": 5828.5165},
        None,
    ),
    # Case 2: Polar LEO 7000 km, inc=90 deg, 1 full orbit (5828.5 s)
    (
        {"r_mag_m": 7000000.0, "inc_deg": 90.0, "duration_s": 5828.5165},
        None,
    ),
    # Case 3: Equatorial LEO 7000 km, inc=0 deg, 1 full orbit (5828.5 s)
    (
        {"r_mag_m": 7000000.0, "inc_deg": 0.0, "duration_s": 5828.5165},
        None,
    ),
    # Case 4: Cape Canaveral inclination 28.5 deg, r=10000 km, duration=10000 s
    (
        {"r_mag_m": 10000000.0, "inc_deg": 28.5, "duration_s": 10000.0},
        None,
    ),
]


def run():
    out, verdicts = [], {}
    for inp, ref in CASES:
        bnd = crosscheck(
            quantity="Cowell J2 Orbit Position Vector",
            inputs=inp,
            engines=ENGINES,
            tolerance=0.05,  # 5 cm tolerance
            unit="m",
            diff_mode="norm",
            reference=ref,
        )
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1

    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-008 verdicts: {verdicts} | max diff m: {max(diffs) if diffs else 0.0}")
    evidence_path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-008_orbit_propagation_evidence.json"
    evidence_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {evidence_path}")
    return out


if __name__ == "__main__":
    run()
