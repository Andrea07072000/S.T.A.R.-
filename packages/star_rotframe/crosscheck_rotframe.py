"""Cross-check of star_rotframe against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_rotframe.py  ->  12_EVIDENCE/crosscheck_rotframe_20261007.json

Lineages, each in its own interpreter; each returns the six numbers of the state in the rotating frame and the six of
the state brought back to the inertial frame:
  spice    NAIF SPICE: the rotation matrix of a frame turned about z (rotate) and the 6x6 state transformation built
           from that rotation and the angular velocity vector (rav2xf), and its inverse (invstm);
  scipy    scipy.spatial.transform.Rotation about z applied to position and velocity, with the transport term
           written as a cross product with (0, 0, rate);
  astropy  astropy.coordinates.matrix_utilities.rotation_matrix about z, the same transport term.
Probe (by hand): a point fixed on the equator of a body of radius 6378.137 km turning at the WGS-84 rate
7.292115e-5 rad/s has, when its meridian is 90 degrees from the inertial x axis, the inertial state r = (0, 6378.137, 0)
km, v = (-0.46510108..., 0, 0) km/s, and in the rotating frame r' = (6378.137, 0, 0), v' = (0, 0, 0).
Corpus (seed 20261007): 600 states: low and geostationary orbits in km and km/s, states in metres, random states of
mixed magnitude; angles within one turn, within 1000 rad and up to 1e8 rad; the Earth's rate and rates up to 0.1 rad/s
of either sign. Differences are relative to |r| for positions and to |v| + |rate| |r| for velocities.
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
import star_rotframe as sf  # noqa: E402

SPICE = """import numpy as np
import spiceypy as sp
def f(r, v, angle, rate):
    xf = np.array(sp.rav2xf(sp.rotate(angle, 3), [0.0, 0.0, rate]))
    there = xf @ np.array(r + v)
    back = np.array(sp.invstm(xf)) @ there
    return [float(c) for c in there] + [float(c) for c in back]
"""
SCIPY = """import numpy as np
from scipy.spatial.transform import Rotation as R
def f(r, v, angle, rate):
    turn = R.from_euler('z', -angle)                       # an active turn by -angle gives the components in the turned frame
    w = np.array([0.0, 0.0, rate])
    rr = turn.apply(r)
    vv = turn.apply(v) - np.cross(w, rr)
    back_r = turn.inv().apply(rr)
    back_v = turn.inv().apply(vv + np.cross(w, rr))
    return [float(c) for c in rr] + [float(c) for c in vv] + [float(c) for c in back_r] + [float(c) for c in back_v]
"""
ASTROPY = """import numpy as np
import astropy.units as u
from astropy.coordinates.matrix_utilities import rotation_matrix
def f(r, v, angle, rate):
    m = rotation_matrix(angle * u.rad, 'z')
    w = np.array([0.0, 0.0, rate])
    rr = m @ np.array(r)
    vv = m @ np.array(v) - np.cross(w, rr)
    back_r = m.T @ rr
    back_v = m.T @ (vv + np.cross(w, rr))
    return [float(c) for c in rr] + [float(c) for c in vv] + [float(c) for c in back_r] + [float(c) for c in back_v]
"""
RUNNER = """
import json, sys
out = []
for c in json.load(sys.stdin):
    try:
        out.append(f(*c))
    except Exception as e:
        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])
print('@@' + json.dumps(out))
"""
RATE = 7.292115e-5
PROBE = [[0.0, 6378.137, 0.0], [-RATE * 6378.137, 0.0, 0.0], math.pi / 2, RATE]
LIMIT = 1e-13


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"spice": (venv("spiceypy"), SPICE), "scipy": (venv("scipy"), SCIPY), "astropy": (venv("astropy"), ASTROPY)}


def mine(r, v, angle, rate):
    rr, vv = sf.to_rotating(r, v, angle, rate)
    br, bv = sf.to_inertial(rr, vv, angle, rate)
    return list(rr) + list(vv) + list(br) + list(bv)


def main():
    rnd = random.Random(20261007)
    cases = [PROBE]
    for k in range(600):
        kind = k % 4
        if kind == 0:
            radius, speed = rnd.uniform(6600.0, 8000.0), rnd.uniform(6.5, 7.9)
        elif kind == 1:
            radius, speed = 42164.0, 3.0747
        elif kind == 2:
            radius, speed = rnd.uniform(6.6e6, 4.3e7), rnd.uniform(3e3, 8e3)
        else:
            radius, speed = 10 ** rnd.uniform(-3, 9), 10 ** rnd.uniform(-6, 5)
        r = [rnd.gauss(0, 1) for _ in range(3)]
        v = [rnd.gauss(0, 1) for _ in range(3)]
        nr, nv = math.sqrt(sum(c * c for c in r)), math.sqrt(sum(c * c for c in v))
        r, v = [radius * c / nr for c in r], [speed * c / nv for c in v]
        angle = rnd.uniform(-math.pi, math.pi) if k % 3 == 0 else (rnd.uniform(-1000.0, 1000.0) if k % 3 == 1 else rnd.uniform(-1e8, 1e8))
        rate = RATE if k % 2 == 0 else rnd.uniform(-0.1, 0.1)
        cases.append([r, v, angle, rate])
    total = len(cases) - 1
    ours = [mine(*c) for c in cases]
    out = {"cases": total, "seed": 20261007, "lineages": {}}

    def scaled(c, a, b):
        r, v, _, rate = c
        nr = math.sqrt(sum(x * x for x in r))
        sv = math.sqrt(sum(x * x for x in v)) + abs(rate) * nr
        return max(max(abs(a[i] - b[i]) for i in (0, 1, 2, 6, 7, 8)) / nr, max(abs(a[i] - b[i]) for i in (3, 4, 5, 9, 10, 11)) / sv)

    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        p = res[0]
        valid = not isinstance(p, str) and abs(p[0] - 6378.137) < 1e-9 and max(abs(p[i]) for i in (1, 2, 3, 4, 5)) < 1e-9
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst, example, n = 0.0, None, 0
            for c, got, ref in zip(cases[1:], ours[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                d = scaled(c, got, ref)
                if d > worst:
                    worst, example = d, [c, got[:6], ref[:6]]
            entry.update(compared=n, max_scaled_diff=worst, example=example)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(p)[:140]}", "errors", len(errors), errors[:1], entry.get("max_scaled_diff"), flush=True)
    L = out["lineages"]
    def back(c, o):
        nr = math.sqrt(sum(x * x for x in c[0]))
        sv = math.sqrt(sum(x * x for x in c[1])) + abs(c[3]) * nr
        return max(max(abs(o[6 + i] - c[0][i]) for i in range(3)) / nr, max(abs(o[9 + i] - c[1][i]) for i in range(3)) / sv)

    round_trip = max(back(c, o) for c, o in zip(cases[1:], ours[1:]))
    mine_ok = abs(ours[0][0] - 6378.137) < 1e-12 and max(abs(ours[0][i]) for i in (1, 2, 3, 4, 5)) < 1e-12 and round_trip < 1e-14
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v["max_scaled_diff"] <= LIMIT for v in L.values())
    worst = max(v.get("max_scaled_diff") or 0.0 for v in L.values())
    out["round_trip_max_scaled_error"] = round_trip
    out["published"] = {"source": "by hand: a point fixed on the equator (radius 6378.137 km, WGS-84 rate 7.292115e-5 rad/s) is at rest in the rotating frame",
                        "star_rotframe_observed": ours[0][:6], "star_rotframe_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["NAIF SPICE rotate / rav2xf / invstm", "scipy.spatial.transform.Rotation", "astropy rotation_matrix"],
                      "claim": "star_rotframe converts position and velocity between an inertial frame and a frame rotating about z, transport term included, in both directions",
                      "crosscheck": f"{total} states (orbits in km and in metres, random magnitudes, angles up to 1e8 rad, rates up to 0.1 rad/s of either sign), there and back: agreement with SPICE, SciPy "
                                    f"and astropy within {worst:.1e} of |r| and of |v| + |rate| |r|; round trip of star_rotframe within {round_trip:.1e}",
                      "benchmark": f"largest scaled difference from SPICE: {L['spice'].get('max_scaled_diff', 0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_rotframe_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "round trip", round_trip, "->", dest.name)


if __name__ == "__main__":
    main()
