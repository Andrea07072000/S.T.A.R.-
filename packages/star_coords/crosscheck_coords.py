"""Cross-check of star_coords against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_coords.py  ->  12_EVIDENCE/crosscheck_coords_20261006.json

Lineages, each in its own interpreter:
  erfa     ERFA s2p and p2s (C): spherical, both directions;
  spice    SPICE latrec, reclat, cylrec, reccyl (C): spherical and cylindrical, both directions;
  astropy  astropy.coordinates.spherical_to_cartesian, cartesian_to_spherical and CylindricalRepresentation (NumPy):
           spherical and cylindrical, both directions.
Probe (by hand, exact trigonometry; the definition is in the Explanatory Supplement to the Astronomical Almanac,
"rectangular coordinates"): longitude 60 deg, latitude 0, radius 2 is (1, sqrt(3), 0). A lineage further than 1e-12
from that is excluded.
Corpus (seed 20261006): 600 cases: directions uniform on the sphere (100 within 1e-9 ... 1e-3 deg of the z axis), radii
and components from 1e-3 to 1e9.
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
import star_coords as sc  # noqa: E402

PROBE = ([60.0, 0.0, 2.0, 1.0, math.sqrt(3.0), 0.0], (1.0, math.sqrt(3.0), 0.0))
ERFA = ("import erfa, math\nD, R = math.degrees, math.radians\ndef f(lon, lat, r, x, y, z):\n"
        "    t, p, d = erfa.p2s([x, y, z])\n"
        "    return {'xyz': [float(v) for v in erfa.s2p(R(lon), R(lat), r)], 'sph': [D(float(t)) % 360.0, D(float(p)), float(d)]}\n")
SPICE = ("import spiceypy as sp, math\nD, R = math.degrees, math.radians\ndef f(lon, lat, r, x, y, z):\n"
         "    d, t, p = sp.reclat([x, y, z]); rho, cl, cz = sp.reccyl([x, y, z])\n"
         "    return {'xyz': [float(v) for v in sp.latrec(r, R(lon), R(lat))], 'sph': [D(t) % 360.0, D(p), d],\n"
         "            'cxyz': [float(v) for v in sp.cylrec(r, R(lon), z)], 'cyl': [rho, D(cl) % 360.0, cz]}\n")
ASTROPY = ("import math\nfrom astropy.coordinates import spherical_to_cartesian, cartesian_to_spherical, CylindricalRepresentation, CartesianRepresentation\n"
           "import astropy.units as u\ndef f(lon, lat, r, x, y, z):\n"
           "    d, p, t = cartesian_to_spherical(x, y, z)\n"
           "    c = CylindricalRepresentation(r * u.m, lon * u.deg, z * u.m).to_cartesian()\n"
           "    k = CartesianRepresentation(x * u.m, y * u.m, z * u.m).represent_as(CylindricalRepresentation)\n"
           "    return {'xyz': [float(v) for v in spherical_to_cartesian(r, math.radians(lat), math.radians(lon))],\n"
           "            'sph': [float(t.to_value(u.deg)) % 360.0, float(p.to_value(u.deg)), float(d)],\n"
           "            'cxyz': [float(c.x.value), float(c.y.value), float(c.z.value)], 'cyl': [float(k.rho.value), float(k.phi.to_value(u.deg)) % 360.0, float(k.z.value)]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"erfa": (sys.executable, ERFA), "spice": (venv("spiceypy"), SPICE), "astropy": (venv("astropy"), ASTROPY)}


def rel(a, b):
    """Largest component difference of two vectors, relative to the length of the second."""
    n = math.hypot(*b) or 1.0
    return max(abs(p - q) for p, q in zip(a, b)) / n


def ang(mine, theirs):
    """Displacement in degrees between two (lon, lat) directions: the longitude difference weighs cos(lat)."""
    dl = abs((mine[0] - theirs[0] + 180.0) % 360.0 - 180.0) * math.cos(math.radians(theirs[1]))
    return max(dl, abs(mine[1] - theirs[1]))


def main():
    rnd = random.Random(20261006)
    cases = [PROBE[0]]
    for k in range(600):
        r = 10 ** rnd.uniform(-3, 9)
        lon = rnd.uniform(0, 360)
        lat = math.degrees(math.asin(rnd.uniform(-1, 1))) if k < 500 else rnd.choice((-1, 1)) * (90.0 - 10 ** rnd.uniform(-9, -3))
        x, y, z = sc.spherical_to_xyz(rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-1, 1))) if k < 500 else lat, 10 ** rnd.uniform(-3, 9))
        cases.append([lon, lat, r, x, y, z])
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
        valid = isinstance(res[0], dict) and len(res[0].get("xyz", [])) == 3 and max(abs(a - b) for a, b in zip(res[0]["xyz"], PROBE[1])) < 1e-12
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"to_xyz_rel": 0.0, "to_sph_deg": 0.0, "to_sph_r_rel": 0.0, "cyl_to_xyz_rel": None, "to_cyl_rel": None, "to_cyl_deg": None}
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                m["to_xyz_rel"] = max(m["to_xyz_rel"], rel(sc.spherical_to_xyz(c[0], c[1], c[2]), x["xyz"]))
                lon, lat, d = sc.xyz_to_spherical(c[3], c[4], c[5])
                m["to_sph_deg"] = max(m["to_sph_deg"], ang((lon, lat), x["sph"]))
                m["to_sph_r_rel"] = max(m["to_sph_r_rel"], abs(d - x["sph"][2]) / x["sph"][2])
                if "cyl" in x:
                    m["cyl_to_xyz_rel"] = max(m["cyl_to_xyz_rel"] or 0.0, rel(sc.cylindrical_to_xyz(c[2], c[0], c[5]), x["cxyz"]))
                    rho, cl, cz = sc.xyz_to_cylindrical(c[3], c[4], c[5])
                    m["to_cyl_rel"] = max(m["to_cyl_rel"] or 0.0, abs(rho - x["cyl"][0]) / math.hypot(c[3], c[4], c[5]), abs(cz - x["cyl"][2]) / math.hypot(c[3], c[4], c[5]))
                    # the longitude of a point at distance rho from the axis: weigh the difference by rho / length
                    m["to_cyl_deg"] = max(m["to_cyl_deg"] or 0.0, abs((cl - x["cyl"][1] + 180.0) % 360.0 - 180.0) * rho / math.hypot(c[3], c[4], c[5]))
            entry.update(compared=n, **{"max_" + k: v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k[4:]: v for k, v in entry.items() if k.startswith("max_") and v is not None}, flush=True)
    L = out["lineages"]
    worst = max(v for e in L.values() for k, v in e.items() if k.startswith("max_") and v is not None) if all(e["probe_valid"] for e in L.values()) else 1.0
    cyl = [n for n, e in L.items() if e.get("max_to_cyl_rel") is not None]
    mine = max(abs(a - b) for a, b in zip(sc.spherical_to_xyz(*PROBE[0][:3]), PROBE[1]))
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and worst < 1e-12 and cyl == ["spice", "astropy"] and mine < 1e-15
    out["by_hand"] = {"case": "lon 60 deg, lat 0, r 2 -> (1, sqrt(3), 0)", "star_coords_abs_diff": mine}
    out["summary"] = {"ok": ok, "lineages": ["ERFA s2p / p2s (C)", "SPICE latrec / reclat / cylrec / reccyl (C)",
                                             "astropy spherical_to_cartesian / cartesian_to_spherical / CylindricalRepresentation"],
                      "claim": "star_coords converts spherical and cylindrical coordinates to rectangular and back as three independent libraries do, close to the axis included",
                      "crosscheck": f"600 cases (100 directions down to 1e-9 deg from the z axis, lengths from 1e-3 to 1e9), both directions: components and lengths within "
                                    f"{worst:.1e} relative, angles within the same in degrees of displacement; spherical: ERFA, SPICE, astropy; cylindrical: SPICE, astropy",
                      "benchmark": "largest difference by lineage: " + "; ".join(
                          f"{n}: {max(v for k, v in e.items() if k.startswith('max_') and v is not None):.1e}" for n, e in L.items() if e['probe_valid'])}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_coords_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "worst %.1e" % worst, "->", dest.name)


if __name__ == "__main__":
    main()
