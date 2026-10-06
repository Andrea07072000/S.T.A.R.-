"""Cross-check of star_ecliptic against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_ecliptic.py  ->  12_EVIDENCE/crosscheck_ecliptic_20261006.json

Lineages, each in its own interpreter:
  erfa     ERFA obl80 and obl06 (C) for the obliquity; s2c, rx, rxp, c2s for the rotation at the obliquity of the case;
  astropy  astropy.coordinates.matrix_utilities.rotation_matrix: the rotation only
           (the conversion of the rotated vector back to angles is two atan2 written in the driver);
  spice    SPICE pxform J2000 -> ECLIPJ2000 (fixed obliquity 84381.448 arcsec), radrec, recrad: the rotation only,
           compared with star_ecliptic called at that obliquity;
  skyfield nutationlib.mean_obliquity (IAU 2006 polynomial, Python): the obliquity only. The IAU 1980 polynomial has
           one library lineage (ERFA) plus the published value of Meeus Example 22.a asserted in the tests.
Probe (published): Meeus, Astronomical Algorithms, Example 13.a: Pollux, alpha 116.328942, delta 28.026183, with
epsilon 23.4392911 deg has lambda 113.215630, beta 6.684170; a lineage further than 5e-6 deg from that is excluded.
Corpus (seed 20261006): 600 cases: dates over 1800-2200, directions uniform on the sphere (100 of them within
1e-6 ... 1 deg of the pole of the ecliptic), obliquity within 2000 arcsec of the J2000 value.
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
import star_ecliptic as se  # noqa: E402

MEEUS = ([2451545.0, 0.0, 116.328942, 28.026183, 23.4392911 * 3600.0], (113.215630, 6.684170))
ERFA = ("import erfa, math, numpy\ndef f(jd, fr, ra, dec, eps):\n"
        "    v = erfa.rxp(erfa.rx(math.radians(eps / 3600.0), numpy.eye(3)), erfa.s2c(math.radians(ra), math.radians(dec)))\n"
        "    lon, lat = erfa.c2s(v)\n"
        "    return {'o80': math.degrees(float(erfa.obl80(jd, fr))) * 3600.0, 'o06': math.degrees(float(erfa.obl06(jd, fr))) * 3600.0,\n"
        "            'ecl': [math.degrees(float(lon)) % 360.0, math.degrees(float(lat))]}\n")
ASTROPY = ("import math, numpy as np\nfrom astropy.coordinates.matrix_utilities import rotation_matrix\n"
           "\nimport astropy.units as u\n"
           "def f(jd, fr, ra, dec, eps):\n"
           "    a, d = math.radians(ra), math.radians(dec)\n"
           "    v = rotation_matrix(eps / 3600.0 * u.deg, 'x') @ np.array([math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)])\n"
           "    return {'ecl': [math.degrees(math.atan2(v[1], v[0])) % 360.0, math.degrees(math.atan2(v[2], math.hypot(v[0], v[1])))]}\n")
SPICE = ("import spiceypy as sp, math\nM = sp.pxform('J2000', 'ECLIPJ2000', 0.0)\ndef f(jd, fr, ra, dec, eps):\n"
         "    r, lon, lat = sp.recrad(sp.mxv(M, sp.radrec(1.0, math.radians(ra), math.radians(dec))))\n"
         "    return {'ecl2000': [math.degrees(lon) % 360.0, math.degrees(lat)]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def VENV(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


SKYFIELD = "from skyfield import nutationlib\ndef f(jd, fr, ra, dec, eps):\n    return {'o06': float(nutationlib.mean_obliquity(jd + fr))}\n"
DRIVERS = {"erfa": (sys.executable, ERFA), "astropy": (VENV("astropy"), ASTROPY), "spice": (VENV("spiceypy"), SPICE),
           "skyfield": (VENV("skyfield"), SKYFIELD)}
EPS_SPICE = 84381.448


def sep(p, q):
    """Angle in degrees between two (longitude, latitude) directions, arc-tangent form."""
    l1, b1, l2, b2 = map(math.radians, (p[0], p[1], q[0], q[1]))
    sd, cd = math.sin(l2 - l1), math.cos(l2 - l1)
    return math.degrees(math.atan2(math.hypot(math.cos(b2) * sd, math.cos(b1) * math.sin(b2) - math.sin(b1) * math.cos(b2) * cd),
                                   math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * cd))


def main():
    rnd = random.Random(20261006)
    cases = [MEEUS[0]]
    for k in range(600):
        eps = EPS_SPICE + rnd.uniform(-2000.0, 2000.0)
        if k < 500:
            ra, dec = rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-1, 1)))
        else:                                               # close to the pole of the ecliptic of that obliquity
            ra, dec = se.ecliptic_to_equatorial(rnd.uniform(0, 360), 90.0 - 10 ** rnd.uniform(-6, 0), eps)
        cases.append([float(rnd.randint(2378497, 2524593)) + 0.5, rnd.uniform(0, 1), ra, dec, eps])
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
        key = "ecl2000" if name == "spice" else "ecl"
        if name == "skyfield":                              # no rotation: probed on the published IAU 2006 constant at J2000.0
            valid = isinstance(res[0], dict) and abs(res[0].get("o06", 0.0) - 84381.406) < 1e-9
        else:
            valid = isinstance(res[0], dict) and len(res[0].get(key, [])) == 2 and sep(res[0][key], MEEUS[1]) < 5e-6
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            pt = o80 = o06 = 0.0
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                if key in x:
                    pt = max(pt, sep(se.equatorial_to_ecliptic(c[2], c[3], EPS_SPICE if name == "spice" else c[4]), x[key]))
                if "o80" in x:
                    o80 = max(o80, abs(se.mean_obliquity_arcsec(c[0], c[1], "iau1980") - x["o80"]))
                if "o06" in x:
                    o06 = max(o06, abs(se.mean_obliquity_arcsec(c[0], c[1], "iau2006") - x["o06"]))
            entry.update(compared=n, max_point_diff_deg=pt if key in res[0] else None, max_obliquity_1980_diff_arcsec=o80 if "o80" in res[0] else None,
                         max_obliquity_2006_diff_arcsec=o06 if "o06" in res[0] else None)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "max" in k}, flush=True)
    L = out["lineages"]
    mine = sep(se.equatorial_to_ecliptic(*MEEUS[0][2:]), MEEUS[1])
    have_pt = [n for n, v in L.items() if v.get("max_point_diff_deg") is not None]
    pt = max(L[n]["max_point_diff_deg"] for n in have_pt) if have_pt else 1.0
    ob = max(max(v.get("max_obliquity_1980_diff_arcsec") or 0.0, v.get("max_obliquity_2006_diff_arcsec") or 0.0) for v in L.values())
    have_ob = [n for n, v in L.items() if v.get("max_obliquity_2006_diff_arcsec") is not None]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and pt < 1e-11 and ob < 1e-8 \
        and have_ob == ["erfa", "skyfield"] and have_pt == ["erfa", "astropy", "spice"] \
        and L["erfa"].get("max_obliquity_1980_diff_arcsec") is not None and mine < 5e-6
    out["published"] = {"source": "Meeus Example 13.a", "star_ecliptic_abs_diff_deg": mine}
    out["summary"] = {"ok": ok, "lineages": ["ERFA obl80 / obl06 / rx (C)", "astropy matrix_utilities.rotation_matrix",
                                             "SPICE pxform J2000 -> ECLIPJ2000", "skyfield nutationlib.mean_obliquity (IAU 2006)", "Meeus, Astronomical Algorithms, Example 13.a"],
                      "claim": "star_ecliptic reproduces the IAU 1980 and IAU 2006 mean obliquity and the equatorial-to-ecliptic rotation of three independent libraries",
                      "crosscheck": f"600 cases (dates 1800-2200, 100 directions down to 1e-6 deg from the ecliptic pole): ecliptic direction within "
                                    f"{pt:.1e} deg of ERFA, astropy and SPICE; mean obliquity within {ob:.1e} arcsec (IAU 2006: ERFA and skyfield; IAU 1980: ERFA only); "
                                    f"Meeus example within {mine:.1e} deg (printed to 1e-6)",
                      "benchmark": "largest direction difference by lineage: " + "; ".join(f"{n}: {L[n]['max_point_diff_deg']:.1e} deg" for n in have_pt)}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_ecliptic_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published diff %.1e deg" % mine, "->", dest.name)


if __name__ == "__main__":
    main()
