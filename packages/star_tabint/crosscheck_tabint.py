"""Cross-check of star_tabint against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_tabint.py  ->  12_EVIDENCE/crosscheck_tabint_20261007.json

Lineages, each in its own interpreter; each returns [trapezoid, last cumulative value, a middle cumulative value,
simpson or None]:
  exact   the rules written with SymPy rationals and rounded once: the truth;
  numpy   numpy.trapezoid and a cumulative sum of the panels;
  scipy   scipy.integrate.trapezoid, cumulative_trapezoid and simpson.
star_tabint must give the SAME float as the exact value on every table. NumPy and SciPy round at every step: they
are compared within 1e-12 of the natural scale of the sum (the sum of the absolute areas of the panels), which is
their own rounding and not a disagreement on the rule.
Probe (by hand, exact): Simpson's rule with four intervals for 1/x on [1, 2] is 1747/2520 = 0.693253968253968...;
the trapezoid rule for x^2 at x = 0, 1, 2 is 3; Simpson's rule is exact for a cubic: x^3 at 0, 1, 2 gives 4.
Corpus (seed 20261007): 500 tables of 2 to 60 points: irregular and regular abscissas, values of mixed magnitude and
sign (lobes that cancel), a large offset in x. Simpson's rule is compared on the tables with an odd number of
equally spaced points.
"""
import json
import random
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_tabint as st  # noqa: E402

EXACT = """from fractions import Fraction
from sympy import Rational
def R(v):
    q = Fraction(v); return Rational(q.numerator, q.denominator)
def f(xs, ys, step):
    x = [R(v) for v in xs]; y = [R(v) for v in ys]
    panels = [(x[k + 1] - x[k]) * (y[k] + y[k + 1]) / 2 for k in range(len(x) - 1)]
    cum = [sum(panels[:k]) for k in range(len(x))]
    s = None
    if step is not None:
        s = float(R(step) * (y[0] + y[-1] + 4 * sum(y[1:-1:2]) + 2 * sum(y[2:-1:2])) / 3)
    return [float(sum(panels)), float(cum[-1]), float(cum[len(cum) // 2]), s]
"""
NUMPY = """import numpy as np
def f(xs, ys, step):
    x = np.array(xs); y = np.array(ys)
    cum = np.concatenate([[0.0], np.cumsum(np.diff(x) * (y[:-1] + y[1:]) / 2)])
    return [float(np.trapezoid(y, x)), float(cum[-1]), float(cum[len(cum) // 2]), None]
"""
SCIPY = """import numpy as np
from scipy import integrate
def f(xs, ys, step):
    cum = integrate.cumulative_trapezoid(ys, xs, initial=0.0)
    s = None if step is None else float(integrate.simpson(ys, dx=step))
    return [float(integrate.trapezoid(ys, xs)), float(cum[-1]), float(cum[len(cum) // 2]), s]
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
PROBE = [[1.0, 1.25, 1.5, 1.75, 2.0], [1.0, 0.8, 2.0 / 3.0, 4.0 / 7.0, 0.5], 0.25]
LIMIT = 1e-12


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"exact": (venv("sympy"), EXACT), "numpy": (venv("scipy"), NUMPY), "scipy": (venv("scipy"), SCIPY)}


def mine(xs, ys, step):
    cum = st.cumulative(xs, ys)
    return [st.trapezoid(xs, ys), cum[-1], cum[len(cum) // 2], None if step is None else st.simpson(ys, step)]


def main():
    rnd = random.Random(20261007)
    cases = [PROBE]
    for k in range(500):
        n = rnd.randint(2, 60)
        regular = k % 2 == 0
        if regular:
            n += (n % 2 == 0)                               # odd, at least 3
            step = 2.0 ** rnd.randint(-6, 4)                # a power of two: the abscissas are then exactly equally spaced
            start = rnd.randint(-1000, 1000) * step
            xs = [start + j * step for j in range(n)]
        else:
            step = None
            origin = 10 ** rnd.randint(6, 9) if k % 4 == 1 else rnd.uniform(-10, 10)
            xs = [float(origin)]
            for _ in range(n - 1):
                xs.append(xs[-1] + rnd.uniform(0.01, 3.0))
        scale = 10 ** rnd.uniform(-3, 6)
        ys = [rnd.uniform(-1, 1) * scale * (10 ** rnd.uniform(-4, 0) if k % 5 == 0 else 1.0) for _ in range(n)]
        cases.append([xs, ys, step])
    total = len(cases) - 1
    ours = [mine(*c) for c in cases]
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
        p = res[0]
        valid = not isinstance(p, str) and (p[3] is None or abs(p[3] - 1747 / 2520) < 1e-14) and abs(p[0] - 0.697023809523809) < 1e-12
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            unequal = worst = n = compared = 0
            for (xs, ys, step), got, ref in zip(cases[1:], ours[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                scale = sum((b - a) * (abs(u) + abs(v)) / 2 for a, b, u, v in zip(xs, xs[1:], ys, ys[1:])) or 1.0
                for a, b in zip(got, ref):
                    if b is None:
                        continue
                    compared += 1
                    unequal += a != b
                    worst = max(worst, abs(a - b) / scale)
            entry.update(compared=n, values_compared=compared, not_identical=unequal, max_scaled_diff=worst)
            entry["within"] = unequal == 0 if name == "exact" else worst <= LIMIT
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(p)[:120]}", "errors", len(errors), errors[:1], entry.get("values_compared"), entry.get("not_identical"), entry.get("max_scaled_diff"), flush=True)
    L = out["lineages"]
    mine_ok = abs(st.simpson(PROBE[1], 0.25) - float(Fraction(1747, 2520))) < 2e-16 and st.trapezoid([0, 1, 2], [0, 1, 4]) == 3.0 and st.simpson([0, 1, 8], 1) == 4.0
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v.get("within") for v in L.values())
    double = max(L[k].get("max_scaled_diff", 1.0) for k in ("numpy", "scipy"))
    out["published"] = {"source": "by hand, exact: Simpson's rule with four intervals for 1/x on [1, 2] is 1747/2520; the trapezoid rule for x^2 at 0, 1, 2 is 3; Simpson's rule for x^3 at 0, 1, 2 is 4",
                        "star_tabint_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rationals", "numpy.trapezoid", "scipy.integrate (trapezoid, cumulative_trapezoid, simpson)"],
                      "claim": "star_tabint returns the trapezoid rule, its running integral and the composite Simpson rule of a table as the exact value of the rule rounded once",
                      "crosscheck": f"{total} tables of 2 to 60 points ({L['exact'].get('values_compared')} values): every value IDENTICAL to the exact rational value rounded once; NumPy and SciPy within "
                                    f"{double:.1e} of the sum of the absolute panel areas (their own rounding)",
                      "benchmark": f"values not identical to the exact one: {L['exact'].get('not_identical')} of {L['exact'].get('values_compared')}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_tabint_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
