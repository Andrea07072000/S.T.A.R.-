"""Cross-check of star_geodesic against three independent geodesic implementations (S.T.A.R., 2026-10-06).

  python crosscheck_geodesic.py  ->  12_EVIDENCE/crosscheck_geodesic_20261006.json

Lineages, each in its own interpreter:
  proj         PROJ geodesic routines in C (Karney's series) through pyproj.Geod;
  geographiclib  GeographicLib, pure-Python port (Karney's series), installed with geopy;
  pygeodesy_exact  PyGeodesy GeodesicExact (elliptic integrals, not the series).
Every lineage is first PROBED on the published line Flinders Peak - Buninyong (Geoscience Australia / ICSM GDA
technical manual: 54972.271 m, azimuths 306 52 05.37 and 127 10 25.07): within 1 mm and 0.01 arcsec, or excluded.
Corpus (seed 20261006): 440 inverse problems (300 random pairs over the globe, 100 short baselines from 1 m to 10 km,
40 pairs within 2 degrees of the antipode)
and 400 direct problems (random start, azimuth and distance up to 20 000 km). Where star_geodesic refuses (nearly
antipodal pairs) the case is counted as a refusal, not compared.
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_geodesic as sg  # noqa: E402


def dms(d, m, s):
    return (abs(d) + m / 60 + s / 3600) * (1 if d >= 0 else -1)


FLINDERS, BUNINYONG = (dms(-37, 57, 3.72030), dms(144, 25, 29.52440)), (dms(-37, 39, 10.15610), dms(143, 55, 35.38390))
PUBLISHED = (54972.271, dms(306, 52, 5.37), (dms(127, 10, 25.07) + 180.0) % 360.0)     # forward azimuth at Buninyong
V = ROOT / ".venvs"
DRIVERS = {
    "proj": (V / "pyproj", "from pyproj import Geod\ng = Geod(ellps='WGS84')\n"
             "def inv(a, b, c, d):\n    f, r, s = g.inv(b, a, d, c)\n    return [s, f % 360.0, (r + 180.0) % 360.0]\n"
             "def fwd(a, b, az, s):\n    lon, lat, r = g.fwd(b, a, az, s)\n    return [lat, lon, (r + 180.0) % 360.0]\n"),
    "geographiclib": (V / "geopy", "from geographiclib.geodesic import Geodesic\ng = Geodesic.WGS84\n"
                      "def inv(a, b, c, d):\n    r = g.Inverse(a, b, c, d)\n    return [r['s12'], r['azi1'] % 360.0, r['azi2'] % 360.0]\n"
                      "def fwd(a, b, az, s):\n    r = g.Direct(a, b, az, s)\n    return [r['lat2'], r['lon2'], r['azi2'] % 360.0]\n"),
    "pygeodesy_exact": (V / "pygeodesy", "from pygeodesy.geodesicx import GeodesicExact\ng = GeodesicExact()\n"
                        "def inv(a, b, c, d):\n    r = g.Inverse(a, b, c, d)\n    return [float(r.s12), float(r.azi1) % 360.0, float(r.azi2) % 360.0]\n"
                        "def fwd(a, b, az, s):\n    r = g.Direct(a, b, az, s)\n    return [float(r.lat2), float(r.lon2), float(r.azi2) % 360.0]\n"),
}
RUNNER = ("\nimport json, sys\np = json.load(sys.stdin)\nout = {'inv': [], 'fwd': []}\n"
          "for k, f in (('inv', inv), ('fwd', fwd)):\n    for c in p[k]:\n        try:\n            out[k].append([float(v) for v in f(*c)])\n"
          "        except Exception as e:\n            out[k].append('error:' + type(e).__name__)\nprint('@@' + json.dumps(out))\n")


def ang(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def corpus():
    rnd = random.Random(20261006)
    lat = lambda: math.degrees(math.asin(rnd.uniform(-1, 1)))            # uniform on the sphere
    inv = [list(FLINDERS) + list(BUNINYONG)]
    inv += [[lat(), rnd.uniform(-180, 180), lat(), rnd.uniform(-180, 180)] for _ in range(300)]
    for _ in range(100):
        la, lo, step = rnd.uniform(-85, 85), rnd.uniform(-180, 180), 10 ** rnd.uniform(-5, -1)
        inv.append([la, lo, la + rnd.uniform(-1, 1) * step, lo + rnd.uniform(-1, 1) * step])
    for _ in range(40):                                  # within 2 degrees of the antipode: where Vincenty is known to fail
        la, lo = rnd.uniform(-80, 80), rnd.uniform(-180, 0)
        inv.append([la, lo, -la + rnd.uniform(-2, 2), lo + 180 + rnd.uniform(-2, 2)])
    fwd = [[lat(), rnd.uniform(-180, 180), rnd.uniform(0, 360), 10 ** rnd.uniform(0, math.log10(2e7))] for _ in range(400)]
    return {"inv": inv, "fwd": fwd}


def band(s):
    return "<1 km" if s < 1e3 else "<100 km" if s < 1e5 else "<5000 km" if s < 5e6 else "<19000 km" if s < 1.9e7 else ">=19000 km"


def main():
    c = corpus()
    mine_inv, refused = [], 0
    for case in c["inv"]:
        try:
            mine_inv.append(sg.inverse(*case))
        except RuntimeError:
            mine_inv.append(None)
            refused += 1
    mine_fwd = [sg.direct(*case) for case in c["fwd"]]
    out = {"inverse_cases": len(c["inv"]) - 1, "direct_cases": len(c["fwd"]), "seed": 20261006, "star_geodesic_refusals_nearly_antipodal": refused,
           "published": {"source": "Flinders Peak - Buninyong", "star_geodesic": {"distance_diff_m": abs(mine_inv[0][0] - PUBLISHED[0]),
                         "azimuth1_diff_arcsec": 3600 * ang(mine_inv[0][1], PUBLISHED[1]), "azimuth2_diff_arcsec": 3600 * ang(mine_inv[0][2], PUBLISHED[2])}},
           "lineages": {}}
    for name, (venv, driver) in DRIVERS.items():
        r = subprocess.run([str(venv / "Scripts" / "python.exe"), "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(c),
                           capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if len(res["inv"]) != len(c["inv"]) or len(res["fwd"]) != len(c["fwd"]):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = sum(isinstance(x, str) for x in res["inv"] + res["fwd"])
        p = res["inv"][0]
        valid = isinstance(p, list) and abs(p[0] - PUBLISHED[0]) <= 1e-3 and 3600 * ang(p[1], PUBLISHED[1]) <= 0.01 and 3600 * ang(p[2], PUBLISHED[2]) <= 0.01
        entry = {"probe_valid": valid, "errors": errors}
        if valid:
            dist, az = {}, 0.0
            for case, m, x in zip(c["inv"][1:], mine_inv[1:], res["inv"][1:]):
                if m is None or isinstance(x, str):
                    continue
                k = band(x[0])
                dist[k] = max(dist.get(k, 0.0), abs(m[0] - x[0]))
                if x[0] > 1.0 and max(abs(case[0]), abs(case[2])) < 89.9:          # azimuth is ill-defined at the poles
                    az = max(az, 3600 * ang(m[1], x[1]), 3600 * ang(m[2], x[2]))
            pos = 0.0
            for m, x in zip(mine_fwd, res["fwd"]):
                if isinstance(x, list):
                    dlat = math.radians(m[0] - x[0]) * sg.A
                    dlon = math.radians(ang(m[1], x[1])) * sg.A * math.cos(math.radians(x[0]))
                    pos = max(pos, math.hypot(dlat, dlon))
            entry.update(max_distance_diff_m_by_band={k: dist[k] for k in sorted(dist)}, max_distance_diff_m=max(dist.values()),
                         max_azimuth_diff_arcsec=az, direct_max_position_diff_m=pos)
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", errors,
              "dist %.2e m, az %.2e arcsec, direct %.2e m" % (entry["max_distance_diff_m"], entry["max_azimuth_diff_arcsec"],
                                                             entry["direct_max_position_diff_m"]) if valid else p, flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_geodesic_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("published:", out["published"]["star_geodesic"], "| refusals", refused, "->", dest.name)


if __name__ == "__main__":
    main()
