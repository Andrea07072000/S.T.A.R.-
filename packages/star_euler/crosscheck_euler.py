"""Cross-check of star_euler against two independent libraries, for the twelve sequences (S.T.A.R., 2026-10-06).

  python crosscheck_euler.py  ->  12_EVIDENCE/crosscheck_euler_20261006.json

Lineages, each in its own interpreter:
  scipy  scipy.spatial.transform.Rotation.from_euler / as_euler with upper-case (intrinsic) sequences;
  spice  NAIF CSPICE eul2m / m2eul: SPICE composes FRAME rotations, so the driver transposes its matrix and reverses
         the order of the angles; the probe below is what proves the driver has the mapping right.
Probe (textbook): the sequence ZYX with yaw 90, pitch 0, roll 0 takes +X to +Y; with yaw 0, pitch 90 it takes +X to -Z
(nose up for a right-handed Z-down frame turns X towards -Z). A lineage that fails is excluded.
Corpus (seed 20261006): for each of the 12 sequences 60 random angle triples in the principal ranges, plus gimbal-lock
cases. Compared: the matrix; the angles recovered from the matrix (regular cases: each angle; gimbal lock: the
rebuilt matrix, because only a combination of the first and third angle is defined there).
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
import star_euler as se  # noqa: E402

SCIPY = '''
from scipy.spatial.transform import Rotation as R
def f(seq, a1, a2, a3):
    r = R.from_euler(seq, [a1, a2, a3], degrees=True)
    return {"dcm": [[float(x) for x in row] for row in r.as_matrix()], "angles": [float(x) for x in r.as_euler(seq, degrees=True)]}
'''
SPICE = '''
import math
import spiceypy as sp
def f(seq, a1, a2, a3):
    ax = ["XYZ".index(c) + 1 for c in seq]
    m = sp.eul2m(math.radians(a3), math.radians(a2), math.radians(a1), ax[2], ax[1], ax[0])
    b3, b2, b1 = sp.m2eul(m, ax[2], ax[1], ax[0])
    return {"dcm": [[float(m[j][i]) for j in range(3)] for i in range(3)], "angles": [math.degrees(b1), math.degrees(b2), math.degrees(b3)]}
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:80])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"scipy": ([str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), "-W", "ignore", "-c"], SCIPY),
           "spice": ([sys.executable, "-W", "ignore", "-c"], SPICE)}
PROBES = [["ZYX", 90.0, 0.0, 0.0], ["ZYX", 0.0, 90.0, 0.0]]
PROBE_X = [(0.0, 1.0, 0.0), (0.0, 0.0, -1.0)]             # image of +X = first column of the matrix


def ang(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def mdiff(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(3) for j in range(3))


def corpus():
    rnd = random.Random(20261006)
    regular, locked = [], []
    for seq in se.SEQUENCES:
        proper = seq[0] == seq[2]
        for _ in range(60):
            mid = rnd.uniform(1.0, 179.0) if proper else rnd.uniform(-89.0, 89.0)
            regular.append([seq, rnd.uniform(-179.9, 179.9), mid, rnd.uniform(-179.9, 179.9)])
        for mid in ((0.0, 180.0) if proper else (90.0, -90.0)):
            locked.append([seq, rnd.uniform(-179.0, 179.0), mid, rnd.uniform(-179.0, 179.0)])
    return regular, locked


def main():
    regular, locked = corpus()
    cases = PROBES + regular + locked
    out = {"sequences": len(se.SEQUENCES), "regular_cases": len(regular), "gimbal_lock_cases": len(locked), "seed": 20261006, "lineages": {}}
    for name, (cmd, driver) in DRIVERS.items():
        r = subprocess.run(cmd + [driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = all(isinstance(x, dict) and len(x["dcm"]) == 3 and max(abs(x["dcm"][i][0] - e[i]) for i in range(3)) < 1e-12
                    for x, e in zip(res[:2], PROBE_X))
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst_m, worst_a, worst_lock, per_seq = 0.0, 0.0, 0.0, {}
            for c, x in zip(cases[2:], res[2:]):
                if isinstance(x, str):
                    continue
                if len(x["dcm"]) != 3 or len(x["angles"]) != 3:
                    raise SystemExit(f"{name}: malformed answer")
                mine = se.to_dcm(*c)
                dm = mdiff(mine, x["dcm"])
                worst_m = max(worst_m, dm)
                back = se.from_dcm(c[0], x["dcm"])
                if c in locked:
                    worst_lock = max(worst_lock, mdiff(se.to_dcm(c[0], *back), x["dcm"]))
                    if not se.is_singular(c[0], x["dcm"]):
                        raise SystemExit(f"gimbal lock not detected for {c}")
                else:
                    da = max(ang(a, b) for a, b in zip(back, x["angles"]))
                    worst_a = max(worst_a, da)
                    per_seq[c[0]] = max(per_seq.get(c[0], 0.0), da, dm)
            entry.update(max_matrix_diff=worst_m, max_angle_diff_deg=worst_a, gimbal_lock_max_rebuilt_matrix_diff=worst_lock,
                         max_diff_by_sequence=per_seq)
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1],
              {k: "%.1e" % v for k, v in entry.items() if isinstance(v, float)}, flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_euler_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("->", dest.name)


if __name__ == "__main__":
    main()
