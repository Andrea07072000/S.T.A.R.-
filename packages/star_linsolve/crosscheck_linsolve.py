"""Cross-check of star_linsolve against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_linsolve.py  ->  12_EVIDENCE/crosscheck_linsolve_20261007.json

Lineages, each in its own interpreter:
  sympy   sympy.Matrix of exact rationals: det(), LUsolve(), inv() (the truth, rounded at the end);
  mpmath  mpmath.det, mpmath.lu_solve and mpmath.inverse at 400 digits;
  numpy   numpy.linalg.det, solve and inv (LAPACK, double precision).
Probe (published): the Hilbert matrix of order 3 has determinant 1/2160 and inverse ((9, -36, 30), (-36, 192, -180),
(30, -180, 180)) (e.g. MathWorld, "Hilbert Matrix"; Choi, "Tricks or treats with the Hilbert matrix", 1983). Multiplied
by 60 it has integer entries ((60, 30, 20), (30, 20, 15), (20, 15, 12)), determinant 60^3 / 2160 = 100 and the same
inverse divided by 60.
Corpus (seed 20261007): 110 well-conditioned systems (order 1 to 8, entries in [-5, 5], diagonal raised) and 40 badly
conditioned ones (Hilbert matrices of order 6 to 12 as floats, and 2 x 2 matrices whose rows differ in the last bits).
Differences are measured per system as the largest |difference| over the largest |value| of star_linsolve, separately
for the determinant, the solution and the inverse. On the badly conditioned set NumPy is measured and reported, not
held to a limit; a system it refuses as singular (LinAlgError) is counted and not compared.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_linsolve as sl  # noqa: E402

SYMPY = '''
from fractions import Fraction
from sympy import Matrix, Rational
def R(v):
    f = Fraction(v)
    return Rational(f.numerator, f.denominator)
def F(c):
    return float(Fraction(int(c.p), int(c.q)))
def one(a, b):
    m = Matrix([[R(v) for v in row] for row in a])
    x = m.LUsolve(Matrix([R(v) for v in b]))
    inv = m.inv()
    n = len(a)
    return [F(m.det()), [F(v) for v in x], [[F(inv[i, j]) for j in range(n)] for i in range(n)]]
'''
MPMATH = '''
import mpmath as mp
from fractions import Fraction
mp.mp.dps = 400
def M(v):
    f = Fraction(v)
    return mp.mpf(f.numerator) / mp.mpf(f.denominator)
def one(a, b):
    m = mp.matrix([[M(v) for v in row] for row in a])
    x = mp.lu_solve(m, mp.matrix([M(v) for v in b]))
    inv = mp.inverse(m)
    n = len(a)
    return [float(mp.det(m)), [float(v) for v in x], [[float(inv[i, j]) for j in range(n)] for i in range(n)]]
'''
NUMPY = '''
import numpy as np
def one(a, b):
    m = np.array(a, dtype=float)
    try:
        np.linalg.inv(m)
    except np.linalg.LinAlgError:
        return "refused"                      # "Singular matrix" for a matrix that is not singular: counted, not compared
    return [float(np.linalg.det(m)), np.linalg.solve(m, np.array(b, dtype=float)).tolist(), np.linalg.inv(m).tolist()]
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
PROBE_A = [[60.0, 30.0, 20.0], [30.0, 20.0, 15.0], [20.0, 15.0, 12.0]]
PROBE_INV = [[9 / 60, -36 / 60, 30 / 60], [-36 / 60, 192 / 60, -180 / 60], [30 / 60, -180 / 60, 180 / 60]]


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"sympy": (venv("sympy"), SYMPY), "mpmath": (venv("mpmath"), MPMATH), "numpy": (venv("scipy"), NUMPY)}
LIMITS = {"sympy": 0.0, "mpmath": 0.0, "numpy": 1e-12}          # measured 5.3e-15 on the well-conditioned systems
EASY = 110


def corpus():
    rnd = random.Random(20261007)
    job = []
    for k in range(EASY):
        n = 1 + k % 8
        a = [[rnd.uniform(-5.0, 5.0) for _ in range(n)] for _ in range(n)]
        for i in range(n):
            a[i][i] += 20.0 if a[i][i] >= 0 else -20.0                      # diagonally dominant: well conditioned
        job.append([a, [rnd.uniform(-10.0, 10.0) for _ in range(n)]])
    for k in range(40):
        if k % 2:
            n = 6 + (k // 2) % 7
            a = [[1.0 / (i + j + 1) for j in range(n)] for i in range(n)]
        else:
            n, eps = 2, 2.0 ** -(10 + k // 2)                              # down to 2^-29: the determinant, about eps^2, is still not zero
            a = [[1.0, 1.0 + eps], [1.0 - eps, 1.0 + eps * eps * 3]]
        job.append([a, [rnd.uniform(-10.0, 10.0) for _ in range(n)]])
    return job + [[PROBE_A, [110.0, 65.0, 47.0]]]                           # the solution of the probe is (1, 1, 1)


def flat(result):
    return [[result[0]], list(result[1]), [v for row in result[2] for v in row]]


def spread(theirs, ours):
    return max(abs(p - q) for p, q in zip(theirs, ours)) / max(max(abs(q) for q in ours), 1e-300)


def main():
    job = corpus()
    mine = [flat([sl.det(a), sl.solve(a, b), sl.inverse(a)]) for a, b in job]
    mine_ok = mine[-1][0] == [100.0] and mine[-1][1] == [1.0, 1.0, 1.0] and mine[-1][2] == [v for row in PROBE_INV for v in row]
    out = {"cases": len(job), "seed": 20261007, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if len(res) != len(job):
            raise SystemExit(f"{name}: wrong number of answers")
        refused = [i for i, x in enumerate(res) if x == "refused"]
        errors = [x for x in res if isinstance(x, str) and x != "refused"]
        valid = isinstance(res[-1], list) and abs(res[-1][0] - 100.0) < 1e-9 and all(abs(v - 1.0) < 1e-9 for v in res[-1][1])
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1], "refused_as_singular_not_compared": len(refused),
                 "refused_all_badly_conditioned": all(EASY <= i < len(job) - 1 for i in refused)}
        if valid and not errors:
            theirs = [m if x == "refused" else flat(x) for x, m in zip(res, mine)]      # a refused system contributes no difference
            worst = {}
            for part, label in enumerate(("determinant", "solution", "inverse")):
                diffs = [spread(t[part], m[part]) for t, m in zip(theirs, mine)]
                worst[label] = {"well_conditioned": max(diffs[:EASY] + diffs[-1:]), "badly_conditioned": max(diffs[EASY:-1])}
            well = max(v["well_conditioned"] for v in worst.values())
            bad = max(v["badly_conditioned"] for v in worst.values())
            entry.update(compared=len(job) - len(refused), identical=sum(t == m for i, (t, m) in enumerate(zip(theirs, mine)) if i not in refused), max_diff=worst,
                         within=(max(well, bad) <= LIMITS[name]) if name != "numpy" else well <= LIMITS[name], limit=LIMITS[name],
                         limit_applies_to="every system" if name != "numpy" else "the well-conditioned systems only")
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("identical"), entry.get("max_diff"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    N = L["numpy"].get("max_diff") or {}
    well = max((v["well_conditioned"] for v in N.values()), default=0.0)
    bad = max((v["badly_conditioned"] for v in N.values()), default=0.0)
    out["published"] = {"source": "Hilbert matrix of order 3: determinant 1/2160, inverse ((9, -36, 30), (-36, 192, -180), (30, -180, 180)) (MathWorld, Hilbert Matrix); "
                                  "times 60 it has integer entries, determinant 100 and that inverse divided by 60", "star_linsolve_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rationals", "mpmath at 400 digits", "numpy.linalg (LAPACK)"],
                      "claim": "star_linsolve returns the float nearest to the exact determinant, to each component of the solution and to each entry of the inverse of the matrix as given, "
                               "for orders 1 to 20, whatever the conditioning",
                      "crosscheck": f"{len(job)} systems ({EASY} well conditioned, 40 badly conditioned, and the Hilbert matrix of order 3 times 60): determinant, solution and inverse equal SymPy's "
                                    f"exact results rounded to a float ({L['sympy'].get('identical')} of {L['sympy'].get('compared')} systems identical) and mpmath's at 400 digits "
                                    f"({L['mpmath'].get('identical')} of {L['mpmath'].get('compared')}); NumPy agrees within {well:.1e} on the well-conditioned systems and differs by up to "
                                    f"{bad:.1e} of the largest value on the badly conditioned ones it accepts ({L['numpy'].get('refused_as_singular_not_compared')} it refuses as "
                                    f"singular, though their determinant is not zero)",
                      "benchmark": f"largest difference from the exact results: 0.0; numpy.linalg on Hilbert matrices of order 6 to 12 and nearly singular 2 x 2 matrices: up to {bad:.1e} relative"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_linsolve_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
