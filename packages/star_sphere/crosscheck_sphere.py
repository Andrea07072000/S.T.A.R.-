"""Cross-check of star_sphere against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_sphere.py  ->  12_EVIDENCE/crosscheck_sphere_20261006.json

Lineages, each in its own interpreter:
  erfa     ERFA seps (separation) and pas (position angle), C; it has no "offset" routine;
  astropy  astropy.coordinates.angular_separation, position_angle and offset_by (Python/NumPy, own formulas).
Probe (published): Meeus, Astronomical Algorithms, Example 17.a: Arcturus (213.9154, +19.1825) and Spica (201.2983,
-11.1614) are 32.7930 deg apart; a lineage further than 5e-5 deg from that is excluded.
Corpus (seed 20261006): 600 pairs: 300 random over the sphere, 150 closer than 1e-6 deg ... 1 deg, 150 within 1e-6 ... 1
deg of the antipode; offsets from 600 random starts.
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
import star_sphere as ss  # noqa: E402

MEEUS = ([213.9154, 19.1825, 201.2983, -11.1614], 32.7930)
ERFA = ("import erfa, math\nr = math.radians\ndef f(a, b, c, d, pa, dist):\n"
        "    return {'sep': math.degrees(float(erfa.seps(r(a), r(b), r(c), r(d)))), 'pa': math.degrees(float(erfa.pas(r(a), r(b), r(c), r(d)))) % 360.0}\n")
ASTROPY = ("import math\nfrom astropy.coordinates import angular_separation, position_angle, offset_by\nimport astropy.units as u\nr = math.radians\n"
           "def f(a, b, c, d, pa, dist):\n"
           "    lon, lat = offset_by(a * u.deg, b * u.deg, pa * u.deg, dist * u.deg)\n"
           "    return {'sep': math.degrees(float(angular_separation(r(a), r(b), r(c), r(d)))),\n"
           "            'pa': float(position_angle(r(a), r(b), r(c), r(d)).to_value(u.deg)) % 360.0,\n"
           "            'off': [float(lon.to_value(u.deg)) % 360.0, float(lat.to_value(u.deg))]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"erfa": (sys.executable, ERFA), "astropy": (str(ROOT / ".venvs" / "astropy" / "Scripts" / "python.exe"), ASTROPY)}


def circ(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def main():
    rnd = random.Random(20261006)
    pt = lambda: (rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-1, 1))))
    cases = [MEEUS[0] + [10.0, 1.0]]
    for k in range(600):
        lon, lat = pt()
        if k < 300:
            lon2, lat2 = pt()
        else:
            d, pa = 10 ** rnd.uniform(-6, 0), rnd.uniform(0, 360)
            lon2, lat2 = ss.offset(lon, max(-89.0, min(89.0, lat)), pa, d if k < 450 else 180.0 - d)
            lat = max(-89.0, min(89.0, lat))
        cases.append([lon, lat, lon2, lat2, rnd.uniform(0, 360), rnd.uniform(0, 180)])
    out = {"pairs": len(cases) - 1, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = isinstance(res[0], dict) and abs(res[0]["sep"] - MEEUS[1]) < 5e-5
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            sep = pa_m = off = 0.0
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                s = ss.separation_deg(*c[:4])
                sep = max(sep, abs(s - x["sep"]))
                # a position angle is ill-conditioned near coincidence and near the antipode: compare it as a displacement
                pa_m = max(pa_m, math.radians(circ(ss.position_angle_deg(*c[:4]), x["pa"])) * math.sin(math.radians(s)))
                if "off" in x:
                    lon2, lat2 = ss.offset(c[0], c[1], c[4], c[5])
                    off = max(off, ss.separation_deg(lon2, lat2, x["off"][0], max(-90.0, min(90.0, x["off"][1]))))
            entry.update(compared=n, max_separation_diff_deg=sep, max_position_angle_displacement_rad=pa_m,
                         max_offset_point_diff_deg=off if "off" in res[0] else None)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "max" in k}, flush=True)
    L = out["lineages"]
    mine = abs(ss.separation_deg(*MEEUS[0]) - MEEUS[1])
    sep = max(v.get("max_separation_diff_deg", 1.0) for v in L.values())
    pa = max(v.get("max_position_angle_displacement_rad", 1.0) for v in L.values())
    off = L["astropy"].get("max_offset_point_diff_deg")
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and sep < 1e-10 and pa < 1e-12 \
        and off is not None and off < 1e-10 and mine < 5e-5
    out["published"] = {"source": "Meeus Example 17.a", "star_sphere_abs_diff_deg": mine}
    out["summary"] = {"ok": ok, "lineages": ["ERFA seps / pas (C)", "astropy angular_separation / position_angle / offset_by",
                                             "Meeus, Astronomical Algorithms, Example 17.a"],
                      "claim": "star_sphere agrees with two independent implementations at every distance, nearby and nearly antipodal pairs included",
                      "crosscheck": f"600 pairs (300 random, 150 down to 1e-6 deg apart, 150 down to 1e-6 deg from the antipode): separation within "
                                    f"{sep:.1e} deg; position angle within {pa:.1e} rad of displacement; offset points within {off:.1e} deg of astropy; "
                                    f"Meeus example within {mine:.1e} deg (printed to 1e-4)",
                      "benchmark": "largest differences by lineage: " + "; ".join(
                          f"{n}: separation {v.get('max_separation_diff_deg', 0):.1e} deg, position angle {v.get('max_position_angle_displacement_rad', 0):.1e} rad"
                          for n, v in L.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_sphere_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published diff %.1e deg" % mine, "->", dest.name)


if __name__ == "__main__":
    main()
