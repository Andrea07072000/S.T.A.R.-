"""Cross-check of star_utm against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_utm.py  ->  12_EVIDENCE/crosscheck_utm_20261006.json

Lineages, each in its own interpreter:
  proj       PROJ through pyproj: +proj=utm and +proj=tmerc (C; the Poder-Engsager extended transverse Mercator);
  pygeodesy  PyGeodesy toUtm8 and Utm.toLatLon (Python; its own Krueger series): UTM zones only.
Probe (published): Snyder, Map Projections - A Working Manual (USGS PP 1395), numerical example for the transverse
Mercator, p. 269: Clarke 1866 ellipsoid (a = 6378206.4 m, e^2 = 0.00676866), central meridian 75 W, k0 = 0.9996,
latitude 40 deg 30' N, longitude 73 deg 30' W: x = 127106.5 m, y = 4484124.4 m. PROJ is probed on that; PyGeodesy, which
is driven on WGS-84 zones only, on the agreement of its inverse with its forward to 1e-6 deg and on its zone number.
Corpus (seed 20261006): 600 points with latitude in [-80, 84] in their own zone (within 3 deg of the central meridian)
and 300 points up to 12 deg from the central meridian (PROJ only).
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
import star_utm as su  # noqa: E402

CLARKE = (6378206.4, 1.0 / 294.978698214)                   # e^2 = 0.00676866 (Snyder)
SNYDER = ([40.5, -73.5, -75.0], (127106.5, 4484124.4))
PROJ = ("from pyproj import Proj\nC = Proj(proj='tmerc', lon_0=-75, k_0=0.9996, a=6378206.4, rf=294.978698214)\nZ = {}\n"
        "def f(lat, lon, lon0):\n"
        "    if lon0 == -75.0 and lat == 40.5:\n        x, y = C(lon, lat); return {'tm': [x, y]}\n"
        "    p = Z.setdefault(lon0, Proj(proj='tmerc', lon_0=lon0, k_0=0.9996, ellps='WGS84'))\n"
        "    x, y = p(lon, lat); lo, la = p(x, y, inverse=True)\n"
        "    return {'tm': [x, y], 'back': [la, lo]}\n")
PYGEODESY = ("from pygeodesy import utm\ndef f(lat, lon, lon0):\n"
             "    u = utm.toUtm8(lat, lon); ll = u.toLatLon()\n"
             "    return {'utm': [int(u.zone), str(u.hemisphere), float(u.easting), float(u.northing)], 'back': [float(ll[0]), float(ll[1])]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"proj": (venv("pyproj"), PROJ), "pygeodesy": (venv("pygeodesy"), PYGEODESY)}


def ground(lat, lon, lat2, lon2):
    """Distance in metres between two nearby geodetic points (local radius 6.4e6 m is enough to size a nanometre)."""
    return 6.4e6 * math.hypot(math.radians(lat - lat2), math.radians((lon - lon2 + 180.0) % 360.0 - 180.0) * math.cos(math.radians(lat)))


def main():
    rnd = random.Random(20261006)
    near, wide = [], []
    for _ in range(600):
        lon = rnd.uniform(-180, 180)
        near.append([rnd.uniform(-80, 84), lon, 6.0 * su.utm_zone(lon) - 183.0])
    for _ in range(300):
        lon0 = float(rnd.randrange(-177, 178, 6))
        wide.append([rnd.uniform(-80, 84), (lon0 + rnd.choice((-1, 1)) * rnd.uniform(3, 12) + 180.0) % 360.0 - 180.0, lon0])
    out = {"cases_in_zone": len(near), "cases_wide": len(wide), "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        cases = [SNYDER[0]] + near + (wide if name == "proj" else [])
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
            valid = isinstance(p, dict) and len(p.get("tm", [])) == 2 and abs(p["tm"][0] - SNYDER[1][0]) < 0.06 and abs(p["tm"][1] - SNYDER[1][1]) < 0.06
        else:
            valid = isinstance(p, dict) and p.get("utm", [0])[0] == 18 and p["utm"][1] == "N" and ground(40.5, -73.5, *p.get("back", [0, 0])) < 0.2
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"forward_in_zone_m": 0.0, "inverse_in_zone_m": 0.0, "forward_wide_m": None, "inverse_wide_m": None}
            n = zones = hemi = 0
            for k, (c, x) in enumerate(zip(cases[1:], res[1:])):
                if isinstance(x, str):
                    continue
                n += 1
                tag = "in_zone" if k < len(near) else "wide"
                if "tm" in x:
                    mx, my = su.tm_forward(*c)
                    fwd, ref = math.hypot(mx - x["tm"][0], my - x["tm"][1]), x["tm"]
                else:
                    # PyGeodesy applies the Norway and Svalbard exceptions of the MGRS grid; star_utm does not (README):
                    # where the zone differs the point is compared in THEIR zone, and the case is counted
                    z, h, e, nn = su.utm_forward(c[0], c[1], x["utm"][0])
                    zones += su.utm_zone(c[1]) != x["utm"][0]
                    hemi += h != x["utm"][1]
                    c = [c[0], c[1], 6.0 * x["utm"][0] - 183.0]
                    fwd = math.hypot(e - x["utm"][2], nn - x["utm"][3])
                    ref = (x["utm"][2] - 500000.0, x["utm"][3] - (10000000.0 if h == "S" else 0.0))
                inv = ground(*su.tm_inverse(ref[0], ref[1], c[2]), *x["back"])
                m[f"forward_{tag}_m"] = max(m[f"forward_{tag}_m"] or 0.0, fwd)
                m[f"inverse_{tag}_m"] = max(m[f"inverse_{tag}_m"] or 0.0, inv)
            entry.update(compared=n, grid_exception_zones=zones, hemisphere_mismatches=hemi, **{"max_" + k: v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:]: v for k, v in entry.items() if k.startswith("max_") and v is not None},
              "grid-exception zones", entry.get("grid_exception_zones"), "hemisphere mismatches", entry.get("hemisphere_mismatches"), flush=True)
    L = out["lineages"]
    P, G = L["proj"], L["pygeodesy"]
    mine = su.tm_forward(*SNYDER[0], *CLARKE)
    snyder = max(abs(mine[0] - SNYDER[1][0]), abs(mine[1] - SNYDER[1][1]))
    need = [P.get("max_forward_in_zone_m"), P.get("max_inverse_in_zone_m"), G.get("max_forward_in_zone_m"), G.get("max_inverse_in_zone_m"),
            P.get("max_forward_wide_m"), P.get("max_inverse_wide_m")]
    ok = all(v["probe_valid"] and not v["errors"] for v in L.values()) and P.get("compared") == 900 and G.get("compared") == 600 \
        and all(x is not None for x in need) and max(need[:4]) < 1e-6 and max(need[4:]) < 1e-3 and G.get("hemisphere_mismatches") == 0 and G.get("grid_exception_zones", 99) <= 5 and snyder < 0.06
    out["published"] = {"source": "Snyder, USGS PP 1395, p. 269 (Clarke 1866, CM 75 W): x = 127106.5 m, y = 4484124.4 m", "star_utm": list(mine), "abs_diff_m": snyder}
    if all(x is not None for x in need):
        out["summary"] = {"ok": ok, "lineages": ["PROJ +proj=tmerc / utm (C, Poder-Engsager)", "PyGeodesy toUtm8 / Utm.toLatLon (Python, Krueger)", "Snyder, USGS PP 1395, p. 269"],
                          "claim": "star_utm reproduces the transverse Mercator of two independent libraries to well below a micrometre inside a UTM zone",
                          "crosscheck": f"600 points in their UTM zone: forward within {max(need[0], need[2]):.1e} m and inverse within {max(need[1], need[3]):.1e} m of PROJ and PyGeodesy, "
                                        f"hemisphere identical, zone identical except {G.get('grid_exception_zones')} point(s) in the Norway/Svalbard grid exceptions (compared in PyGeodesy's zone); 300 points 3 to 12 deg from the central meridian: forward within {need[4]:.1e} m and inverse within "
                                        f"{need[5]:.1e} m of PROJ; Snyder's example within {snyder:.2f} m (printed to 0.1 m)",
                          "benchmark": f"in zone: PROJ {max(need[0], need[1]):.1e} m, PyGeodesy {max(need[2], need[3]):.1e} m; up to 12 deg: {max(need[4], need[5]):.1e} m"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_utm_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "Snyder diff %.3f m" % snyder, "->", dest.name)


if __name__ == "__main__":
    main()
