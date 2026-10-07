"""Cross-check of star_wahba against two independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_wahba.py  ->  12_EVIDENCE/crosscheck_wahba_20261007.json

Lineages, each in its own interpreter:
  scipy  scipy.spatial.transform.Rotation.align_vectors(bodies, refs, weights): the solution of Wahba's problem by a
         singular value decomposition (Kabsch / Markley), another algorithm than the eigenvector of the q-method;
  ahrs   ahrs.filters.TRIAD(w1, w2, v1, v2).A: the TRIAD attitude matrix from the first two pairs.
Probe (by hand): a frame turned by +90 degrees about z has the attitude matrix ((0, 1, 0), (-1, 0, 0), (0, 0, 1)); the
reference directions (1, 0.2, 0.3), (0.1, 1, -0.4), (0.5, -0.5, 0.7) are seen in the body as that matrix times each.
Corpus (seed 20261007): 400 attitudes drawn uniformly, 2 to 8 directions each with the first two at least 20 degrees
apart, random weights; half of the problems noise-free, half with the body directions perturbed by 0.01 rad.
Differences: the largest element of the difference of two attitude matrices (about the angle between the two
attitudes, in radians). With noise the q-method and the SVD must still agree (they minimise the same loss), and TRIAD
must agree with TRIAD (it is one algorithm); TRIAD and the q-method are different estimates and are not compared.
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
import star_wahba as sw  # noqa: E402

SCIPY = '''
import numpy as np
from scipy.spatial.transform import Rotation as R
def one(refs, bodies, weights):
    r = np.array(refs, dtype=float)
    b = np.array(bodies, dtype=float)
    r /= np.linalg.norm(r, axis=1)[:, None]
    b /= np.linalg.norm(b, axis=1)[:, None]
    rot, _ = R.align_vectors(b, r, weights=weights)
    return rot.as_matrix().tolist()
'''
AHRS = '''
import numpy as np
from ahrs.filters import TRIAD
def one(refs, bodies, weights):
    return np.asarray(TRIAD(w1=np.array(bodies[0], dtype=float), w2=np.array(bodies[1], dtype=float), v1=np.array(refs[0], dtype=float), v2=np.array(refs[1], dtype=float)).A).tolist()
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
QUARTER_TURN = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
PROBE_REFS = [[1.0, 0.2, 0.3], [0.1, 1.0, -0.4], [0.5, -0.5, 0.7]]


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"scipy": (venv("scipy"), SCIPY), "ahrs": (venv("ahrs"), AHRS)}
LIMITS = {"scipy": 1e-11, "ahrs": 1e-11}


def apply(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


def corpus():
    rnd = random.Random(20261007)
    job = []
    for k in range(400):
        attitude = sw.rotation_matrix([rnd.gauss(0, 1) for _ in range(4)])
        n = rnd.randint(2, 8)
        refs = []
        while len(refs) < n:
            v = [rnd.gauss(0, 1) for _ in range(3)]
            size = math.sqrt(sum(c * c for c in v))
            v = [c / size * rnd.uniform(0.5, 3.0) for c in v]              # not unit: only the direction counts
            if len(refs) == 1:
                first = refs[0]
                cos = sum(a * b for a, b in zip(first, v)) / (math.sqrt(sum(a * a for a in first)) * math.sqrt(sum(a * a for a in v)))
                if abs(cos) > math.cos(math.radians(20.0)):
                    continue
            refs.append(v)
        bodies = [apply(attitude, v) for v in refs]
        if k % 2:
            bodies = [[c + rnd.gauss(0, 0.01) * math.sqrt(sum(x * x for x in v)) for c in v] for v in bodies]
        job.append([refs, bodies, [rnd.uniform(0.1, 3.0) for _ in range(n)]])
    return job + [[PROBE_REFS, [apply(QUARTER_TURN, v) for v in PROBE_REFS], [1.0, 2.0, 3.0]]]


def gap(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(3) for j in range(3))


def main():
    job = corpus()
    mine = {"scipy": [sw.rotation_matrix(sw.q_method(r, b, w)) for r, b, w in job], "ahrs": [sw.triad(r[0], r[1], b[0], b[1]) for r, b, _ in job]}
    mine_ok = gap(mine["scipy"][-1], QUARTER_TURN) < 1e-15 and gap(mine["ahrs"][-1], QUARTER_TURN) < 1e-15
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
        valid = isinstance(res[-1], list) and gap(res[-1], QUARTER_TURN) < 1e-12
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            diffs = [gap(a, b) for a, b in zip(mine[name], res)]
            worst = {"noise_free": max(diffs[0:-1:2] + diffs[-1:]), "with_noise": max(diffs[1:-1:2])}
            entry.update(compared=len(job), max_diff=worst, within=max(worst.values()) <= LIMITS[name], limit=LIMITS[name],
                         compares="q_method against the SVD solution" if name == "scipy" else "triad against TRIAD")
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("max_diff"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    S, A = (L["scipy"].get("max_diff") or {}), (L["ahrs"].get("max_diff") or {})
    out["published"] = {"source": "by hand: a frame turned by +90 degrees about z has the attitude matrix ((0, 1, 0), (-1, 0, 0), (0, 0, 1)) (reference to body)",
                        "star_wahba_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["scipy Rotation.align_vectors (SVD)", "ahrs TRIAD"],
                      "claim": "star_wahba returns the same attitude as an SVD solution of Wahba's problem (q-method) and as an independent TRIAD, with and without measurement noise",
                      "crosscheck": f"{len(job)} attitudes with 2 to 8 weighted directions, half of them with 0.01 rad of noise: the q-method differs from SciPy's SVD solution by at most "
                                    f"{S.get('noise_free', 0):.1e} (noise-free) and {S.get('with_noise', 0):.1e} (with noise) in any element of the attitude matrix; TRIAD from ahrs by "
                                    f"{A.get('noise_free', 0):.1e} and {A.get('with_noise', 0):.1e}",
                      "benchmark": f"largest element difference from SciPy: {max(S.values(), default=0):.1e}; from ahrs: {max(A.values(), default=0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_wahba_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
