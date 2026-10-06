"""Cross-check of star_iod against known orbits and an independent implementation (S.T.A.R., 2026-10-06).

  python crosscheck_iod.py  ->  12_EVIDENCE/crosscheck_iod_20261006.json

Lineages, each in its own interpreter:
  known_orbit  NAIF CSPICE conics: three positions of a KNOWN Keplerian orbit and its true velocity at the middle one
               (truth without any orbit-determination algorithm);
  orekit       Orekit IodGibbs on the same three positions (an independent implementation of Gibbs' method).
Probe for Orekit: Vallado Example 7-3 (v2 = 0, 5.531148, -5.191806 km/s) within 1e-5 km/s, or excluded.
Corpus (seed 20261006): 240 orbits (perigee radius 6700-30000 km, eccentricity 0-0.7, any orientation), each sampled
at one of six spacings between consecutive positions: 0.02, 0.1, 0.5, 2, 10 and 40 degrees of mean anomaly.
Measured, per spacing: relative velocity error of gibbs and of herrick_gibbs against the true velocity - the two
methods have opposite domains, and the table says where each one is usable - and gibbs against Orekit.
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
import star_iod as si  # noqa: E402

MU = si.MU_EARTH
SPACINGS_DEG = (0.02, 0.1, 0.5, 2.0, 10.0, 40.0)
VALLADO = [[0.0, 0.0, 6378.137], [0.0, -4464.696, -5102.509], [0.0, 5740.323, 3189.068]]
VALLADO_V2 = (0.0, 5.531148, -5.191806)
TRUTH = f"MU = {MU!r}\n" + '''
import math
import spiceypy as sp
def f(rp, e, inc, raan, argp, m0, dt):
    elts = [rp, e, inc, raan, argp, m0, 0.0, MU]
    s = [sp.conics(elts, t) for t in (-dt, 0.0, dt)]
    return {"r": [[float(x) for x in st[:3]] for st in s], "v2": [float(x) for x in s[1][3:]], "dt": dt}
'''
OREKIT = f"MU = {MU!r}\n" + '''
import orekit_jpype
orekit_jpype.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data
setup_orekit_data("/root/orekit-data.zip", from_pip_library=False)
from org.orekit.estimation.iod import IodGibbs
from org.orekit.frames import FramesFactory
from org.orekit.time import AbsoluteDate
from org.hipparchus.geometry.euclidean.threed import Vector3D
def f(r, dt):
    fr = FramesFactory.getEME2000()
    t0 = AbsoluteDate.J2000_EPOCH
    v = [Vector3D(float(a[0]) * 1e3, float(a[1]) * 1e3, float(a[2]) * 1e3) for a in r]
    o = IodGibbs(MU * 1e9).estimate(fr, v[0], t0.shiftedBy(-dt), v[1], t0, v[2], t0.shiftedBy(dt))
    vel = o.getPVCoordinates().getVelocity()
    return [vel.getX() / 1e3, vel.getY() / 1e3, vel.getZ() / 1e3]
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:80])\nprint('@@' + json.dumps(out))\n")


def run(cmd, driver, cases, name):
    r = subprocess.run(cmd + [driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=1800)
    line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
    if r.returncode or not line:
        raise SystemExit(f"{name}: driver failed\n{r.stderr[-1000:]}")
    res = json.loads(line[0][2:])
    if not isinstance(res, list) or len(res) != len(cases):
        raise SystemExit(f"{name}: wrong number of answers")
    return res


def rel(a, b):
    return math.hypot(*[x - y for x, y in zip(a, b)]) / math.hypot(*b)


def main():
    rnd = random.Random(20261006)
    orbits = []
    for k in range(240):
        rp, e = rnd.uniform(6700.0, 30000.0), rnd.uniform(0.0, 0.7)
        a = rp / (1 - e)
        n = math.sqrt(MU / a ** 3)
        dm = math.radians(SPACINGS_DEG[k % 6])
        orbits.append([rp, e, rnd.uniform(0.05, 3.0), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), dm / n])
    truth = run([sys.executable, "-W", "ignore", "-c"], TRUTH, orbits, "known_orbit")
    if any(isinstance(t, str) for t in truth):
        raise SystemExit(f"known_orbit: errors {[t for t in truth if isinstance(t, str)][:2]}")
    ok_cases = [[VALLADO, 600.0]] + [[t["r"], t["dt"]] for t in truth]
    orekit = run(["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-W", "ignore", "-c"], OREKIT, ok_cases, "orekit")
    probe = orekit[0]
    valid = isinstance(probe, list) and len(probe) == 3 and max(abs(a - b) for a, b in zip(probe, VALLADO_V2)) < 1e-5
    out = {"orbits": len(orbits), "seed": 20261006, "spacings_deg_of_mean_anomaly": list(SPACINGS_DEG),
           "published": {"source": "Vallado Example 7-3", "star_iod_gibbs_abs_diff_kms": max(abs(a - b) for a, b in zip(si.gibbs(*VALLADO), VALLADO_V2))},
           "orekit_probe_valid": valid, "orekit_errors": sum(isinstance(x, str) for x in orekit), "by_spacing": {}}
    # the truth generator is checked too: its velocity must satisfy the vis-viva equation of the orbit it was asked for
    vis = max(abs(math.hypot(*t["v2"]) ** 2 / (MU * (2 / math.hypot(*t["r"][1]) - (1 - o[1]) / o[0])) - 1) for t, o in zip(truth, orbits))
    out["lineages"] = {"known_orbit": {"probe_valid": vis < 1e-12, "errors": 0, "max_vis_viva_residual": vis},
                       "orekit": {"probe_valid": valid, "errors": out["orekit_errors"]}}
    for i, sp_deg in enumerate(SPACINGS_DEG):
        g = h = o = 0.0
        refused = 0
        for k in range(i, len(orbits), 6):
            t = truth[k]
            if len(t["r"]) != 3 or len(t["v2"]) != 3:
                raise SystemExit("known_orbit: malformed answer")
            try:
                mine = si.gibbs(*t["r"])
                g = max(g, rel(mine, t["v2"]))
                if valid and isinstance(orekit[k + 1], list):
                    o = max(o, rel(mine, orekit[k + 1]))
            except ValueError:
                refused += 1
            h = max(h, rel(si.herrick_gibbs(*t["r"], -t["dt"], 0.0, t["dt"]), t["v2"]))
        out["by_spacing"][str(sp_deg)] = {"gibbs_max_rel_error_vs_truth": g, "herrick_gibbs_max_rel_error_vs_truth": h,
                                          "gibbs_max_rel_diff_vs_orekit": o if valid else None, "gibbs_refusals": refused}
        print(sp_deg, "deg: gibbs %.1e | herrick-gibbs %.1e | gibbs vs orekit %.1e | refused %d" % (g, h, o, refused), flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_iod_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("orekit probe", "valid" if valid else f"EXCLUDED {probe}", "errors", out["orekit_errors"], "| published diff %.1e km/s ->" % out["published"]["star_iod_gibbs_abs_diff_kms"], dest.name)


if __name__ == "__main__":
    main()
