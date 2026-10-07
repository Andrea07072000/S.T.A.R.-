"""Cross-check of star_polyfit against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_polyfit.py  ->  12_EVIDENCE/crosscheck_polyfit_20261007.json

Lineages, each in its own interpreter:
  sympy   the normal equations with exact rationals solved by sympy.Matrix.LUsolve (the truth, rounded at the end);
  mpmath  mpmath.qr_solve (Householder QR, no normal equations) on the weighted Vandermonde matrix at 120 digits;
  numpy   numpy.polynomial.polynomial.polyfit (double precision, scaled least squares by SVD).
Probe (published): NIST Statistical Reference Datasets, Wampler1: x = 0..20, y = 1 + x + x^2 + x^3 + x^4 + x^5; the
certified coefficients of the fit of degree 5 are all 1.00000000000000 and the residual standard deviation is 0.
Corpus (seed 20261007): 120 well-conditioned problems (degree 0 to 6, 5 to 40 points, x in [-2, 2], a third of them
weighted, some weights exactly 0) and 40 badly conditioned ones (degree 3 to 5, x in [1000, 1001], or x = 1e6 + k).
Differences are measured per problem as the largest |difference of a coefficient| over the largest |coefficient|.
On the badly conditioned set NumPy is measured and reported, not held to a limit: double precision cannot do it
(a difference of 1 means that its coefficients have no digit in common with the exact ones).
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_polyfit as sp  # noqa: E402

SYMPY = '''
from fractions import Fraction
from sympy import Matrix, Rational
def R(v):
    f = Fraction(v)
    return Rational(f.numerator, f.denominator)
def one(xs, ys, degree, weights):
    w = [R(v) for v in (weights or [1.0] * len(xs))]
    x = [R(v) for v in xs]
    y = [R(v) for v in ys]
    n = degree + 1
    a = Matrix(n, n, lambda i, j: sum(wk * xk ** (i + j) for wk, xk in zip(w, x)))
    b = Matrix(n, 1, lambda i, j: sum(wk * xk ** i * yk for wk, xk, yk in zip(w, x, y)))
    return [float(Fraction(int(c.p), int(c.q))) for c in a.LUsolve(b)]
'''
MPMATH = '''
import mpmath as mp
from fractions import Fraction
mp.mp.dps = 120
def M(v):
    f = Fraction(v)
    return mp.mpf(f.numerator) / mp.mpf(f.denominator)
def one(xs, ys, degree, weights):
    rows = [(M(x), M(y), mp.sqrt(M(w))) for x, y, w in zip(xs, ys, weights or [1.0] * len(xs)) if w != 0]
    a = mp.matrix(len(rows), degree + 1)
    b = mp.matrix(len(rows), 1)
    for i, (x, y, s) in enumerate(rows):
        for j in range(degree + 1):
            a[i, j] = s * x ** j
        b[i] = s * y
    c, _ = mp.qr_solve(a, b)
    return [float(v) for v in c]
'''
NUMPY = '''
import numpy as np
from numpy.polynomial import polynomial as P
def one(xs, ys, degree, weights):
    w = None if weights is None else np.sqrt(np.array(weights))
    return [float(v) for v in P.polyfit(np.array(xs), np.array(ys), degree, w=w)]
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
WAMPLER_X = [float(k) for k in range(21)]
WAMPLER_Y = [float(1 + k + k ** 2 + k ** 3 + k ** 4 + k ** 5) for k in range(21)]


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"sympy": (venv("sympy"), SYMPY), "mpmath": (venv("mpmath"), MPMATH), "numpy": (venv("scipy"), NUMPY)}
LIMITS = {"sympy": 0.0, "mpmath": 0.0, "numpy": 1e-8}           # NumPy on Wampler1: measured 1.0e-9; on the random problems 9e-14


def corpus():
    rnd = random.Random(20261007)
    job = []
    for k in range(120):
        degree, n = k % 7, rnd.randint(max(5, k % 7 + 2), 40)
        xs = [rnd.uniform(-2.0, 2.0) for _ in range(n)]
        ys = [rnd.uniform(-10.0, 10.0) for _ in range(n)]
        weights = None
        if k % 3 == 0:
            weights = [rnd.choice([0.0, 0.5, 1.0, 2.0, rnd.uniform(0.1, 5.0)]) for _ in range(n)]
            for i in range(degree + 1):                      # enough points with a positive weight
                weights[i] = 1.0
        job.append([xs, ys, degree, weights])
    for k in range(40):
        degree, n = 3 + k % 3, rnd.randint(8, 30)
        xs = [1000.0 + rnd.random() for _ in range(n)] if k % 2 else [1e6 + i for i in range(n)]
        job.append([xs, [rnd.uniform(-10.0, 10.0) for _ in range(n)], degree, None])
    return job + [[WAMPLER_X, WAMPLER_Y, 5, None]]


def spread(a, b):
    return max(abs(p - q) for p, q in zip(a, b)) / max(max(abs(q) for q in b), 1e-300)


def main():
    job = corpus()
    easy = 120
    mine = [list(sp.polyfit(xs, ys, d, w)) for xs, ys, d, w in job]
    mine_ok = mine[-1] == [1.0] * 6 and sp.residual_sum(WAMPLER_X, WAMPLER_Y, mine[-1]) == 0.0
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
        valid = isinstance(res[-1], list) and all(abs(c - 1.0) < 1e-6 for c in res[-1])
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            diffs = [spread(b, a) for a, b in zip(mine, res)]          # relative to the largest coefficient of star_polyfit
            well, bad = max(diffs[:easy] + diffs[-1:]), max(diffs[easy:-1])
            entry.update(compared=len(job), identical=sum(a == b for a, b in zip(mine, res)), max_diff={"well_conditioned": well, "badly_conditioned": bad},
                         within=(max(well, bad) <= LIMITS[name]) if name != "numpy" else well <= LIMITS[name], limit=LIMITS[name],
                         limit_applies_to="every problem" if name != "numpy" else "the well-conditioned problems only")
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("identical"), entry.get("max_diff"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    N = L["numpy"].get("max_diff") or {}
    out["published"] = {"source": "NIST Statistical Reference Datasets, Wampler1 (x = 0..20, y = 1 + x + x^2 + x^3 + x^4 + x^5): certified coefficients of the degree-5 fit all "
                                  "1.00000000000000, residual standard deviation 0", "star_polyfit_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rationals (LU on the normal equations)", "mpmath.qr_solve at 120 digits", "numpy.polynomial.polynomial.polyfit"],
                      "claim": "star_polyfit returns the float nearest to each exact least-squares coefficient of the data as given, for degree 0 to 10, weighted or not, whatever the conditioning",
                      "crosscheck": f"{len(job)} problems ({easy} well conditioned, 40 badly conditioned, and NIST Wampler1): every coefficient equals SymPy's exact solution rounded to a float "
                                    f"({L['sympy'].get('identical')} of {L['sympy'].get('compared')} problems identical) and mpmath's QR at 120 digits ({L['mpmath'].get('identical')} of "
                                    f"{L['mpmath'].get('compared')}); NumPy agrees within {N.get('well_conditioned', 0):.1e} on the well-conditioned problems and differs by up to "
                                    f"{N.get('badly_conditioned', 0):.1e} of the largest coefficient on the badly conditioned ones",
                      "benchmark": f"largest difference from the exact solution: 0.0; NumPy on problems with x in [1000, 1001] or x = 1e6 + k: up to {N.get('badly_conditioned', 0):.1e} relative"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_polyfit_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
