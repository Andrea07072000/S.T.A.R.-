"""Cross-check of star_polar against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_polar.py  ->  12_EVIDENCE/crosscheck_polar_20261006.json

Lineages, each in its own interpreter:
  proj       PROJ through pyproj: +proj=stere with lat_ts (forward, inverse, scale factor by numerical
             differentiation) and +proj=ups (C);
  pygeodesy  PyGeodesy toUps8 and Ups.toLatLon (Python): UPS only.
Probe (published): Snyder, Map Projections - A Working Manual (USGS PP 1395), polar stereographic numerical example,
p. 314: International ellipsoid (a = 6378388 m, 1/f = 297), south polar aspect, true scale at 71 S, central meridian
100 W, point 75 S 150 E: x = -1540033.6 m, y = -560526.4 m. PROJ is probed on that (0.06 m). PyGeodesy, which offers UPS
only, on the pole (2000000, 2000000) and on the agreement of its inverse with its forward to 1e-6 deg.
Corpus (seed 20261006): 600 cases: both poles, latitudes from the pole to 60 deg beyond the equator's near side limit
used here (down to 20 deg of latitude), true-scale parallels from 50 to 90 deg, any central meridian; UPS on the same points.
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
import star_polar as sp  # noqa: E402

INTL = (6378388.0, 1.0 / 297.0)
SNYDER = ([-75.0, 150.0, -1, -100.0, -71.0, True], (-1540033.6, -560526.4))
PROJ = ("from pyproj import Proj\nU = {1: Proj(proj='ups'), -1: Proj(proj='ups', south=True)}\n"
        "def f(lat, lon, s, lon0, ts, intl):\n"
        "    e = dict(a=6378388.0, rf=297.0) if intl else dict(ellps='WGS84')\n"
        "    p = Proj(proj='stere', lat_0=90 * s, lat_ts=ts, lon_0=lon0, **e)\n"
        "    x, y = p(lon, lat); lo, la = p(x, y, inverse=True); e2, n2 = U[s](lon, lat)\n"
        "    return {'xy': [x, y], 'back': [la, lo], 'k': float(p.get_factors(lon, lat).meridional_scale), 'ups': [e2, n2]}\n")
PYGEODESY = ("from pygeodesy import ups\ndef f(lat, lon, s, lon0, ts, intl):\n"
             "    u = ups.toUps8(lat, lon, strict=False); b = u.toLatLon(); z = ups.toUps8(90.0 * s, 0.0, strict=False)\n"
             "    return {'ups': [float(u.easting), float(u.northing)], 'pole': str(u.pole), 'ups_back': [float(b[0]), float(b[1])],\n"
             "            'at_pole': [float(z.easting), float(z.northing)]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"proj": (venv("pyproj"), PROJ), "pygeodesy": (venv("pygeodesy"), PYGEODESY)}


def ground(lat, lon, lat2, lon2):
    return 6.4e6 * math.hypot(math.radians(lat - lat2), math.radians((lon - lon2 + 180.0) % 360.0 - 180.0) * math.cos(math.radians(lat)))


def main():
    rnd = random.Random(20261006)
    cases = [SNYDER[0]]
    for _ in range(600):
        s = rnd.choice((-1, 1))
        cases.append([s * rnd.uniform(20, 89.999), rnd.uniform(-180, 180), s, rnd.uniform(-180, 180), s * rnd.uniform(50, 90), False])
    out = {"cases": len(cases) - 1, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        p = res[0]
        if name == "proj":
            valid = isinstance(p, dict) and len(p.get("xy", [])) == 2 and abs(p["xy"][0] - SNYDER[1][0]) < 0.06 and abs(p["xy"][1] - SNYDER[1][1]) < 0.06
        else:
            valid = isinstance(p, dict) and p.get("at_pole") == [2000000.0, 2000000.0] and p.get("pole") == "S" and ground(-75.0, 150.0, *p.get("ups_back", [0, 0])) < 0.2
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"forward_m": None, "inverse_m": None, "scale_rel": None, "ups_forward_m": 0.0, "ups_inverse_m": None}
            n = poles = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                pole = "N" if c[2] > 0 else "S"
                up, ue, un = sp.ups_forward(c[0], c[1])
                poles += up != pole or ("pole" in x and x["pole"] != pole)
                m["ups_forward_m"] = max(m["ups_forward_m"], math.hypot(ue - x["ups"][0], un - x["ups"][1]))
                m["ups_inverse_m"] = max(m["ups_inverse_m"] or 0.0, ground(*sp.ups_inverse(pole, x["ups"][0], x["ups"][1]), c[0], c[1]))
                if "xy" in x:
                    mx, my = sp.ps_forward(c[0], c[1], pole, c[3], c[4])
                    m["forward_m"] = max(m["forward_m"] or 0.0, math.hypot(mx - x["xy"][0], my - x["xy"][1]))
                    m["inverse_m"] = max(m["inverse_m"] or 0.0, ground(*sp.ps_inverse(x["xy"][0], x["xy"][1], pole, c[3], c[4]), c[0], c[1]))
                    m["scale_rel"] = max(m["scale_rel"] or 0.0, abs(sp.ps_scale(c[0], pole, c[4]) / x["k"] - 1.0))
            entry.update(compared=n, pole_mismatches=poles, **{"max_" + k: v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:]: v for k, v in entry.items() if k.startswith("max_") and v is not None},
              "pole mismatches", entry.get("pole_mismatches"), flush=True)
    L = out["lineages"]
    P, G = L["proj"], L["pygeodesy"]
    mine = sp.ps_forward(*SNYDER[0][:2], "S", SNYDER[0][3], SNYDER[0][4], 1.0, *INTL)
    snyder = max(abs(mine[0] - SNYDER[1][0]), abs(mine[1] - SNYDER[1][1]))
    need = [P.get("max_forward_m"), P.get("max_inverse_m"), P.get("max_scale_rel"), P.get("max_ups_forward_m"), G.get("max_ups_forward_m"), G.get("max_ups_inverse_m")]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 and v.get("pole_mismatches") == 0 for v in L.values()) \
        and all(x is not None for x in need) and need[0] < 1e-4 and need[1] < 1e-4 and need[2] < 1e-8 and need[3] < 1e-4 and need[4] < 1e-6 and need[5] < 1e-6 and snyder < 0.06
    out["published"] = {"source": "Snyder, USGS PP 1395, p. 314: x = -1540033.6 m, y = -560526.4 m", "star_polar": list(mine), "abs_diff_m": snyder}
    if all(x is not None for x in need):
        out["summary"] = {"ok": ok, "lineages": ["PROJ +proj=stere / ups and get_factors (C)", "PyGeodesy toUps8 / Ups.toLatLon (Python)", "Snyder, USGS PP 1395, p. 314"],
                          "claim": "star_polar reproduces the polar stereographic projection of PROJ for any parallel of true scale and the UPS grid of PROJ and PyGeodesy, at both poles",
                          "crosscheck": f"600 cases at both poles (latitudes 20 to 89.999 deg, true scale at 50 to 90 deg): forward within {need[0]:.1e} m and inverse within {need[1]:.1e} m of PROJ, "
                                        f"scale within {need[2]:.1e} relative; UPS within {need[4]:.1e} m of PyGeodesy and {need[3]:.1e} m of PROJ, inverse within {need[5]:.1e} m; "
                                        f"Snyder's example within {snyder:.3f} m (printed to 0.1 m)",
                          "benchmark": f"UPS forward: PyGeodesy {need[4]:.1e} m, PROJ {need[3]:.1e} m; general: PROJ {need[0]:.1e} m"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_polar_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "Snyder diff %.3f m" % snyder, "->", dest.name)


if __name__ == "__main__":
    main()
