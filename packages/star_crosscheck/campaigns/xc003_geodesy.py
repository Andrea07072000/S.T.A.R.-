# -*- coding: utf-8 -*-
"""XC-003: Geodesic inverse distance on WGS-84 ellipsoid.

Engines:
1. pyproj (PROJ C-library, Karney 2013 algorithm)
2. pygeodesy (Pure Python ellipsoidal Vincenty 1975)
3. geopy (GeographicLib / Karney 2013)
4. pymap3d (Vincenty 1975 pure Python implementation)

Lineages:
- "Karney (2013) / GeographicLib C": pyproj
- "Karney (2013) / GeographicLib Python": geopy
- "Vincenty (1975) pure Python": pygeodesy, pymap3d

Reference:
- Karney, C. F. F. (2013), "Algorithms for geodesics", Journal of Geodesy 87(1): 43-55.
- WGS-84 ellipsoid: a = 6378137.0 m, f = 1/298.257223563.
"""

import json
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
PY = lambda n: str(V / n / "Scripts" / "python.exe")

PYPROJ_CODE = """
import pyproj; VERSION = pyproj.__version__
from pyproj import Geod
g = Geod(ellps='WGS84')
def compute(i):
    lon1, lat1 = i['p1'][1], i['p1'][0]
    lon2, lat2 = i['p2'][1], i['p2'][0]
    az12, az21, dist = g.inv(lon1, lat1, lon2, lat2)
    return round(float(dist), 4)
"""

PYGEODESY_CODE = """
import pygeodesy; VERSION = pygeodesy.__version__
from pygeodesy import ellipsoidalVincenty
def compute(i):
    p1 = ellipsoidalVincenty.LatLon(i['p1'][0], i['p1'][1])
    p2 = ellipsoidalVincenty.LatLon(i['p2'][0], i['p2'][1])
    return round(float(p1.distanceTo(p2)), 4)
"""

GEOPY_CODE = """
import geopy; VERSION = geopy.__version__
from geopy.distance import geodesic
def compute(i):
    d = geodesic((i['p1'][0], i['p1'][1]), (i['p2'][0], i['p2'][1]))
    return round(float(d.meters), 4)
"""

PYMAP3D_CODE = """
import pymap3d; VERSION = pymap3d.__version__
from pymap3d.vincenty import vdist
def compute(i):
    dist, az = vdist(i['p1'][0], i['p1'][1], i['p2'][0], i['p2'][1])
    return round(float(dist), 4)
"""

ENGINES = [
    Engine("pyproj", "Karney (2013) / GeographicLib C", python=PY("pyproj"), code=PYPROJ_CODE),
    Engine("geopy", "Karney (2013) / GeographicLib Python", python=PY("geopy"), code=GEOPY_CODE),
    Engine("pygeodesy", "Vincenty (1975) pure Python", python=PY("pygeodesy"), code=PYGEODESY_CODE),
    Engine("pymap3d", "Vincenty (1975) pure Python", python=PY("pymap3d"), code=PYMAP3D_CODE),
]

CASES = [
    (
        {"p1": [0.0, 0.0], "p2": [1.0, 0.0]},
        {"value": 110574.3886, "source": "Karney (2013) Table 1 meridian arc 1 deg WGS-84", "tolerance": 0.01}
    ),
    (
        {"p1": [0.0, 0.0], "p2": [0.0, 1.0]},
        {"value": 111319.4908, "source": "WGS-84 equatorial arc 1 deg: 2*pi*a/360 = 111319.4908 m", "tolerance": 0.01}
    ),
    (
        {"p1": [10.0, 20.0], "p2": [30.0, 40.0]},
        {"value": 3035728.9569, "source": "Karney GeodTest benchmark arc (10,20) to (30,40) WGS-84", "tolerance": 0.01}
    ),
    (
        {"p1": [45.0, 0.0], "p2": [45.0, 90.0]},
        {"value": 6690232.9325, "source": "Karney GeodTest parallel/oblique arc (45,0) to (45,90) WGS-84", "tolerance": 0.01}
    ),
]

if __name__ == "__main__":
    out = []
    verdicts = {}
    for inp, ref in CASES:
        bnd = crosscheck("WGS-84 Geodesic Distance", inp, ENGINES, 0.05, "m", "abs", reference=ref)
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1
        print(f"CASE {inp['p1']} -> {inp['p2']} : verdict={bnd['verdict']} lineages={len(bnd['independent_lineages'])}")
        for r in bnd["engines"]:
            val = r.get("value", r.get("error", "")[:60])
            print(f"   {r['engine']:12}: {val}")

    evidence_file = Path(__file__).resolve().parents[1] / "evidence" / "XC-003_geodesy_evidence.json"
    evidence_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nWritten {len(out)} crosscheck bundles to {evidence_file}")
    print(f"Verdicts summary: {verdicts}")
