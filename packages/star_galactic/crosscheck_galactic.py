"""Cross-check of star_galactic against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_galactic.py  ->  12_EVIDENCE/crosscheck_galactic_20261006.json

Lineages, each in its own interpreter:
  erfa     ERFA icrs2g and g2icrs (C, Hipparcos matrix): system "icrs", both directions;
  astropy  astropy FK4NoETerms(B1950) <-> Galactic (Python, IAU 1958 matrix): system "b1950", both directions;
  spice    SPICE pxform FK4 <-> GALACTIC (C, System II): system "b1950", both directions. SPICE's frame named
           B1950 is rotated by 0.525 arcsec from FK4 and is NOT the one the galactic system is defined on: the probe
           excluded it (1.4e-4 deg from the published example) before this driver was corrected.
Probes (published): erfa on the Hipparcos definition (the celestial pole has l = 122.93192, b = 27.12825); astropy
and spice on Meeus, Astronomical Algorithms, Example 13.b (B1950 267.248917, -14.718944 -> l 12.9593, b 6.0463).
A lineage further than 8e-5 deg from its probe is excluded (the example is printed to 1e-4 deg per coordinate).
Corpus (seed 20261006): 600 directions, 500 uniform on the sphere and 100 within 1e-6 ... 1 deg of a galactic pole.
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
import star_galactic as sg  # noqa: E402

PROBES = {"icrs": ([0.0, 90.0], (122.93192, 27.12825)), "b1950": ([267.248917, -14.718944], (12.9593, 6.0463))}
ERFA = ("import erfa, math\nD, R = math.degrees, math.radians\ndef f(a, d, l, b):\n"
        "    x, y = erfa.icrs2g(R(a), R(d)); p, q = erfa.g2icrs(R(l), R(b))\n"
        "    return {'gal': [D(float(x)) % 360.0, D(float(y))], 'eq': [D(float(p)) % 360.0, D(float(q))]}\n")
ASTROPY = ("from astropy.coordinates import SkyCoord, FK4NoETerms, Galactic\nimport astropy.units as u\nF = FK4NoETerms(equinox='B1950')\n"
           "def f(a, d, l, b):\n"
           "    g = SkyCoord(a * u.deg, d * u.deg, frame=F).transform_to(Galactic())\n"
           "    e = SkyCoord(l * u.deg, b * u.deg, frame=Galactic()).transform_to(F)\n"
           "    return {'gal': [float(g.l.deg) % 360.0, float(g.b.deg)], 'eq': [float(e.ra.deg) % 360.0, float(e.dec.deg)]}\n")
SPICE = ("import spiceypy as sp, math\nD, R = math.degrees, math.radians\nM, N = sp.pxform('FK4', 'GALACTIC', 0.0), sp.pxform('GALACTIC', 'FK4', 0.0)\n"
         "def f(a, d, l, b):\n"
         "    _, x, y = sp.recrad(sp.mxv(M, sp.radrec(1.0, R(a), R(d)))); _, p, q = sp.recrad(sp.mxv(N, sp.radrec(1.0, R(l), R(b))))\n"
         "    return {'gal': [D(x) % 360.0, D(y)], 'eq': [D(p) % 360.0, D(q)]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"erfa": (sys.executable, ERFA, "icrs"), "astropy": (venv("astropy"), ASTROPY, "b1950"), "spice": (venv("spiceypy"), SPICE, "b1950")}


def sep(p, q):
    """Angle in degrees between two (longitude, latitude) directions, arc-tangent form."""
    l1, b1, l2, b2 = map(math.radians, (p[0], p[1], q[0], q[1]))
    sd, cd = math.sin(l2 - l1), math.cos(l2 - l1)
    return math.degrees(math.atan2(math.hypot(math.cos(b2) * sd, math.cos(b1) * math.sin(b2) - math.sin(b1) * math.cos(b2) * cd),
                                   math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * cd))


def main():
    rnd = random.Random(20261006)
    body = []
    for k in range(600):
        if k < 500:
            p = [rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-1, 1)))]
        else:                                               # close to a galactic pole of either system: there the longitude is ill-conditioned
            p = list(sg.galactic_to_equatorial(rnd.uniform(0, 360), rnd.choice((-1, 1)) * (90.0 - 10 ** rnd.uniform(-6, 0)), rnd.choice(("icrs", "b1950"))))
        body.append(p + [rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-1, 1)))])
    out = {"cases": len(body), "seed": 20261006, "lineages": {}}
    for name, (py, driver, system) in DRIVERS.items():
        cases = [PROBES[system][0] + [10.0, 10.0]] + body
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = isinstance(res[0], dict) and len(res[0].get("gal", [])) == 2 and sep(res[0]["gal"], PROBES[system][1]) < 8e-5
        entry = {"system": system, "probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            fwd = inv = 0.0
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                fwd = max(fwd, sep(sg.equatorial_to_galactic(c[0], c[1], system), x["gal"]))
                inv = max(inv, sep(sg.galactic_to_equatorial(c[2], c[3], system), x["eq"]))
            entry.update(compared=n, max_to_galactic_diff_deg=fwd, max_to_equatorial_diff_deg=inv)
        out["lineages"][name] = entry
        print(name, system, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "max" in k}, flush=True)
    L = out["lineages"]
    mine = {s: sep(sg.equatorial_to_galactic(*PROBES[s][0], s), PROBES[s][1]) for s in PROBES}
    worst = max(max(v.get("max_to_galactic_diff_deg", 1.0), v.get("max_to_equatorial_diff_deg", 1.0)) for v in L.values())
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and worst < 1e-10 and max(mine.values()) < 8e-5
    out["published"] = {"icrs": "ESA 1997, The Hipparcos and Tycho Catalogues, vol. 1, 1.5.3", "b1950": "Meeus Example 13.b", "star_galactic_abs_diff_deg": mine}
    out["summary"] = {"ok": ok, "lineages": ["ERFA icrs2g / g2icrs (C)", "astropy FK4NoETerms <-> Galactic", "SPICE pxform FK4 <-> GALACTIC",
                                             "Meeus, Astronomical Algorithms, Example 13.b"],
                      "claim": "star_galactic reproduces the Hipparcos (ICRS) and IAU 1958 (B1950) galactic frames of three independent libraries, in both directions",
                      "crosscheck": f"600 directions (100 down to 1e-6 deg from a galactic pole), both directions: within {worst:.1e} deg; "
                                    f"Meeus Example 13.b within {mine['b1950']:.1e} deg (printed to 1e-4)",
                      "benchmark": "largest difference by lineage: " + "; ".join(
                          f"{n} ({v['system']}): {max(v.get('max_to_galactic_diff_deg', 0), v.get('max_to_equatorial_diff_deg', 0)):.1e} deg" for n, v in L.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_galactic_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", mine, "->", dest.name)


if __name__ == "__main__":
    main()
