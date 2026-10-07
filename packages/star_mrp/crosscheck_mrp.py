"""Cross-check of star_mrp against two independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_mrp.py  ->  12_EVIDENCE/crosscheck_mrp_20261007.json

Lineages, each in its own interpreter:
  basilisk  Basilisk.utilities.RigidBodyKinematics (the astrodynamics framework of the AVS Laboratory): EP2MRP, MRP2EP,
            MRP2C, addMRP, MRP2PRV, PRV2MRP, MRPswitch and dMRP;
  scipy     scipy.spatial.transform.Rotation: from_mrp / as_mrp, as_quat, as_matrix, as_rotvec, from_rotvec and the
            product of two rotations (no kinematic equation there: mrp_rate is compared with Basilisk only).
Conventions pinned on one case before the corpus: star_mrp.compose(a, b) is Basilisk addMRP(a, b) and SciPy
(R(a) * R(b)).as_mrp(); star_mrp.dcm_from_mrp is Basilisk MRP2C and the transpose of SciPy as_matrix.
Probe (by hand, definition of Schaub and Junkins): the quaternion (1/2, 1/2, 1/2, 1/2), a turn of 120 degrees about
(1, 1, 1), has sigma = v / (1 + w) = (1/3, 1/3, 1/3), i.e. tan(30 deg) / sqrt(3) on each axis.
Corpus (seed 20261007): 600 pairs of MRPs with norms from 1e-8 to 5 (a third beyond 1, where the shadow set applies)
and angular velocities up to 0.1 rad/s.
Differences: largest absolute difference of a component (MRPs with |sigma| <= 1, quaternions, matrices), rotation
vectors in radians, rates relative to the size of the rate.
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
import star_mrp as sm  # noqa: E402

BASILISK = '''
import numpy as np
from Basilisk.utilities import RigidBodyKinematics as rbk
def short(s):
    s = np.array(s, dtype=float)
    return rbk.MRPswitch(s, 1.0)
def one(a, b, w):
    a_, b_ = np.array(a, dtype=float), np.array(b, dtype=float)
    q = rbk.MRP2EP(short(a_))
    return {"quaternion": [float(x) for x in q], "mrp_from_quaternion": [float(x) for x in short(rbk.EP2MRP(q))],
            "dcm": [float(x) for x in np.asarray(rbk.MRP2C(a_)).ravel()], "compose": [float(x) for x in short(rbk.addMRP(short(a_), short(b_)))],
            "rotation_vector": [float(x) for x in rbk.MRP2PRV(short(a_))], "mrp_from_rotation_vector": [float(x) for x in short(rbk.PRV2MRP(rbk.MRP2PRV(short(a_))))],
            "switch": [float(x) for x in short(a_)], "rate": [float(x) for x in rbk.dMRP(a_, np.array(w, dtype=float))]}
'''
SCIPY = '''
import numpy as np
from scipy.spatial.transform import Rotation as R
def one(a, b, w):
    ra, rb = R.from_mrp(a), R.from_mrp(b)
    q = ra.as_quat(scalar_first=True, canonical=True)
    return {"quaternion": q.tolist(), "mrp_from_quaternion": R.from_quat(q, scalar_first=True).as_mrp().tolist(), "dcm": ra.as_matrix().T.ravel().tolist(),
            "compose": (ra * rb).as_mrp().tolist(), "rotation_vector": ra.as_rotvec().tolist(), "mrp_from_rotation_vector": R.from_rotvec(ra.as_rotvec()).as_mrp().tolist(),
            "switch": ra.as_mrp().tolist(), "rate": None}
'''
RUNNER = '''
import json, sys, warnings
warnings.simplefilter("ignore")
job = json.load(sys.stdin)
out = []
for args in job:
    try:
        out.append(one(*args))
    except Exception as e:
        out.append("error:" + type(e).__name__ + ":" + str(e)[:60])
print("@@" + json.dumps(out))
'''
KEYS = ("quaternion", "mrp_from_quaternion", "dcm", "compose", "rotation_vector", "mrp_from_rotation_vector", "switch", "rate")
THIRD = 1.0 / 3.0


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"basilisk": (venv("basilisk"), BASILISK), "scipy": (venv("scipy"), SCIPY)}
LIMITS = {"basilisk": 1e-13, "scipy": 1e-13}          # measured: 6e-16 and 1.4e-15


def corpus():
    rnd = random.Random(20261007)

    def mrp(k):
        v = [rnd.gauss(0, 1) for _ in range(3)]
        size = math.sqrt(sum(c * c for c in v))
        norm = (rnd.uniform(1.0, 5.0) if k % 3 == 0 else 10.0 ** rnd.uniform(-8, 0)) * (0.999 if k % 3 else 1.0)
        return [c / size * norm for c in v]

    return [[mrp(k), mrp(k + 1), [rnd.uniform(-0.1, 0.1) for _ in range(3)]] for k in range(600)] + [[[THIRD, THIRD, THIRD], [0.1, 0.2, 0.3], [0.01, -0.02, 0.03]]]


def ours(a, b, w):
    q = sm.quaternion_from_mrp(a)
    return {"quaternion": list(q), "mrp_from_quaternion": list(sm.mrp_from_quaternion(q)), "dcm": [c for row in sm.dcm_from_mrp(a) for c in row],
            "compose": list(sm.compose(a, b)), "rotation_vector": list(sm.rotation_vector_from_mrp(a)),
            "mrp_from_rotation_vector": list(sm.mrp_from_rotation_vector(sm.rotation_vector_from_mrp(a))), "switch": list(sm.switch(a)), "rate": list(sm.mrp_rate(a, w))}


def gap(key, mine, theirs):
    if key in ("compose", "mrp_from_quaternion", "mrp_from_rotation_vector", "switch", "rotation_vector"):
        # at exactly half a turn the two MRPs of norm 1 (and the two rotation vectors of length pi) are the same attitude
        flipped = max(abs(a + b) for a, b in zip(mine, theirs))
        direct = max(abs(a - b) for a, b in zip(mine, theirs))
        size = math.sqrt(sum(a * a for a in mine))
        at_half_turn = abs(size - (math.pi if key == "rotation_vector" else 1.0)) < 1e-9
        return min(direct, flipped) if at_half_turn else direct
    if key == "rate":
        return max(abs(a - b) for a, b in zip(mine, theirs)) / max(max(abs(a) for a in mine), 1e-300)
    return max(abs(a - b) for a, b in zip(mine, theirs))


def main():
    job = corpus()
    mine = [ours(*args) for args in job]
    half = 0.5
    mine_ok = max(abs(a - b) for a, b in zip(mine[-1]["quaternion"], [half] * 4)) < 2e-16 and sm.mrp_from_quaternion((half, half, half, half)) == (THIRD, THIRD, THIRD)
    out = {"cases": len(job), "seed": 20261007, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if len(res) != len(job):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        probe = res[-1]
        valid = isinstance(probe, dict) and max(abs(a - half) for a in probe["quaternion"]) < 1e-12
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            worst = {k: 0.0 for k in KEYS if res[0][k] is not None}
            for a, b in zip(mine, res):
                for k in worst:
                    worst[k] = max(worst[k], gap(k, a[k], b[k]))
            entry.update(compared=len(job), max_diff=worst, within=max(worst.values()) <= LIMITS[name], limit=LIMITS[name])
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("max_diff"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    B, S = (L["basilisk"].get("max_diff") or {}), (L["scipy"].get("max_diff") or {})
    out["published"] = {"source": "by hand from the definition sigma = e tan(phi / 4) (Schaub and Junkins, Analytical Mechanics of Space Systems): the quaternion (1/2, 1/2, 1/2, 1/2) has "
                                  "sigma = (1/3, 1/3, 1/3)", "star_mrp_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["Basilisk RigidBodyKinematics", "scipy Rotation"],
                      "claim": "star_mrp converts, composes and differentiates modified Rodrigues parameters as two independent implementations do, the shadow set included",
                      "crosscheck": f"{len(job)} pairs of MRPs with norms from 1e-8 to 5 and angular velocities up to 0.1 rad/s: against Basilisk the largest difference is "
                                    f"{max(B.values(), default=0):.1e} over eight operations (the kinematic equation {B.get('rate', 0):.1e} relative); against SciPy "
                                    f"{max(S.values(), default=0):.1e} over seven",
                      "benchmark": f"largest difference from Basilisk: {max(B.values(), default=0):.1e}; from SciPy: {max(S.values(), default=0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_mrp_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
