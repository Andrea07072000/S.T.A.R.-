"""Cross-check of star_mercator against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_mercator.py  ->  12_EVIDENCE/crosscheck_mercator_20261006.json

Lineages, each in its own interpreter:
  proj       PROJ through pyproj: +proj=merc with lat_ts (forward, inverse, scale factor by numerical differentiation: near 89 deg,
             where the scale reaches 57, its error grows to 1e-7 relative)
             and +proj=webmerc (C);
  pygeodesy  PyGeodesy Ellipsoid.auxIsometric (the isometric latitude, from which y = a k0 psi) and webmercator.toWm
             with its inverse (Python). It does not compute x or the scale of the ellipsoidal projection.
Probe (published): Snyder, Map Projections - A Working Manual (USGS PP 1395), Mercator numerical example, p. 266:
Clarke 1866 (a = 6378206.4 m, e^2 = 0.00676866), central meridian 180, point 35 N 75 W: x = 11688673.7 m and
k = 1.2194146 (its y is not used as a probe: the digit recalled for it was not confirmed). PROJ is probed on x (0.06 m);
PyGeodesy on the isometric latitude of 35 deg on Clarke 1866 agreeing with PROJ's y of that example to 1e-6 m.
Corpus (seed 20261006): 600 cases on WGS-84: latitudes within +-89, any longitude and central meridian, latitude of
true scale within +-80.
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
import star_mercator as sm  # noqa: E402

CLARKE = (6378206.4, 1.0 / 294.978698214)
SNYDER = ([35.0, -75.0, 180.0, 0.0, True], 11688673.7, 1.2194146)
PROJ = ("from pyproj import Proj\nW = Proj(proj='webmerc', datum='WGS84')\ndef f(lat, lon, lon0, ts, clarke):\n"
        "    e = dict(a=6378206.4, rf=294.978698214) if clarke else dict(ellps='WGS84')\n"
        "    p = Proj(proj='merc', lon_0=lon0, lat_ts=ts, **e)\n"
        "    x, y = p(lon, lat); lo, la = p(x, y, inverse=True); wx, wy = W(lon, lat)\n"
        "    return {'xy': [x, y], 'back': [la, lo], 'k': float(p.get_factors(lon, lat).meridional_scale), 'web': [wx, wy]}\n")
PYGEODESY = ("import math\nfrom pygeodesy import Ellipsoids, webmercator\ndef f(lat, lon, lon0, ts, clarke):\n"
             "    E = Ellipsoids.Clarke1866 if clarke else Ellipsoids.WGS84\n"
             "    out = {'psi': math.radians(float(E.auxIsometric(lat))), 'a': float(E.a)}\n"
             "    if abs(lat) <= 85.05:                    # PyGeodesy refuses Web Mercator beyond its square: not asked there\n"
             "        w = webmercator.toWm(lat, lon); out['web'] = [float(w.x), float(w.y)]\n"
             "    return out\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"proj": (venv("pyproj"), PROJ), "pygeodesy": (venv("pygeodesy"), PYGEODESY)}


def ground(lat, lon, lat2, lon2):
    return 6.4e6 * math.hypot(math.radians(lat - lat2), math.radians((lon - lon2 + 180.0) % 360.0 - 180.0) * math.cos(math.radians(lat)))


def main():
    rnd = random.Random(20261006)
    cases = [SNYDER[0]] + [[rnd.uniform(-89, 89), rnd.uniform(-180, 180), rnd.uniform(-180, 180), rnd.uniform(-80, 80), False] for _ in range(600)]
    out = {"cases": len(cases) - 1, "seed": 20261006, "lineages": {}}
    y_snyder_proj = None
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
            valid = isinstance(p, dict) and len(p.get("xy", [])) == 2 and abs(p["xy"][0] - SNYDER[1]) < 0.06 and abs(p.get("k", 0.0) - SNYDER[2]) < 6e-8
            y_snyder_proj = p["xy"][1] if valid else None
        else:
            valid = isinstance(p, dict) and y_snyder_proj is not None and abs(p.get("a", 0.0) * p.get("psi", 0.0) - y_snyder_proj) < 1e-6
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"forward_m": None, "inverse_m": None, "scale_rel": None, "isometric_latitude_m": None, "web_forward_m": 0.0, "web_inverse_m": 0.0}
            n = beyond = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                if "web" in x:
                    wx, wy = sm.web_mercator_forward(c[0], c[1])
                    m["web_forward_m"] = max(m["web_forward_m"], math.hypot(wx - x["web"][0], wy - x["web"][1]))
                    m["web_inverse_m"] = max(m["web_inverse_m"], ground(*sm.web_mercator_inverse(x["web"][0], x["web"][1]), c[0], c[1]))
                else:                                       # beyond the Web Mercator square (|lat| > 85.05 deg): PyGeodesy was not asked
                    beyond += 1
                if "xy" in x:
                    mx, my = sm.mercator_forward(*c[:4])
                    m["forward_m"] = max(m["forward_m"] or 0.0, math.hypot(mx - x["xy"][0], my - x["xy"][1]))
                    m["inverse_m"] = max(m["inverse_m"] or 0.0, ground(*sm.mercator_inverse(x["xy"][0], x["xy"][1], c[2], c[3]), c[0], c[1]))
                    m["scale_rel"] = max(m["scale_rel"] or 0.0, abs(sm.mercator_scale(c[0], c[3]) / x["k"] - 1.0))
                else:                                       # y of the equatorial-scale projection is a * psi
                    m["isometric_latitude_m"] = max(m["isometric_latitude_m"] or 0.0, abs(sm.mercator_forward(c[0], 0.0)[1] - x["a"] * x["psi"]))
            entry.update(compared=n, refused_beyond_web_square=beyond, **{"max_" + k: v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:]: v for k, v in entry.items() if k.startswith("max_") and v is not None}, flush=True)
    L = out["lineages"]
    P, G = L["proj"], L["pygeodesy"]
    mine = sm.mercator_forward(*SNYDER[0][:4], *CLARKE)
    snyder = abs(mine[0] - SNYDER[1])
    k_pub = abs(sm.mercator_scale(35.0, 0.0, CLARKE[1]) - SNYDER[2])
    need = [P.get("max_forward_m"), P.get("max_inverse_m"), P.get("max_scale_rel"), G.get("max_isometric_latitude_m"), P.get("max_web_forward_m"), G.get("max_web_forward_m"),
            P.get("max_web_inverse_m"), G.get("max_web_inverse_m")]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and G.get("refused_beyond_web_square", 99) <= 30 \
        and all(x is not None for x in need) \
        and need[0] < 1e-6 and need[1] < 1e-6 and need[2] < 5e-7 and need[3] < 1e-6 and max(need[4:]) < 1e-6 and snyder < 0.06 and k_pub < 6e-8
    out["published"] = {"source": "Snyder, USGS PP 1395, p. 266: x = 11688673.7 m, k = 1.2194146", "star_mercator_x": mine[0], "abs_diff_m": snyder, "scale_abs_diff": k_pub}
    if all(x is not None for x in need):
        out["summary"] = {"ok": ok, "lineages": ["PROJ +proj=merc / webmerc and get_factors (C)", "PyGeodesy Ellipsoid.auxIsometric and webmercator.toWm (Python)", "Snyder, USGS PP 1395, p. 266"],
                          "claim": "star_mercator reproduces the ellipsoidal Mercator of PROJ for any latitude of true scale, its isometric latitude agrees with PyGeodesy, and Web Mercator agrees with both",
                          "crosscheck": f"600 cases on WGS-84 (latitudes to +-89, true scale to +-80): forward within {need[0]:.1e} m and inverse within {need[1]:.1e} m of PROJ, scale within "
                                        f"{need[2]:.1e}; y of the equatorial projection within {need[3]:.1e} m of PyGeodesy's isometric latitude; Web Mercator within {max(need[4:6]):.1e} m "
                                        f"(forward) and {max(need[6:]):.1e} m (inverse) of both (PyGeodesy on {G.get('compared')}: it refuses the {G.get('refused_beyond_web_square')} beyond 85.05 deg); Snyder's x within {snyder:.3f} m and k within {k_pub:.1e}",
                          "benchmark": f"ellipsoidal: PROJ {need[0]:.1e} m; isometric latitude: PyGeodesy {need[3]:.1e} m; web: {max(need[4:6]):.1e} m"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_mercator_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "Snyder x diff %.3f m, k diff %.1e" % (snyder, k_pub), "->", dest.name)


if __name__ == "__main__":
    main()
