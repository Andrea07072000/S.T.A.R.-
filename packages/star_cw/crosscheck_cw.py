"""Cross-check of star_cw against two independent determinations (S.T.A.R., 2026-10-06).

  python crosscheck_cw.py  ->  12_EVIDENCE/crosscheck_cw_20261006.json

Lineages, each in its own interpreter:
  expm       SciPy matrix exponential of the 6x6 system matrix of the Clohessy-Wiltshire equations (no closed form):
             checks the ALGEBRA of the transition matrix;
  two_body   NAIF CSPICE prop2b: chief and deputy are propagated as two full Keplerian orbits and differenced in the
             rotating frame of the chief: checks the PHYSICS, i.e. how far the linear model is from real two-body
             motion as the separation grows.
Probe (textbook property of the model): a deputy started at (x0, 0, 0) with along-track velocity -2 n x0 flies a
closed 2-by-1 ellipse: after a quarter period it must be at (0, -2 x0, 0). A lineage that misses it is excluded (tolerance: 1e-9 for the
algebra; 5 x0^2 / radius for the two-body lineage, which is not supposed to follow the linear model exactly).
Corpus (seed 20261006): 300 random states and times up to 3 revolutions for expm; for two_body 60 states at each
separation scale 1 m, 100 m and 10 km around a 7000 km circular orbit, drift of up to one revolution.
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
import star_cw as cw  # noqa: E402

MU, A_KM = 398600.4418, 7000.0
N = math.sqrt(MU / A_KM ** 3)
EXPM = '''
import numpy as np
from scipy.linalg import expm
def f(state, n, t):
    A = np.zeros((6, 6))
    A[0, 3] = A[1, 4] = A[2, 5] = 1.0
    A[3, 0], A[3, 4] = 3 * n * n, 2 * n
    A[4, 3] = -2 * n
    A[5, 2] = -n * n
    return [float(v) for v in expm(A * t) @ np.array(state)]
'''
TWO_BODY = f"MU = {MU!r}\nA_KM = {A_KM!r}\n" + '''
import math
import numpy as np
import spiceypy as sp
def frame(r, v):
    x = r / np.linalg.norm(r)
    z = np.cross(r, v)
    z = z / np.linalg.norm(z)
    return np.array([x, np.cross(z, x), z])            # rows: radial, along-track, normal
def f(state, n, t):
    rc, vc = np.array([A_KM, 0.0, 0.0]), np.array([0.0, math.sqrt(MU / A_KM), 0.0])
    R = frame(rc, vc)
    w = np.array([0.0, 0.0, n])
    rho, rhod = np.array(state[:3]), np.array(state[3:])
    rd, vd = rc + R.T @ rho, vc + R.T @ (rhod + np.cross(w, rho))
    c = np.array(sp.prop2b(MU, np.concatenate([rc, vc]), t))
    d = np.array(sp.prop2b(MU, np.concatenate([rd, vd]), t))
    R = frame(c[:3], c[3:])
    rho = R @ (d[:3] - c[:3])
    return [float(v) for v in np.concatenate([rho, R @ (d[3:] - c[3:]) - np.cross(w, rho)])]
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:80])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"expm": (str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), EXPM), "two_body": (sys.executable, TWO_BODY)}
SCALES_KM = (0.001, 0.1, 10.0)
PROBE = [[1.0, 0.0, 0.0, 0.0, -2.0 * N * 1.0, 0.0], N, 0.5 * math.pi / N]


def corpus():
    rnd = random.Random(20261006)
    alg = [PROBE]
    for _ in range(300):
        n = 10 ** rnd.uniform(-4.3, -2.9)                                  # GEO to very low orbit
        scale = 10 ** rnd.uniform(-3, 2)
        alg.append([[rnd.uniform(-1, 1) * scale for _ in range(3)] + [rnd.uniform(-1, 1) * scale * n for _ in range(3)], n,
                    rnd.uniform(0.0, 3.0) * 2 * math.pi / n])
    phys = [PROBE]
    for scale in SCALES_KM:
        for _ in range(60):
            phys.append([[rnd.uniform(-1, 1) * scale for _ in range(3)] + [rnd.uniform(-1, 1) * scale * N for _ in range(3)], N,
                         rnd.uniform(0.05, 1.0) * 2 * math.pi / N])
    return {"expm": alg, "two_body": phys}


def main():
    cases = corpus()
    out = {"seed": 20261006, "chief_radius_km": A_KM, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        cs = cases[name]
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cs), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cs):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        p = res[0]
        # the algebra must be exact; real two-body motion departs from the model by about separation^2 / radius
        tol = 1e-9 if name == "expm" else 5.0 * 1.0 / A_KM
        valid = isinstance(p, list) and len(p) == 6 and max(abs(a - b) for a, b in zip(p[:3], (0.0, -2.0, 0.0))) < tol
        entry = {"cases": len(cs) - 1, "probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and name == "expm":
            worst = 0.0
            for c, x in zip(cs[1:], res[1:]):
                if isinstance(x, list):
                    m = cw.propagate(*c)
                    if len(m) != 6 or len(x) != 6:
                        raise SystemExit(f"{name}: a state does not have six components")
                    size = max(math.hypot(*x[:3]), math.hypot(*c[0][:3]))
                    worst = max(worst, math.hypot(*[a - b for a, b in zip(m[:3], x[:3])]) / size,
                                math.hypot(*[a - b for a, b in zip(m[3:], x[3:])]) / (size * c[1]))
            entry["max_relative_diff"] = worst
        if valid and name == "two_body":
            by = {}
            for k, (c, x) in enumerate(zip(cs[1:], res[1:])):
                if isinstance(x, list):
                    scale = SCALES_KM[k // 60]
                    m = cw.propagate(*c)
                    if len(m) != 6 or len(x) != 6:
                        raise SystemExit(f"{name}: a state does not have six components")
                    by[scale] = max(by.get(scale, 0.0), math.hypot(*[a - b for a, b in zip(m[:3], x[:3])]))
            entry["max_position_diff_km_by_separation_km"] = {str(k): v for k, v in by.items()}
            entry["ratio_error_over_separation_squared_per_radius"] = {str(k): v / (k * k / A_KM) for k, v in by.items()}
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "diff" in k or "ratio" in k}, flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_cw_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("->", dest.name)


if __name__ == "__main__":
    main()
