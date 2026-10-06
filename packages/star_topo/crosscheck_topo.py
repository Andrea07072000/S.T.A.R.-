"""Cross-check of star_topo against three independent libraries, each in its own interpreter (S.T.A.R., 2026-10-06).

  python crosscheck_topo.py  ->  12_EVIDENCE/crosscheck_topo_20261006.json

Lineages: pymap3d (pure Python), PROJ through pyproj (C, +proj=topocentric), PyGeodesy Ltp.forward on
Karney's ECEF (pure Python, own classes; there the point goes through geodetic coordinates).
Corpus: deterministic (seed 20261006), 400 site/target pairs: sites over the whole globe including both poles and the
antimeridian, heights from -400 m to 9000 m; targets from 1 m to 40 000 km away, plus the EPSG Guidance Note 7-2 example.
Each library is first PROBED on that published example: one that does not reproduce it is excluded from the comparison.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_topo  # noqa: E402

# EPSG Guidance Note 7-2, "Geocentric/topocentric conversions" (EPSG method 9836): site 55 N, 5 E, h = 200 m
EPSG_SITE = (55.0, 5.0, 200.0)
EPSG_POINT = (3771793.968, 140253.342, 5124304.349)
EPSG_ENU = (-189013.869, -128642.040, -4220.171)

DRIVERS = {
    "pymap3d": "import pymap3d\ndef f(x,y,z,lat,lon,h):\n    return [float(v) for v in pymap3d.ecef2enu(x,y,z,lat,lon,h)]\n",
    "pyproj": ("import pyproj\ndef f(x,y,z,lat,lon,h):\n"
               "    t = pyproj.Transformer.from_pipeline(f'+proj=topocentric +ellps=WGS84 +lat_0={lat!r} +lon_0={lon!r} +h_0={h!r}')\n"
               "    return [float(v) for v in t.transform(x,y,z)]\n"),
    "pygeodesy": ("from pygeodesy import Ltp, EcefKarney\nfrom pygeodesy.datums import Datums\n"
                  "def f(x,y,z,lat,lon,h):\n    k = EcefKarney(Datums.WGS84)\n    r = Ltp(lat, lon, h, ecef=k).forward(k.reverse(x, y, z))\n"
                  "    return [float(r.x), float(r.y), float(r.z)]\n"),
}
RUNNER = ("\nimport json,sys\nout=[]\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:'+type(e).__name__)\nprint('@@'+json.dumps(out))\n")


def corpus():
    rnd = random.Random(20261006)
    sites = [(90.0, 0.0, 0.0), (-90.0, 123.0, 2800.0), (0.0, 180.0, 0.0), (0.0, -180.0, 10.0), (89.999999, -45.0, 0.0), EPSG_SITE]
    sites += [(rnd.uniform(-90, 90), rnd.uniform(-180, 180), rnd.uniform(-400, 9000)) for _ in range(94)]
    cases = [list(EPSG_POINT) + list(EPSG_SITE)]
    for i, s in enumerate(sites):
        for dist in (1.0, 1e3, 4e5, 4e7):
            az, el = rnd.uniform(0, 360), rnd.uniform(-90, 90)
            cases.append(list(star_topo.aer_to_ecef(az, el, dist, *s)) + list(s))
    return cases[:401]


def run(name, cases):
    py = ROOT / ".venvs" / name / "Scripts" / "python.exe"
    r = subprocess.run([str(py), "-c", DRIVERS[name] + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=600)
    line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
    if r.returncode or not line:
        raise SystemExit(f"{name}: driver failed\n{r.stderr[-600:]}")
    res = json.loads(line[0][2:])
    if not isinstance(res, list) or len(res) != len(cases):          # one answer per case, or the run is void
        raise SystemExit(f"{name}: {len(res) if isinstance(res, list) else 'no'} answers for {len(cases)} cases")
    return res


def main():
    cases = corpus()
    mine = [list(star_topo.ecef_to_enu(*c)) for c in cases]
    out = {"cases": len(cases), "seed": 20261006, "published": {"source": "EPSG Guidance Note 7-2, method 9836 example",
           "star_topo_abs_diff_m": [abs(a - b) for a, b in zip(mine[0], EPSG_ENU)]}, "lineages": {}}
    for name in DRIVERS:
        res = run(name, cases)
        probe = res[0] if isinstance(res[0], list) else None
        valid = probe is not None and all(abs(a - b) <= 1e-3 for a, b in zip(probe, EPSG_ENU))
        errors = sum(isinstance(r, str) for r in res)
        worst = {"1 m": 0.0, "1 km": 0.0, "400 km": 0.0, "40000 km": 0.0}
        if valid:
            for k, (m, r) in enumerate(zip(mine[1:], res[1:])):
                if isinstance(r, list):
                    key = list(worst)[k % 4]
                    worst[key] = max(worst[key], max(abs(a - b) for a, b in zip(m, r)))
        out["lineages"][name] = {"probe_valid": valid, "errors": errors, "max_abs_diff_m_by_target_distance": worst if valid else None}
        print(name, "valid" if valid else "EXCLUDED", "errors", errors, worst if valid else "", flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_topo_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("published example, star_topo abs diff (m):", out["published"]["star_topo_abs_diff_m"], "->", dest.name)


if __name__ == "__main__":
    main()
