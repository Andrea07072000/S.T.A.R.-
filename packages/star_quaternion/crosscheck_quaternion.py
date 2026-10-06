"""Cross-check of star_quaternion against two independent rotation libraries (S.T.A.R., 2026-10-06).

  python crosscheck_quaternion.py  ->  12_EVIDENCE/crosscheck_quaternion_20261006.json

Lineages, each in its own interpreter:
  spice   NAIF CSPICE through spiceypy: q2m, m2q, qxq, mxv, raxisa (C translated from Fortran; scalar-first quaternion);
  scipy   scipy.spatial.transform.Rotation (scalar-LAST quaternion: the driver reorders the components).
Every lineage is first PROBED on the textbook case that fixes the convention: the rotation of +90 degrees about +Z,
q = (cos 45, 0, 0, sin 45), must take +X to +Y and have the matrix [[0,-1,0],[1,0,0],[0,0,1]]; a library (or a driver)
with the passive or the transposed convention fails the probe and is excluded.
Corpus (seed 20261006): 400 pairs of random unit quaternions and a random vector, plus identity, half-turns about each
axis and rotations of 1e-9 degrees. Compared: matrix, matrix -> quaternion (up to sign), product, rotated vector,
rotation angle. Quaternions are compared as rotations: q and -q are the same.
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
import star_quaternion as sa  # noqa: E402

S = math.sqrt(0.5)
PROBE = {"a": [S, 0.0, 0.0, S], "b": [1.0, 0.0, 0.0, 0.0], "v": [1.0, 0.0, 0.0]}
DRIVERS = {
    "spice": (sys.executable, "import spiceypy as sp\n"
              "def f(a, b, v):\n    m = sp.q2m(a)\n    ax, ang = sp.raxisa(m)\n"
              "    return {'dcm': [[float(x) for x in r] for r in m], 'quat': [float(x) for x in sp.m2q(m)],\n"
              "            'prod': [float(x) for x in sp.qxq(a, b)], 'rot': [float(x) for x in sp.mxv(m, v)], 'angle': float(ang)}\n"),
    "scipy": (str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), "from scipy.spatial.transform import Rotation as R\nimport math\n"
              "def last(q):\n    return [q[1], q[2], q[3], q[0]]\n"
              "def first(q):\n    return [float(q[3]), float(q[0]), float(q[1]), float(q[2])]\n"
              "def f(a, b, v):\n    ra, rb = R.from_quat(last(a)), R.from_quat(last(b))\n    m = ra.as_matrix()\n"
              "    return {'dcm': [[float(x) for x in r] for r in m], 'quat': first(R.from_matrix(m).as_quat()),\n"
              "            'prod': first((ra * rb).as_quat()), 'rot': [float(x) for x in ra.apply(v)], 'angle': float(ra.magnitude())}\n"),
}
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(c['a'], c['b'], c['v']))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def qdiff(p, q):
    """Largest component difference between two quaternions taken as rotations (sign-free)."""
    return min(max(abs(a - b) for a, b in zip(p, q)), max(abs(a + b) for a, b in zip(p, q)))


def corpus():
    rnd = random.Random(20261006)
    unit = lambda: list(sa.normalize([rnd.gauss(0, 1) for _ in range(4)]))
    cases = [PROBE]
    cases += [{"a": unit(), "b": unit(), "v": [rnd.uniform(-1e4, 1e4) for _ in range(3)]} for _ in range(400)]
    special = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    special += [list(sa.from_axis_angle(ax, 1e-9)) for ax in ((1, 0, 0), (0, 1, 0), (1, 2, 3))]
    special += [list(sa.from_axis_angle((1, -1, 0.5), ang)) for ang in (179.999999, 180.0, 90.0, 359.0)]
    cases += [{"a": q, "b": unit(), "v": [1.0, 2.0, 3.0]} for q in special]
    return cases


def mine(c):
    m = sa.to_dcm(c["a"])
    return {"dcm": [list(r) for r in m], "quat": list(sa.from_dcm(m)), "prod": list(sa.multiply(c["a"], c["b"])),
            "rot": list(sa.rotate(c["a"], c["v"])), "angle": math.radians(sa.to_axis_angle(c["a"])[1])}


def main():
    cases = corpus()
    ours = [mine(c) for c in cases]
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
        p = res[0]
        valid = (isinstance(p, dict) and max(abs(a - b) for a, b in zip(p["rot"], (0.0, 1.0, 0.0))) < 1e-12
                 and max(abs(p["dcm"][i][j] - e) for i, row in enumerate(((0, -1, 0), (1, 0, 0), (0, 0, 1))) for j, e in enumerate(row)) < 1e-12
                 and abs(p["angle"] - math.pi / 2) < 1e-12)
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst = {"dcm": 0.0, "quat_from_dcm": 0.0, "product": 0.0, "rotated_vector_relative": 0.0, "angle_rad": 0.0}
            for c, m, x in zip(cases[1:], ours[1:], res[1:]):
                if isinstance(x, str):
                    continue
                worst["dcm"] = max(worst["dcm"], max(abs(a - b) for ra, rb in zip(m["dcm"], x["dcm"]) for a, b in zip(ra, rb)))
                worst["quat_from_dcm"] = max(worst["quat_from_dcm"], qdiff(m["quat"], x["quat"]))
                worst["product"] = max(worst["product"], qdiff(m["prod"], x["prod"]))
                norm = math.sqrt(sum(a * a for a in c["v"]))
                worst["rotated_vector_relative"] = max(worst["rotated_vector_relative"], max(abs(a - b) for a, b in zip(m["rot"], x["rot"])) / norm)
                worst["angle_rad"] = max(worst["angle_rad"], abs(m["angle"] - x["angle"]))
            entry["max_abs_diff"] = worst
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1],
              {k: "%.1e" % v for k, v in entry["max_abs_diff"].items()} if valid else p, flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_quaternion_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("->", dest.name)


if __name__ == "__main__":
    main()
