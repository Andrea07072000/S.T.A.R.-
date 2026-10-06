"""Cross-check of star_coverage against two independent geometry libraries on a sphere (S.T.A.R., 2026-10-06).

  python crosscheck_coverage.py  ->  12_EVIDENCE/crosscheck_coverage_20261006.json

Lineages, each in its own interpreter:
  pymap3d  pymap3d.geodetic2aer with a spherical Ellipsoid (semi-axes both equal to the radius);
  proj     PROJ +proj=topocentric with +a = +b = radius, through pyproj; elevation and range from its East-North-Up.
Neither knows the closed-form coverage formulas: they convert coordinates. For a ground point on the equator and a
satellite at altitude h whose sub-satellite point is `lam` degrees away, each returns the elevation and the range.
Probe (textbook): a geostationary satellite (h = 35 786 km) is at the zenith, 35 786 km away, over its sub-satellite
point, and on the horizon (elevation 0 within 0.001 deg) at a central angle of 81.2995 deg; a lineage that misses is out.
Corpus (seed 20261006): 400 pairs, altitude from 200 km to 400 000 km (log-uniform), central angle from 0 to the horizon
and a little beyond. Compared: elevation; slant range and central angle recovered from the library's elevation.
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
import star_coverage as sc  # noqa: E402

R = sc.EARTH_RADIUS_KM
PYMAP3D = f"R = {R!r}\n" + '''
import pymap3d
ELL = pymap3d.Ellipsoid(R * 1e3, R * 1e3)
def f(h, lam):
    az, el, rng = pymap3d.geodetic2aer(lam, 0.0, h * 1e3, 0.0, 0.0, 0.0, ell=ELL)
    return [float(el), float(rng) / 1e3]
'''
PROJ = f"R = {R!r}\n" + '''
import math
import pyproj
T = pyproj.Transformer.from_pipeline(f"+proj=topocentric +a={R * 1e3!r} +b={R * 1e3!r} +lat_0=0 +lon_0=0 +h_0=0")
def f(h, lam):
    r = (R + h) * 1e3
    e, n, u = T.transform(r * math.cos(math.radians(lam)), 0.0, r * math.sin(math.radians(lam)))
    return [math.degrees(math.atan2(u, math.hypot(e, n))), math.sqrt(e * e + n * n + u * u) / 1e3]
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:80])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"pymap3d": (str(ROOT / ".venvs" / "pymap3d" / "Scripts" / "python.exe"), PYMAP3D),
           "proj": (str(ROOT / ".venvs" / "pyproj" / "Scripts" / "python.exe"), PROJ)}
GEO = 35786.0
PROBES = [[GEO, 0.0], [GEO, 81.2995]]


def main():
    rnd = random.Random(20261006)
    cases = list(PROBES)
    for _ in range(400):
        h = 10 ** rnd.uniform(math.log10(200.0), math.log10(4e5))
        cases.append([h, rnd.uniform(0.0, 1.05) * sc.central_angle_deg(h)])
    out = {"cases": len(cases) - 2, "seed": 20261006, "radius_km": R, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        a, b = res[0], res[1]
        valid = (isinstance(a, list) and isinstance(b, list) and len(a) == 2 and len(b) == 2 and abs(a[0] - 90.0) < 1e-6
                 and abs(a[1] - GEO) < 1e-6 and abs(b[0]) < 1e-3)
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            d_el = d_rng = d_lam = 0.0
            visible = 0
            for (h, lam), x in zip(cases[2:], res[2:]):
                if isinstance(x, str):
                    continue
                if len(x) != 2:
                    raise SystemExit(f"{name}: malformed answer")
                d_el = max(d_el, abs(sc.elevation_deg(h, lam) - x[0]))
                if x[0] >= 0.0:
                    visible += 1
                    d_rng = max(d_rng, abs(sc.slant_range(h, x[0]) - x[1]) / x[1])
                    d_lam = max(d_lam, abs(sc.central_angle_deg(h, x[0]) - lam))
            entry.update(max_elevation_diff_deg=d_el, max_slant_range_relative_diff=d_rng, max_central_angle_diff_deg=d_lam, visible_cases=visible)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {a} {b}", "errors", len(errors), errors[:1],
              {k: "%.1e" % v for k, v in entry.items() if isinstance(v, float)}, flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_coverage_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("->", dest.name)


if __name__ == "__main__":
    main()
