"""Cross-check of star_horizon against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_horizon.py  ->  12_EVIDENCE/crosscheck_horizon_20261006.json

Lineages, each in its own interpreter:
  erfa   ERFA hd2ae, ae2hd, hd2pa (C): the three functions;
  spice  SPICE latrec, rotvec, reclat (C): the two conversions as a rotation about the East axis by -(90 deg +
         latitude) into a North-East-Down frame. The routines are SPICE's; their composition is written in the
         driver, so this lineage is independent in arithmetic but not in the choice of the rotation.
Probe (published): Meeus, Astronomical Algorithms, Example 13.b: Venus at hour angle 64.352133, declination
-6.719892, seen from latitude +38.921389, has azimuth 68.0337 deg from the South westward (248.0337 from North
through East) and altitude 15.1249 deg. A lineage further than 8e-5 deg from that is excluded.
Corpus (seed 20261006): 600 cases: 400 uniform, 100 within 1e-6 ... 1 deg of the zenith, 100 at latitudes within
1e-6 ... 1 deg of a geographic pole. The parallactic angle has one library lineage (ERFA).
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
import star_horizon as sh  # noqa: E402

MEEUS = ([64.352133, -6.719892, 38.921389, 100.0, 20.0], (248.0337, 15.1249))
ERFA = ("import erfa, math\nD, R = math.degrees, math.radians\ndef f(ha, dec, lat, az, el):\n"
        "    a, e = erfa.hd2ae(R(ha), R(dec), R(lat)); h, d = erfa.ae2hd(R(az), R(el), R(lat))\n"
        "    return {'azel': [D(float(a)) % 360.0, D(float(e))], 'hadec': [D(float(h)), D(float(d))], 'pa': D(float(erfa.hd2pa(R(ha), R(dec), R(lat))))}\n")
SPICE = ("import spiceypy as sp, math\nD, R = math.degrees, math.radians\ndef turn(lon, lat, phi):\n"
         "    _, a, b = sp.reclat(sp.rotvec(sp.latrec(1.0, -R(lon), R(lat)), -(math.pi / 2 + R(phi)), 2))\n"
         "    return D(a), -D(b)\n"
         "def f(ha, dec, lat, az, el):\n"
         "    a, e = turn(ha, dec, lat); h, d = turn(az, el, lat)\n"
         "    return {'azel': [a % 360.0, e], 'hadec': [h, d]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"erfa": (sys.executable, ERFA), "spice": (str(ROOT / ".venvs" / "spiceypy" / "Scripts" / "python.exe"), SPICE)}


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
        lat = rnd.uniform(-89.0, 89.0) if k < 500 else rnd.choice((-1, 1)) * (90.0 - 10 ** rnd.uniform(-6, 0))
        if 400 <= k < 500:                                  # close to the zenith: azimuth ill-conditioned, compared as a displacement
            ha, dec = sh.azel_to_hadec(rnd.uniform(0, 360), 90.0 - 10 ** rnd.uniform(-6, 0), lat)
        else:
            ha, dec = rnd.uniform(-180, 180), math.degrees(math.asin(rnd.uniform(-1, 1)))
        cases.append([ha, dec, lat, rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-1, 1)))])
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
        valid = isinstance(res[0], dict) and len(res[0].get("azel", [])) == 2 and sep(res[0]["azel"], MEEUS[1]) < 8e-5
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            fwd = inv = 0.0
            pa = None
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                fwd = max(fwd, sep(sh.hadec_to_azel(c[0], c[1], c[2]), x["azel"]))
                inv = max(inv, sep(sh.azel_to_hadec(c[3], c[4], c[2]), x["hadec"]))
                if "pa" in x:
                    # the parallactic angle is ill-conditioned at the zenith: weigh it by the zenith distance
                    zd = math.radians(90.0 - sh.hadec_to_azel(c[0], c[1], c[2])[1])
                    d = abs((sh.parallactic_angle_deg(c[0], c[1], c[2]) - x["pa"] + 180.0) % 360.0 - 180.0)
                    pa = max(pa or 0.0, d * math.sin(zd))
            entry.update(compared=n, max_azel_diff_deg=fwd, max_hadec_diff_deg=inv, max_parallactic_displacement_deg=pa)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "max" in k}, flush=True)
    L = out["lineages"]
    mine = sep(sh.hadec_to_azel(*MEEUS[0][:3]), MEEUS[1])
    worst = max(max(v.get("max_azel_diff_deg", 1.0), v.get("max_hadec_diff_deg", 1.0)) for v in L.values())
    pa = L["erfa"].get("max_parallactic_displacement_deg")
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and worst < 1e-10 \
        and pa is not None and pa < 1e-10 and mine < 8e-5
    out["published"] = {"source": "Meeus Example 13.b", "star_horizon_abs_diff_deg": mine}
    out["summary"] = {"ok": ok, "lineages": ["ERFA hd2ae / ae2hd / hd2pa (C)", "SPICE latrec / rotvec / reclat (rotation composed in the driver)",
                                             "Meeus, Astronomical Algorithms, Example 13.b"],
                      "claim": "star_horizon converts hour angle and declination to azimuth and elevation, and back, as ERFA and a SPICE rotation do",
                      "crosscheck": f"600 cases (100 down to 1e-6 deg from the zenith, 100 at latitudes down to 1e-6 deg from a pole), both directions: "
                                    f"within {worst:.1e} deg; parallactic angle within {pa or 0:.1e} deg of displacement of ERFA (one lineage); "
                                    f"Meeus Example 13.b within {mine:.1e} deg (printed to 1e-4)",
                      "benchmark": "largest difference by lineage: " + "; ".join(
                          f"{n}: {max(v.get('max_azel_diff_deg', 0), v.get('max_hadec_diff_deg', 0)):.1e} deg" for n, v in L.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_horizon_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published diff %.1e deg" % mine, "->", dest.name)


if __name__ == "__main__":
    main()
