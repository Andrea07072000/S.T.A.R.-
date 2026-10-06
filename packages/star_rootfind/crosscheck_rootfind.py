"""Cross-check of star_rootfind against three independent root finders (S.T.A.R., 2026-10-07).

  python crosscheck_rootfind.py  ->  12_EVIDENCE/crosscheck_rootfind_20261007.json

Lineages, each in its own interpreter, each evaluating the functions with its own arithmetic:
  mpmath  mpmath.findroot (bisection, 200 halvings of the bracket) at 50 digits: the truth for the root of the mathematical function;
  scipy   scipy.optimize.brentq with the smallest tolerances it accepts (C implementation of Brent's method);
  fluids  fluids.numerics.brenth (a pure-Python Brent with hyperbolic extrapolation, by another author).
Probe (published): the real root of x^3 - 2x - 5, the equation Wallis used in 1685 to present Newton's method:
2.0945514815423265 (2.09455148154232659...).
Corpus (seed 20261007), 600 bracketed problems in six families:
  cube     x^3 - c            on [0, 11]      c in [0.1, 1000]
  exp      exp(x) - c         on [-6, 6]      c in [0.01, 100]
  cosine   cos(x) - k x       on [0, 1.6]     k in [0.1, 5]
  kepler   E - e sin E - M    on [0, pi]      e in [0, 0.95], M in [0.01, 3.1]
  tanh     tanh(x) - c        on [-5, 5]      c in [-0.99, 0.99]
  log      log(x) - c         on [0.01, 30]   c in [-3, 3]
The comparison is relative to max(|root|, 1e-3): star_rootfind is exact about where the COMPUTED function changes
sign; the distance from the true root is the rounding error of the function divided by its slope.
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
import star_rootfind as sr  # noqa: E402

FAMILIES = ("def make(m, kind, p, q):\n"
            "    return {'cube': lambda x: x ** 3 - p, 'exp': lambda x: m.exp(x) - p, 'cosine': lambda x: m.cos(x) - p * x,\n"
            "            'kepler': lambda x: x - p * m.sin(x) - q, 'tanh': lambda x: m.tanh(x) - p, 'log': lambda x: m.log(x) - p,\n"
            "            'wallis': lambda x: x ** 3 - 2 * x - 5}[kind]\n")
MPMATH = FAMILIES + ("import mpmath as mp\nmp.mp.dps = 50\n"
                     "def f(kind, p, q, a, b):\n    return float(mp.findroot(make(mp, kind, mp.mpf(p), mp.mpf(q)), (mp.mpf(a), mp.mpf(b)), solver='bisect', tol=mp.mpf(10) ** -45, maxsteps=200, verify=False))\n")
SCIPY = FAMILIES + ("import math\nfrom scipy.optimize import brentq\n"
                    "def f(kind, p, q, a, b):\n    return float(brentq(make(math, kind, p, q), a, b, xtol=1e-300, rtol=8.881784197001252e-16, maxiter=500))\n")
FLUIDS = FAMILIES + ("import math\nfrom fluids.numerics import brenth\n"
                     "def f(kind, p, q, a, b):\n    return float(brenth(make(math, kind, p, q), a, b, xtol=1e-300, rtol=8.881784197001252e-16, maxiter=500))\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
exec(FAMILIES)                                              # the same definitions for star_rootfind, evaluated with math


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"mpmath": (venv("mpmath"), MPMATH), "scipy": (venv("scipy"), SCIPY), "fluids": (venv("thermo"), FLUIDS)}
LIMIT = {"mpmath": 2e-14, "scipy": 2e-14, "fluids": 2e-14}
WALLIS = 2.0945514815423265


def main():
    rnd = random.Random(20261007)
    cases = [["wallis", 0.0, 0.0, 2.0, 3.0]]
    for k in range(600):
        kind = ("cube", "exp", "cosine", "kepler", "tanh", "log")[k % 6]
        if kind == "cube":
            cases.append([kind, 10 ** rnd.uniform(-1, 3), 0.0, 0.0, 11.0])
        elif kind == "exp":
            cases.append([kind, 10 ** rnd.uniform(-2, 2), 0.0, -6.0, 6.0])
        elif kind == "cosine":
            cases.append([kind, rnd.uniform(0.1, 5.0), 0.0, 0.0, 1.6])
        elif kind == "kepler":
            cases.append([kind, rnd.uniform(0.0, 0.95), rnd.uniform(0.01, 3.1), 0.0, math.pi])
        elif kind == "tanh":
            cases.append([kind, rnd.uniform(-0.99, 0.99), 0.0, -5.0, 5.0])
        else:
            cases.append([kind, rnd.uniform(-3.0, 3.0), 0.0, 0.01, 30.0])
    total = len(cases) - 1
    mine = [sr.find_root(make(math, kind, p, q), a, b) for kind, p, q, a, b in cases]  # noqa: F821
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
        valid = not isinstance(res[0], str) and abs(res[0] - WALLIS) < 1e-14
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst, example, n = 0.0, None, 0
            per_family = {}
            for c, got, ref in zip(cases[1:], mine[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                d = abs(got - ref) / max(abs(ref), 1e-3)
                per_family[c[0]] = max(per_family.get(c[0], 0.0), d)
                if d > worst:
                    worst, example = d, [c, got, ref]
            entry.update(compared=n, max_rel_diff=worst, per_family=per_family, example=example, limit=LIMIT[name])
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[:1]}", "errors", len(errors), errors[:1], entry.get("max_rel_diff"), entry.get("per_family"), flush=True)
    L = out["lineages"]
    mine_ok = abs(mine[0] - WALLIS) <= 4.5e-16
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v["max_rel_diff"] <= LIMIT[k] for k, v in L.items())
    worst = max((v.get("max_rel_diff") or 0.0) for v in L.values())
    out["published"] = {"source": "the real root of x^3 - 2x - 5 (Wallis 1685, Newton's example): 2.0945514815423265", "star_rootfind_observed": mine[0], "star_rootfind_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["mpmath findroot at 50 digits", "scipy.optimize.brentq", "fluids.numerics.brenth"],
                      "claim": "star_rootfind.find_root returns the point where the computed function changes sign, to the last float, with no tolerance and at most 64 evaluations after the two ends",
                      "crosscheck": f"{total} bracketed problems in six families (cube, exponential, cosine, Kepler's equation up to e = 0.95, tanh, logarithm): the roots agree with mpmath at 50 digits, "
                                    f"SciPy brentq and fluids brenth within {worst:.1e} relative",
                      "benchmark": f"largest relative difference from mpmath at 50 digits: {L['mpmath'].get('max_rel_diff', 0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_rootfind_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, mine[0], "->", dest.name)


if __name__ == "__main__":
    main()
