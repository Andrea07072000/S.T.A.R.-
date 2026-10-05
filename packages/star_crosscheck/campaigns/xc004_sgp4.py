# -*- coding: utf-8 -*-
"""XC-004: SGP4 TEME Satellite State Vector Crosscheck.

Engines:
1. sgp4 (Vallado et al. 2006 official C++ reference port)
2. skyfield (TEME position vector from EarthSatellite)
3. pyorbital (PyTroll pure-Python SGDP4 propagator)

Lineages:
- "Vallado SGP4": sgp4, skyfield (both use Satrec)
- "PyTroll SGDP4": pyorbital (independent Python translation)

Reference:
- Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006),
  "Revisiting Spacetrack Report #3", AIAA-2006-6753, Table 4.
  Vanguard 1 (NORAD 00005) at epoch (2000-06-27T18:50:19.733568Z):
  r = [7022.4653, -1400.0830, 0.0400] km.
"""

import json
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
PY = lambda n: str(V / n / "Scripts" / "python.exe")

TLE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
TLE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"

SGP4_CODE = f"""
import sgp4; VERSION = sgp4.__version__
from sgp4.api import Satrec
s = Satrec.twoline2rv('{TLE1}', '{TLE2}')
def compute(i):
    delta_days = i['dt_minutes'] / 1440.0
    e, r, v = s.sgp4(2451723.0, 0.28495062 + delta_days)
    return [round(float(x), 4) for x in r]
"""

SKYFIELD_CODE = f"""
import skyfield; VERSION = skyfield.__version__
from skyfield.api import EarthSatellite, load
from datetime import datetime, timezone, timedelta
ts = load.timescale(builtin=True)
sat = EarthSatellite('{TLE1}', '{TLE2}', 'VANGUARD', ts)
def compute(i):
    dt = datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(days=178.78495062, minutes=i['dt_minutes'])
    t = ts.from_datetime(dt)
    r, v, err = sat._position_and_velocity_TEME_km(t)
    return [round(float(x), 4) for x in r]
"""

PYORBITAL_CODE = f"""
import pyorbital; VERSION = pyorbital.__version__
from pyorbital.orbital import Orbital
from datetime import datetime, timezone, timedelta
import warnings
warnings.filterwarnings('ignore')
orb = Orbital('VANGUARD', line1='{TLE1}', line2='{TLE2}')
def compute(i):
    dt = datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(days=178.78495062, minutes=i['dt_minutes'])
    pos, vel = orb.get_position(dt, False)
    return [round(float(x), 4) for x in pos]
"""

ENGINES = [
    Engine("sgp4", "Vallado SGP4 / Satrec", python=PY("sgp4"), code=SGP4_CODE),
    Engine("skyfield", "Vallado SGP4 / Satrec", python=PY("skyfield"), code=SKYFIELD_CODE),
    Engine("pyorbital", "PyTroll SGDP4 pure-Python", python=PY("pyorbital"), code=PYORBITAL_CODE),
]

CASES = [
    (
        {"dt_minutes": 0.0},
        {"value": [7022.4653, -1400.0830, 0.0400], "source": "Vallado AIAA-2006-6753 Table 4 Vanguard 1 at epoch", "tolerance": 0.005}
    ),
    (
        {"dt_minutes": 60.0},
        None
    ),
    (
        {"dt_minutes": 360.0},
        None
    ),
    (
        {"dt_minutes": 1440.0},
        None
    ),
]

if __name__ == "__main__":
    out = []
    verdicts = {}
    for inp, ref in CASES:
        bnd = crosscheck("SGP4 TEME Position Vector", inp, ENGINES, 0.005, "km", "norm", reference=ref)
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1
        print(f"CASE dt={inp['dt_minutes']} min : verdict={bnd['verdict']} lineages={len(bnd['independent_lineages'])}")
        for r in bnd["engines"]:
            val = r.get("value", r.get("error", "")[:60])
            print(f"   {r['engine']:12}: {val}")

    evidence_file = Path(__file__).resolve().parents[1] / "evidence" / "XC-004_sgp4_evidence.json"
    evidence_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nWritten {len(out)} crosscheck bundles to {evidence_file}")
    print(f"Verdicts summary: {verdicts}")
