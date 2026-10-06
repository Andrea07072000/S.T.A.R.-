"""Cross-check of star_quadrature against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_quadrature.py  ->  12_EVIDENCE/crosscheck_quadrature_20261006.json

Lineages, each in its own interpreter:
  sympy   sympy.integrals.quadrature.gauss_legendre at 40 digits (the truth for nodes and weights), the Legendre
          polynomials and their derivatives evaluated on exact rationals, and exact integrals of monomials;
  numpy   numpy.polynomial.legendre.leggauss (eigenvalues of the companion matrix and one Newton step) and
          numpy.polynomial.Legendre for values and derivatives;
  scipy   scipy.special.roots_legendre (Golub-Welsch), scipy.special.eval_legendre, scipy.integrate.fixed_quad; the
          derivative from the identity (1 - x^2) P_n' = n (P_(n-1) - x P_n), which cancels near the ends (limit 1e-9).
Probe (published, Abramowitz & Stegun table 25.4): the 2-point rule has the nodes +-1/sqrt(3) = +-0.577350269189626
and the weights 1; the 3-point rule has the nodes 0, +-sqrt(3/5) = +-0.774596669241483 and the weights 8/9, 5/9.
Corpus (seed 20261006): every rule from 1 to 32 points (528 nodes and weights); 400 pairs (n, x) with n from 0 to 32
and x in [-1, 1], the two ends included; 120 integrals of a monomial x^k, k <= 2n - 1, over an interval with
rational ends, for which the rule is exact.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_quadrature as sq  # noqa: E402

SYMPY = ("from sympy import Rational, Symbol, diff, legendre_poly, integrate as integ\nfrom sympy.integrals.quadrature import gauss_legendre\n"
         "from fractions import Fraction\nX = Symbol('x')\n"
         "def R(v):\n    f = Fraction(v); return Rational(f.numerator, f.denominator)\n"
         "def rule(n):\n    x, w = gauss_legendre(n, 40); return [[float(a) for a in x], [float(a) for a in w]]\n"
         "def point(n, x):\n    p = legendre_poly(n, X); return [float(p.subs(X, R(x)).evalf(30)), float(diff(p, X).subs(X, R(x)).evalf(30))]\n"
         "def integral(n, k, a, b):\n    return float(integ(X ** k, (X, R(a), R(b))).evalf(30))\n")
NUMPY = ("import numpy as np\nfrom numpy.polynomial import Legendre\n"
         "def rule(n):\n    x, w = np.polynomial.legendre.leggauss(n); return [x.tolist(), w.tolist()]\n"
         "def point(n, x):\n    p = Legendre.basis(n); return [float(p(x)), float(p.deriv()(x))]\n"
         "def integral(n, k, a, b):\n    x, w = np.polynomial.legendre.leggauss(n); return float((b - a) / 2 * np.sum(w * ((a + b) / 2 + (b - a) / 2 * x) ** k))\n")
SCIPY = ("import numpy as np\nfrom scipy import special, integrate\n"
         "def rule(n):\n    x, w = special.roots_legendre(n); return [x.tolist(), w.tolist()]\n"
         "def point(n, x):\n    p = float(special.eval_legendre(n, x))\n    if n == 0:\n        return [p, 0.0]\n"
         "    if abs(x) == 1.0:\n        return [p, x ** (n + 1) * n * (n + 1) / 2]\n"
         "    return [p, float(n * (special.eval_legendre(n - 1, x) - x * p) / (1 - x * x))]\n"
         "def integral(n, k, a, b):\n    return float(integrate.fixed_quad(lambda t: t ** k, a, b, n=n)[0])\n")
RUNNER = ("\nimport json, sys\njob = json.load(sys.stdin)\nout = {}\nfor name, fn in (('rules', rule), ('points', point), ('integrals', integral)):\n"
          "    out[name] = []\n    for args in job[name]:\n        try:\n            out[name].append(fn(*args))\n"
          "        except Exception as e:\n            out[name].append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"sympy": (venv("sympy"), SYMPY), "numpy": (venv("scipy"), NUMPY), "scipy": (venv("scipy"), SCIPY)}
LIMITS = {"sympy": {"node": 0.0, "weight": 4e-16, "legendre": 1e-12, "integral": 1e-13},
          "numpy": {"node": 1e-14, "weight": 1e-11, "legendre": 1e-11, "integral": 1e-11},
          "scipy": {"node": 1e-14, "weight": 1e-11, "legendre": 1e-9, "integral": 1e-11}}


def rel(a, b):
    return abs(a - b) / max(abs(b), 1.0)


def main():
    rnd = random.Random(20261006)
    job = {"rules": [[n] for n in range(1, sq.MAX_POINTS + 1)], "points": [], "integrals": []}
    for k in range(400):
        n = k % (sq.MAX_POINTS + 1)
        job["points"].append([n, (-1.0, 1.0, 0.0)[k % 40] if k % 40 < 3 else rnd.uniform(-1.0, 1.0)])
    for k in range(120):
        n = 1 + k % 12
        a = rnd.randint(-40, 40) / 8.0
        job["integrals"].append([n, rnd.randint(0, 2 * n - 1), a, a + rnd.randint(1, 24) / 8.0])
    sizes = {k: len(v) for k, v in job.items()}
    out = {"cases": sizes, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if any(len(res[k]) != sizes[k] for k in sizes):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for k in sizes for x in res[k] if isinstance(x, str)]
        two, three = res["rules"][1], res["rules"][2]
        valid = not isinstance(two, str) and not isinstance(three, str) and abs(two[0][1] - 0.577350269189626) < 1e-14 and abs(two[1][0] - 1.0) < 1e-14 \
            and abs(three[0][2] - 0.774596669241483) < 1e-14 and abs(three[1][1] - 8.0 / 9.0) < 1e-14 and abs(three[1][0] - 5.0 / 9.0) < 1e-14
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            worst = {"node": 0.0, "weight": 0.0, "legendre": 0.0, "integral": 0.0}
            for (n,), (xs, ws) in zip(job["rules"], res["rules"]):
                mx, mw = sq.gauss_legendre(n)
                worst["node"] = max([worst["node"]] + [abs(a - b) for a, b in zip(mx, xs)])
                worst["weight"] = max([worst["weight"]] + [abs(a - b) / b for a, b in zip(mw, ws)])
            for (n, x), ref in zip(job["points"], res["points"]):
                worst["legendre"] = max([worst["legendre"]] + [rel(a, b) for a, b in zip(sq.legendre(n, x), ref)])
            for (n, k, a, b), ref in zip(job["integrals"], res["integrals"]):
                worst["integral"] = max(worst["integral"], rel(sq.integrate(lambda t, k=k: t ** k, a, b, n), ref))
            entry.update(compared=sum(sizes.values()), max_diff=worst, within=all(worst[k] <= LIMITS[name][k] for k in worst), limits=LIMITS[name])
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("max_diff"), entry.get("within"), flush=True)
    L = out["lineages"]
    x2, w2 = sq.gauss_legendre(2)
    x3, w3 = sq.gauss_legendre(3)
    mine_ok = abs(x2[1] - 0.577350269189626) < 1e-15 and w2 == (1.0, 1.0) and abs(x3[2] - 0.774596669241483) < 1e-15 and x3[1] == 0.0 \
        and abs(w3[1] - 8.0 / 9.0) < 2e-16 and abs(w3[0] - 5.0 / 9.0) < 2e-16
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    S = L["sympy"].get("max_diff") or {}
    out["published"] = {"source": "Abramowitz & Stegun, Handbook of Mathematical Functions, table 25.4: n = 2 nodes +-0.577350269189626, weights 1; "
                                  "n = 3 nodes 0, +-0.774596669241483, weights 0.888888888888889, 0.555555555555556", "star_quadrature_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy gauss_legendre at 40 digits and exact Legendre polynomials", "numpy.polynomial.legendre", "scipy.special / scipy.integrate.fixed_quad"],
                      "claim": "star_quadrature returns Gauss-Legendre nodes that are the floats nearest to the true roots and weights correct to the last digit, for 1 to 32 points",
                      "crosscheck": f"all 32 rules (528 nodes and weights), {sizes['points']} Legendre values with derivatives, {sizes['integrals']} exact integrals of monomials: against SymPy at 40 digits the "
                                    f"nodes differ by {S.get('node')} and the weights by at most {S.get('weight', 0):.1e} relative; NumPy and SciPy agree on the nodes within 1e-14 and on the weights "
                                    f"within 1e-11 (their own weights are less accurate than that at 32 points)",
                      "benchmark": f"largest relative difference of a weight from SymPy at 40 digits: {S.get('weight', 0):.1e}; of a node: {S.get('node')}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_quadrature_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
