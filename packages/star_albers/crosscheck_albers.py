"""Cross-check of star_albers against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_albers.py  ->  12_EVIDENCE/crosscheck_albers_20261006.json

Lineages, each in its own interpreter:
  proj       PROJ through pyproj: +proj=aea forward, inverse and the scale factors from get_factors (C; the factors
             come from numerical differentiation, so they are compared to 1e-8 relative);
  pygeodesy  PyGeodesy albers.AlbersEqualArea2 forward / reverse and its scale (Python, Karney's formulation, which
             is not Snyder's). Its y is counted from its own origin latitude: the driver subtracts its y at
             (lat0, lon0), so that both are counted from the same origin.
Probe (published): Snyder, Map Projections - A Working Manual (USGS PP 1395), Albers numerical example, p. 292: Clarke
1866 (a = 6378206.4 m, e^2 = 0.00676866), standard parallels 29.5 N and 45.5 N, origin 23 N 96 W, point 35 N 75 W:
x = 1885472.7 m, y = 1535925.0 m, h = 1.0085173, k = 0.9915546. A lineage further than 0.06 m is excluded.
Corpus (seed 20261006): 600 cases on WGS-84: cones in both hemispheres with standard parallels 5 to 80 deg from the
equator (60 tangent), points up to 60 deg of longitude from the central meridian (which may sit anywhere, so some
cross the date line) and from 60 deg on the far side of the equator to 85 deg on the near side.
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
import star_albers as sa  # noqa: E402

CLARKE = (6378206.4, 1.0 / 294.978698214)
SNYDER = ([35.0, -75.0, 29.5, 45.5, 23.0, -96.0, True], (1885472.7, 1535925.0), (1.0085173, 0.9915546))
PROJ = ("from pyproj import Proj\ndef f(lat, lon, p1, p2, lat0, lon0, clarke):\n"
        "    e = dict(a=6378206.4, rf=294.978698214) if clarke else dict(ellps='WGS84')\n"
        "    p = Proj(proj='aea', lat_1=p1, lat_2=p2, lat_0=lat0, lon_0=lon0, **e)\n"
        "    x, y = p(lon, lat); lo, la = p(x, y, inverse=True); g = p.get_factors(lon, lat)\n"
        "    return {'xy': [x, y], 'back': [la, lo], 'k': float(g.parallel_scale), 'h': float(g.meridional_scale)}\n")
PYGEODESY = ("from pygeodesy import albers, Datums\nN = [0]\ndef f(lat, lon, p1, p2, lat0, lon0, clarke):\n"
             "    N[0] += 1\n"
             "    A = albers.AlbersEqualArea2(p1, p2, datum=Datums.NAD27 if clarke else Datums.WGS84, name='a%d' % N[0])\n"
             "    r, o = A.forward(lat, lon, lon0=lon0), A.forward(lat0, lon0, lon0=lon0)\n"
             "    b = A.reverse(r.x, r.y, lon0=lon0)\n"
             "    return {'xy': [float(r.x), float(r.y - o.y)], 'back': [float(b.lat), float(b.lon)], 'k': float(r.scale)}\n")
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
    for k in range(600):
        s = rnd.choice((-1, 1))
        p1 = rnd.uniform(5, 80)
        p2 = p1 if k < 60 else rnd.uniform(5, 80)
        lon0 = rnd.uniform(-180, 180)
        cases.append([s * rnd.uniform(-60, 85), (lon0 + rnd.uniform(-60, 60) + 180.0) % 360.0 - 180.0, s * p1, s * p2, s * rnd.uniform(0, 80), lon0, False])
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
        valid = isinstance(p, dict) and len(p.get("xy", [])) == 2 and abs(p["xy"][0] - SNYDER[1][0]) < 0.06 and abs(p["xy"][1] - SNYDER[1][1]) < 0.06
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            fwd = inv = kk = 0.0
            hh = None
            n = 0
            worst = None
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                mx, my = sa.albers_forward(*c[:6])
                d = math.hypot(mx - x["xy"][0], my - x["xy"][1])
                if d > fwd:
                    fwd, worst = d, [round(v, 3) for v in c[:6]]
                inv = max(inv, ground(*sa.albers_inverse(x["xy"][0], x["xy"][1], *c[2:6]), c[0], c[1]))
                h, k = sa.albers_scale(c[0], c[2], c[3])
                kk = max(kk, abs(k / x["k"] - 1.0))
                if "h" in x:
                    hh = max(hh or 0.0, abs(h / x["h"] - 1.0))
            entry.update(compared=n, max_forward_m=fwd, worst_forward_case=worst, max_inverse_vs_truth_m=inv, max_k_rel_diff=kk, max_h_rel_diff=hh)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:]: v for k, v in entry.items() if k.startswith("max_") and v is not None},
              entry.get("worst_forward_case"), flush=True)
    L = out["lineages"]
    P, G = L["proj"], L["pygeodesy"]
    mine = sa.albers_forward(*SNYDER[0][:6], *CLARKE)
    snyder = max(abs(mine[0] - SNYDER[1][0]), abs(mine[1] - SNYDER[1][1]))
    hk = sa.albers_scale(35.0, 29.5, 45.5, *CLARKE)
    hk_pub = max(abs(hk[0] - SNYDER[2][0]), abs(hk[1] - SNYDER[2][1]))
    need = [P.get("max_forward_m"), G.get("max_forward_m"), P.get("max_inverse_vs_truth_m"), G.get("max_inverse_vs_truth_m"), P.get("max_k_rel_diff"), G.get("max_k_rel_diff"), P.get("max_h_rel_diff")]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and all(x is not None for x in need) \
        and max(need[:4]) < 1e-5 and need[4] < 1e-8 and need[5] < 1e-12 and need[6] < 1e-8 and snyder < 0.06 and hk_pub < 6e-8
    out["published"] = {"source": "Snyder, USGS PP 1395, p. 292: x = 1885472.7 m, y = 1535925.0 m, h = 1.0085173, k = 0.9915546", "star_albers": list(mine), "abs_diff_m": snyder,
                        "scale_abs_diff": hk_pub}
    if all(x is not None for x in need):
        out["summary"] = {"ok": ok, "lineages": ["PROJ +proj=aea and get_factors (C)", "PyGeodesy albers.AlbersEqualArea2 (Python, Karney)", "Snyder, USGS PP 1395, p. 292"],
                          "claim": "star_albers reproduces the Albers equal-area conic of two independent libraries, in both hemispheres, across the date line and for the tangent cone",
                          "crosscheck": f"600 cones and points on WGS-84 (60 tangent cones): forward within {need[0]:.1e} m of PROJ and {need[1]:.1e} m of PyGeodesy; "
                                        f"star_albers inverse of their plane coordinates within {max(need[2], need[3]):.1e} m of the starting point; parallel scale within "
                                        f"{need[5]:.1e} of PyGeodesy and {need[4]:.1e} of PROJ; Snyder's example within {snyder:.3f} m (printed to 0.1 m), its h and k within {hk_pub:.1e}",
                          "benchmark": f"forward: PROJ {need[0]:.1e} m, PyGeodesy {need[1]:.1e} m; inverse: {need[2]:.1e} m, {need[3]:.1e} m"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_albers_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "Snyder diff %.3f m, h/k diff %.1e" % (snyder, hk_pub), "->", dest.name)


if __name__ == "__main__":
    main()
