"""Cross-check of star_lcc against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_lcc.py  ->  12_EVIDENCE/crosscheck_lcc_20261006.json

Lineages, each in its own interpreter:
  proj       PROJ through pyproj: +proj=lcc forward, inverse and the scale factor from get_factors (C; PROJ obtains the
             factors by numerical differentiation, so the scale is compared to 1e-8 relative, not to rounding);
  pygeodesy  PyGeodesy lcc.Conic / toLcc / Lcc.toLatLon (Python, Snyder's formulas with its own iteration).
Probe (published): Snyder, Map Projections - A Working Manual (USGS PP 1395), numerical example for the Lambert
conformal conic, p. 296: Clarke 1866 (a = 6378206.4 m, e^2 = 0.00676866), standard parallels 33 N and 45 N, origin
23 N 96 W, point 35 N 75 W: x = 1894410.9 m, y = 1564649.5 m, k = 0.9970171. A lineage further than 0.06 m is excluded.
Corpus (seed 20261006): 600 cases on WGS-84: cones in both hemispheres with standard parallels 5 to 80 deg from the
equator (60 of them tangent, lat1 = lat2 = lat0: PyGeodesy takes the origin as the parallel of a tangent cone), points up to 60 deg of longitude from the central meridian and from 60 deg
on the far side of the equator to 85 deg on the near side.
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
import star_lcc as sl  # noqa: E402

CLARKE = (6378206.4, 1.0 / 294.978698214)
SNYDER = ([35.0, -75.0, 33.0, 45.0, 23.0, -96.0, True], (1894410.9, 1564649.5), 0.9970171)
PROJ = ("from pyproj import Proj\ndef f(lat, lon, p1, p2, lat0, lon0, clarke):\n"
        "    e = dict(a=6378206.4, rf=294.978698214) if clarke else dict(ellps='WGS84')\n"
        "    p = Proj(proj='lcc', lat_1=p1, lat_2=p2, lat_0=lat0, lon_0=lon0, **e)\n"
        "    x, y = p(lon, lat); lo, la = p(x, y, inverse=True)\n"
        "    return {'xy': [x, y], 'back': [la, lo], 'k': float(p.get_factors(lon, lat).meridional_scale)}\n")
PYGEODESY = ("from pygeodesy import lcc, Datums\nfrom pygeodesy.ellipsoidalVincenty import LatLon\nN = [0]\ndef f(lat, lon, p1, p2, lat0, lon0, clarke):\n"
             "    d = Datums.NAD27 if clarke else Datums.WGS84\n"
             "    N[0] += 1\n"
             "    c = lcc.Conic(LatLon(lat0, lon0, datum=d), p1, p2, E0=0, N0=0, name='c%d' % N[0])\n"
             "    l = lcc.toLcc(LatLon(lat, lon, datum=d), conic=c); b = l.toLatLon(LatLon)\n"
             "    return {'xy': [float(l.easting), float(l.northing)], 'back': [float(b.lat), float(b.lon)]}\n")
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
        cases.append([s * rnd.uniform(-60, 85), (lon0 + rnd.uniform(-60, 60) + 180.0) % 360.0 - 180.0, s * p1, s * p2, s * (p1 if k < 60 else rnd.uniform(0, 80)), lon0, False])
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
            fwd = inv = 0.0
            kk = None
            n = skipped = 0
            skipped_diff = 0.0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                if name == "pygeodesy" and abs(c[1] - c[5]) > 180.0:
                    # CANDIDATE FINDING (third-party, not reported): PyGeodesy does not reduce the longitude difference across the
                    # date line and lands elsewhere on the cone; PROJ and star_lcc agree there. Counted, not compared.
                    skipped += 1
                    mx, my = sl.lcc_forward(*c[:6])
                    skipped_diff = max(skipped_diff, math.hypot(mx - x["xy"][0], my - x["xy"][1]))
                    continue
                n += 1
                mx, my = sl.lcc_forward(*c[:6])
                # the plane coordinates reach 1e8 m far from the parallels: the difference is taken relative to the distance from the cone's pole
                fwd = max(fwd, math.hypot(mx - x["xy"][0], my - x["xy"][1]) / max(1.0, math.hypot(*x["xy"])) * 6.4e6)
                inv = max(inv, ground(*sl.lcc_inverse(x["xy"][0], x["xy"][1], *c[2:6]), c[0], c[1]))
                if "k" in x:
                    kk = max(kk or 0.0, abs(sl.lcc_scale(c[0], c[2], c[3]) / x["k"] - 1.0))
            entry.update(compared=n, date_line_cases_not_compared=skipped, largest_plane_difference_in_those_m=skipped_diff, max_forward_m_per_earth_radius=fwd, max_inverse_vs_truth_m=inv, max_scale_rel_diff=kk)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:]: v for k, v in entry.items() if k.startswith("max_") and v is not None}, flush=True)
    L = out["lineages"]
    P, G = L["proj"], L["pygeodesy"]
    mine = sl.lcc_forward(*SNYDER[0][:6], *CLARKE)
    snyder = max(abs(mine[0] - SNYDER[1][0]), abs(mine[1] - SNYDER[1][1]))
    k_pub = abs(sl.lcc_scale(35.0, 33.0, 45.0, *CLARKE) - SNYDER[2])
    need = [P.get("max_forward_m_per_earth_radius"), G.get("max_forward_m_per_earth_radius"), P.get("max_inverse_vs_truth_m"), G.get("max_inverse_vs_truth_m"), P.get("max_scale_rel_diff")]
    ok = all(v["probe_valid"] and not v["errors"] for v in L.values()) and P.get("compared") == 600         and G.get("compared", 0) + G.get("date_line_cases_not_compared", 0) == 600 and G.get("compared", 0) >= 500 and all(x is not None for x in need) \
        and max(need[0], need[2]) < 1e-6 and max(need[1], need[3]) < 1e-4 and need[4] < 1e-8 and snyder < 0.06 and k_pub < 6e-8
    out["published"] = {"source": "Snyder, USGS PP 1395, p. 296: x = 1894410.9 m, y = 1564649.5 m, k = 0.9970171", "star_lcc": list(mine), "abs_diff_m": snyder, "scale_abs_diff": k_pub}
    if all(x is not None for x in need):
        out["summary"] = {"ok": ok, "lineages": ["PROJ +proj=lcc and get_factors (C)", "PyGeodesy lcc.Conic / toLcc (Python)", "Snyder, USGS PP 1395, p. 296"],
                          "claim": "star_lcc reproduces the Lambert conformal conic of two independent libraries, in both hemispheres and for the tangent cone",
                          "crosscheck": f"600 cones and points on WGS-84 (60 tangent cones; PyGeodesy compared on {G.get('compared')}, the {G.get('date_line_cases_not_compared')} that cross the date line excluded): forward within {max(need[:2]):.1e} m per Earth radius of plane distance of PROJ and PyGeodesy; "
                                        f"star_lcc inverse of their plane coordinates within {max(need[2:4]):.1e} m of the starting point; scale factor within {need[4]:.1e} relative of PROJ; "
                                        f"Snyder's example within {snyder:.3f} m (printed to 0.1 m) and its k within {k_pub:.1e}",
                          "benchmark": f"forward: PROJ {need[0]:.1e}, PyGeodesy {need[1]:.1e} (m per Earth radius); inverse: {need[2]:.1e} m, {need[3]:.1e} m"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_lcc_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "Snyder diff %.3f m, k diff %.1e" % (snyder, k_pub), "->", dest.name)


if __name__ == "__main__":
    main()
