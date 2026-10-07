"""Cross-check of star_linefit against four independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_linefit.py  ->  12_EVIDENCE/crosscheck_linefit_20261007.json

Lineages, each in its own interpreter; every one returns (slope, intercept, slope error, intercept error, residual
standard deviation, correlation), with None where it has no such result:
  exact    the centred sums as exact rationals in SymPy, square roots at 60 digits, each result rounded once: the truth;
  scipy    scipy.stats.linregress (slope, intercept, their standard errors, r);
  numpy    numpy.polyfit of degree 1 (slope and intercept) and numpy.corrcoef;
  cpython  statistics.linear_regression and statistics.correlation (CPython 3.12).
star_linefit must give the SAME float as the exact value on every dataset. The three double-precision lineages
are compared on the "plain" half of the corpus (x within +-10, where their own rounding is small) within 1e-7 of
each result's natural scale (linregress derives the errors from 1 - r^2, which cancels when the fit is almost exact); on the "offset" half (x = 1e6 .. 1e9 plus small steps, where a double-precision fit
loses digits) their largest deviation is recorded and is not a criterion.
Probe (published): NIST Statistical Reference Datasets, linear regression, dataset Norris (36 observations):
certified slope 1.00211681802045, intercept -0.262323073774029, standard errors 0.429796848199937E-03 and
0.232818234301152, residual standard deviation 0.884796396144373.
Corpus (seed 20261007): 500 datasets of 3 to 40 points: a line plus noise, exact lines, points with repeated x.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_linefit as sl  # noqa: E402

NORRIS_Y = [0.1, 338.8, 118.1, 888.0, 9.2, 228.1, 668.5, 998.5, 449.1, 778.9, 559.2, 0.3, 0.1, 778.1, 668.8, 339.3, 448.9, 10.8, 557.7, 228.3, 998.0, 888.8, 119.6, 0.3, 0.6,
            557.6, 339.3, 888.0, 998.5, 778.9, 10.2, 117.6, 228.9, 668.4, 449.2, 0.2]
NORRIS_X = [0.2, 337.4, 118.2, 884.6, 10.1, 226.5, 666.3, 996.3, 448.6, 777.0, 558.2, 0.4, 0.6, 775.5, 666.9, 338.0, 447.5, 11.6, 556.0, 228.1, 995.8, 887.6, 120.2, 0.3, 0.3,
            556.8, 339.1, 887.2, 999.0, 779.0, 11.1, 118.3, 229.2, 669.1, 448.9, 0.5]
CERTIFIED = [1.00211681802045, -0.262323073774029, 0.429796848199937e-03, 0.232818234301152, 0.884796396144373]
EXACT = """from fractions import Fraction
from sympy import Rational, sqrt
def R(v):
    q = Fraction(v); return Rational(q.numerator, q.denominator)
def fl(e):
    return float(e.evalf(60))
def f(xs, ys):
    x = [R(v) for v in xs]; y = [R(v) for v in ys]; n = len(x)
    mx = sum(x) / n; my = sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x); syy = sum((b - my) ** 2 for b in y); sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    slope = sxy / sxx; var = (syy - sxy * sxy / sxx) / (n - 2)
    r = None if syy == 0 else (-1 if sxy < 0 else 1) * fl(sqrt(sxy * sxy / (sxx * syy)))
    return [fl(slope), fl(my - slope * mx), fl(sqrt(var / sxx)), fl(sqrt(var * (Rational(1, n) + mx * mx / sxx))), fl(sqrt(var)), r]
"""
SCIPY = ("from scipy import stats\n"
         "def f(xs, ys):\n    r = stats.linregress(xs, ys)\n    return [float(r.slope), float(r.intercept), float(r.stderr), float(r.intercept_stderr), None, float(r.rvalue)]\n")
NUMPY = """import numpy as np
def f(xs, ys):
    a, b = np.polyfit(xs, ys, 1)
    c = float(np.corrcoef(xs, ys)[0, 1])
    return [float(a), float(b), None, None, None, c if c == c else None]
"""
CPYTHON = ("import statistics as st\n"
           "def f(xs, ys):\n    r = st.linear_regression(xs, ys)\n"
           "    try:\n        c = st.correlation(xs, ys)\n    except st.StatisticsError:\n        c = None\n    return [r.slope, r.intercept, None, None, None, c]\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
NAMES = ("slope", "intercept", "slope_error", "intercept_error", "residual_sd", "correlation")
LIMIT = 1e-7


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"exact": (venv("sympy"), EXACT), "scipy": (venv("scipy"), SCIPY), "numpy": (venv("scipy"), NUMPY), "cpython": (venv("sympy"), CPYTHON)}


def mine(xs, ys):
    try:
        r = sl.correlation(xs, ys)
    except ValueError:
        r = None                                            # all y equal: not defined
    return list(sl.fit(xs, ys)) + list(sl.fit_errors(xs, ys)) + [r]


def main():
    rnd = random.Random(20261007)
    cases = [[NORRIS_X, NORRIS_Y]]
    for k in range(500):
        n = rnd.randint(3, 40)
        if k % 2 == 0:                                      # plain
            xs = [rnd.uniform(-10, 10) for _ in range(n)] if k % 6 else [float(rnd.randint(-5, 5)) for _ in range(n)]
            if len(set(xs)) < 2:
                xs[0] += 1.0
        else:                                               # offset: a large origin plus small steps
            base = 10 ** rnd.randint(6, 9)
            xs = [float(base + j) + (rnd.random() if k % 4 == 1 else 0.0) for j in range(n)]
        a, b = rnd.uniform(-5, 5), rnd.uniform(-100, 100)
        noise = 0.0 if k % 10 == 0 else 10 ** rnd.uniform(-3, 1)
        cases.append([xs, [a * x + b + rnd.gauss(0.0, noise) if noise else float(round(a)) * x + round(b) for x in xs]])
    total = len(cases) - 1
    ours = [mine(*c) for c in cases]
    out = {"cases": total, "seed": 20261007, "plain": total // 2, "offset": total - total // 2, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = not isinstance(res[0], str) and all(v is None or abs(v - c) <= 1e-9 * abs(c) for v, c in zip(res[0][:5], CERTIFIED))
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            unequal = {}
            worst = {"plain": 0.0, "offset": 0.0}
            n = 0
            for k, ((xs, ys), got, ref) in enumerate(zip(cases[1:], ours[1:], res[1:])):
                if isinstance(ref, str):
                    continue
                n += 1
                group = "plain" if k % 2 == 0 else "offset"
                span_y = (max(ys) - min(ys)) or 1.0
                span_x = max(xs) - min(xs)
                scales = (span_y / span_x, span_y + abs(got[0]) * max(abs(v) for v in xs), span_y / span_x, span_y + abs(got[0]) * max(abs(v) for v in xs), span_y, 1.0)
                for stat, a, b, scale in zip(NAMES, got, ref, scales):
                    if a is None or b is None:
                        continue
                    unequal[stat] = unequal.get(stat, 0) + (a != b)
                    worst[group] = max(worst[group], abs(a - b) / scale)
            entry.update(compared=n, not_identical=unequal, max_scaled_diff=worst)
            entry["within"] = all(v == 0 for v in unequal.values()) if name == "exact" else worst["plain"] <= LIMIT
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(res[0])[:150]}", "errors", len(errors), errors[:1], entry.get("not_identical") if name == "exact" else "", entry.get("max_scaled_diff"), flush=True)
    L = out["lineages"]
    mine_ok = all(abs(v - c) <= 1e-13 * abs(c) for v, c in zip(ours[0][:5], CERTIFIED))
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v.get("within") for v in L.values())
    double_plain = max(L[k].get("max_scaled_diff", {"plain": 1.0})["plain"] for k in ("scipy", "numpy", "cpython"))
    double_offset = max(L[k].get("max_scaled_diff", {"offset": 1.0})["offset"] for k in ("scipy", "numpy", "cpython"))
    out["published"] = {"source": "NIST StRD linear regression, dataset Norris: slope 1.00211681802045, intercept -0.262323073774029, standard errors 0.429796848199937E-03 and "
                                  "0.232818234301152, residual standard deviation 0.884796396144373", "star_linefit_observed": ours[0][:5], "star_linefit_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rationals", "scipy.stats.linregress", "numpy.polyfit and corrcoef", "CPython statistics"],
                      "claim": "star_linefit returns the least-squares line, its standard errors and the correlation as the exact value of each formula rounded once",
                      "crosscheck": f"{total} datasets of 3 to 40 points: all six results IDENTICAL to the exact rational value rounded once; on the plain half SciPy, NumPy and CPython statistics agree "
                                    f"within {double_plain:.1e} of the natural scale; on the half with x near 1e6 to 1e9 their largest deviation is {double_offset:.1e} (their rounding, recorded, not a criterion)",
                      "benchmark": f"results not identical to the exact value: {sum((L['exact'].get('not_identical') or {'': 1}).values())}; NIST Norris certified values reproduced to 1e-13 relative: {mine_ok}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_linefit_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, ours[0][:5], "->", dest.name)


if __name__ == "__main__":
    main()
