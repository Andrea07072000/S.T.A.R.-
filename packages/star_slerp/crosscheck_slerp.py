"""Cross-check of star_slerp against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_slerp.py  ->  12_EVIDENCE/crosscheck_slerp_20261007.json

Lineages, each in its own interpreter; each returns the interpolated quaternion as (w, x, y, z):
  scipy  scipy.spatial.transform.Slerp between two Rotation objects (its quaternions are scalar-last);
  ahrs   ahrs.common.quaternion.slerp, a direct quaternion formula by another author. By documented design it switches
         to LINEAR interpolation when the dot product of the two quaternions exceeds 0.9995 (rotations below 3.6
         degrees): those pairs are compared apart and their deviation is recorded, not used as a criterion;
  spice  no quaternion interpolation at all: the rotation from q0 to q1 as a matrix (q2m, mxmt), its axis and angle
         (raxisa), the fraction t of that angle about the same axis (axisar), back to a quaternion (m2q).
A quaternion and its negative are the same attitude, so results are compared after aligning the sign; the measure is
the largest component difference.
Probe (by hand, from the definition of Shoemake 1985): half-way from the identity to a rotation of 90 degrees about
z is a rotation of 45 degrees about z: (cos 22.5 deg, 0, 0, sin 22.5 deg) = (0.923879532511287, 0, 0, 0.382683432365090).
Corpus (seed 20261007): 600 pairs of unit quaternions: random attitudes, rotations of 1e-9 to 1e-3 rad between the
two, rotations within 0.1 degree of 180 degrees, and the second quaternion given in the opposite hemisphere; t
random in [0, 1] with 0, 0.5 and 1 included. Rotations of exactly 180 degrees, where the two arcs are equally short
and the libraries may legitimately choose either, are not in the corpus.
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
import star_slerp as ss  # noqa: E402

SCIPY = """import numpy as np
from scipy.spatial.transform import Rotation as R, Slerp
def f(q0, q1, t):
    s = Slerp([0.0, 1.0], R.from_quat([[q0[1], q0[2], q0[3], q0[0]], [q1[1], q1[2], q1[3], q1[0]]]))
    x, y, z, w = s([t]).as_quat()[0]
    return [float(w), float(x), float(y), float(z)]
"""
AHRS = """import numpy as np
from ahrs.common.quaternion import slerp
def f(q0, q1, t):
    return [float(v) for v in slerp(np.array(q0), np.array(q1), [t])[0]]
"""
SPICE = """import spiceypy as sp
def f(q0, q1, t):
    m0, m1 = sp.q2m(q0), sp.q2m(q1)
    axis, angle = sp.raxisa(sp.mxmt(m1, m0))
    return [float(v) for v in sp.m2q(sp.mxm(sp.axisar(axis, t * angle), m0))]
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
PROBE = [[1.0, 0.0, 0.0, 0.0], [math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4)], 0.5]
EXPECTED = [0.923879532511287, 0.0, 0.0, 0.382683432365090]
LIMIT = {"scipy": 1e-13, "ahrs": 1e-13, "spice": 1e-11}


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"scipy": (venv("scipy"), SCIPY), "ahrs": (venv("ahrs"), AHRS), "spice": (venv("spiceypy"), SPICE)}


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v]


def times(a, b):
    """Hamilton product of two quaternions (w, x, y, z)."""
    return [a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3], a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
            a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1], a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]]


def gap(a, b):
    return min(max(abs(x - y) for x, y in zip(a, b)), max(abs(x + y) for x, y in zip(a, b)))


def main():
    rnd = random.Random(20261007)
    cases = [PROBE]
    for k in range(600):
        q0 = unit([rnd.gauss(0, 1) for _ in range(4)])
        axis = unit([rnd.gauss(0, 1) for _ in range(3)])
        kind = k % 4
        if kind == 0:
            angle = rnd.uniform(0.01, math.pi - 0.01)
        elif kind == 1:
            angle = 10 ** rnd.uniform(-9, -3)
        elif kind == 2:
            angle = math.pi - rnd.uniform(1e-6, 1.7e-3)       # within 0.1 degree of 180
        else:
            angle = rnd.uniform(0.01, 3.0)
        step = [math.cos(angle / 2)] + [math.sin(angle / 2) * c for c in axis]
        q1 = unit(times(step, q0))
        if kind == 3:
            q1 = [-c for c in q1]                           # the same attitude, given in the other hemisphere
        cases.append([q0, q1, (0.0, 0.5, 1.0)[k % 30] if k % 30 < 3 else rnd.random()])
    total = len(cases) - 1
    ours = [list(ss.slerp(*c)) for c in cases]
    out = {"cases": total, "seed": 20261007, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = not isinstance(res[0], str) and gap(res[0], EXPECTED) < 1e-14
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst, example, n, small, small_n = 0.0, None, 0, 0.0, 0
            for c, got, ref in zip(cases[1:], ours[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                d = gap(got, ref)
                if name == "ahrs" and abs(sum(a * b for a, b in zip(c[0], c[1]))) > 0.9995:
                    small, small_n = max(small, d), small_n + 1   # its documented threshold: linear interpolation below 3.6 degrees
                    continue
                if d > worst:
                    worst, example = d, [c, got, ref]
            entry.update(compared=n, max_component_diff=worst, limit=LIMIT[name], example=example)
            if name == "ahrs":
                entry["below_its_linear_threshold"] = {"pairs": small_n, "max_component_diff": small}
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[:1]}", "errors", len(errors), errors[:1], entry.get("max_component_diff"), flush=True)
    L = out["lineages"]
    mine_ok = gap(ours[0], EXPECTED) < 1e-15 and all(abs(math.sqrt(sum(c * c for c in q)) - 1.0) < 4e-16 for q in ours)
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v["max_component_diff"] <= LIMIT[k] for k, v in L.items())
    out["published"] = {"source": "by hand from the definition of spherical linear interpolation (Shoemake 1985): half-way from the identity to 90 degrees about z is 45 degrees about z, "
                                  "(0.923879532511287, 0, 0, 0.382683432365090)", "star_slerp_observed": ours[0], "star_slerp_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["scipy.spatial.transform.Slerp", "ahrs.common.quaternion.slerp", "NAIF SPICE through rotation matrices, axis and angle"],
                      "claim": "star_slerp interpolates two attitudes along the shorter rotation at constant rate and returns a unit quaternion",
                      "crosscheck": f"{total} pairs of attitudes (rotations from 1e-9 rad to within 0.1 degree of 180 degrees, either hemisphere): the largest component difference is "
                                    f"{L['scipy'].get('max_component_diff', 0):.1e} from SciPy, {L['ahrs'].get('max_component_diff', 0):.1e} from ahrs (above its linear-interpolation threshold; {(L['ahrs'].get('below_its_linear_threshold') or {}).get('max_component_diff', 0):.1e} below it) and {L['spice'].get('max_component_diff', 0):.1e} from the "
                                    f"SPICE matrix route (sign aligned)",
                      "benchmark": f"largest component difference from SciPy Slerp: {L['scipy'].get('max_component_diff', 0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_slerp_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, ours[0], "->", dest.name)


if __name__ == "__main__":
    main()
