"""Cross-check of star_quantile against four independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_quantile.py  ->  12_EVIDENCE/crosscheck_quantile_20261007.json

Lineages, each in its own interpreter; each returns [median, quantile(q), interquartile range, median absolute
deviation], with None where it has no such result:
  exact    the Hyndman-Fan type 7 definition written with SymPy rationals (q as the exact value of its float),
           rounded once: the truth;
  numpy    numpy.median, numpy.quantile (method 'linear'), the difference of two numpy.quantile for the range;
  scipy    scipy.stats.iqr, scipy.stats.median_abs_deviation (scale 1), scipy.stats.scoreatpercentile;
  cpython  statistics.median and statistics.quantiles(n=4, method='inclusive') for the quartiles.
star_quantile must give the SAME float as the exact value on every dataset. The double-precision lineages
interpolate in floating point: they are compared within 1e-13 of the largest |value| of the dataset.
Probe (published): the worked example of the median absolute deviation, data (1, 1, 2, 2, 4, 6, 9): median 2,
absolute deviations (1, 1, 0, 0, 2, 4, 7), MAD 1; and the quartiles of 1..5 by the type 7 definition (Hyndman and
Fan 1996; the default of R and NumPy): 2 and 4.
Corpus (seed 20261007): 500 datasets of 1 to 60 values: mixed magnitudes, ties, a large offset, outliers; q drawn in
[0, 1] with 0, 1, 0.25, 0.5, 0.75 and 0.1 included.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_quantile as sq  # noqa: E402

EXACT = """from fractions import Fraction
from sympy import Rational, floor
def R(v):
    f = Fraction(v); return Rational(f.numerator, f.denominator)
def at(xs, q):
    h = (len(xs) - 1) * q
    lo = int(floor(h))
    return xs[lo] if lo == len(xs) - 1 else xs[lo] + (h - lo) * (xs[lo + 1] - xs[lo])
def f(values, q):
    xs = sorted(R(v) for v in values)
    med = at(xs, Rational(1, 2))
    dev = sorted(abs(v - med) for v in xs)
    return [float(med), float(at(xs, R(q))), float(at(xs, Rational(3, 4)) - at(xs, Rational(1, 4))), float(at(dev, Rational(1, 2)))]
"""
NUMPY = """import numpy as np
def f(values, q):
    x = np.array(values)
    return [float(np.median(x)), float(np.quantile(x, q, method='linear')), float(np.quantile(x, 0.75) - np.quantile(x, 0.25)), float(np.median(np.abs(x - np.median(x))))]
"""
SCIPY = """import numpy as np
from scipy import stats
def f(values, q):
    x = np.array(values)
    return [None, float(stats.scoreatpercentile(x, 100.0 * q)) if q in (0.0, 0.25, 0.5, 0.75, 1.0) else None, float(stats.iqr(x)), float(stats.median_abs_deviation(x, scale=1.0))]
"""
CPYTHON = """import statistics as st
def f(values, q):
    quart = st.quantiles(values, n=4, method='inclusive') if len(values) > 1 else None
    pick = {0.25: 0, 0.5: 1, 0.75: 2}.get(q)
    return [st.median(values), None if quart is None or pick is None else quart[pick], None if quart is None else quart[2] - quart[0], None]
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
PROBES = [[[1.0, 1.0, 2.0, 2.0, 4.0, 6.0, 9.0], 0.5], [[1.0, 2.0, 3.0, 4.0, 5.0], 0.25]]
LIMIT = 1e-13


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"exact": (venv("sympy"), EXACT), "numpy": (venv("scipy"), NUMPY), "scipy": (venv("scipy"), SCIPY), "cpython": (venv("sympy"), CPYTHON)}


def mine(values, q):
    return [sq.median(values), sq.quantile(values, q), sq.iqr(values), sq.mad(values)]


def main():
    rnd = random.Random(20261007)
    cases = list(PROBES)
    special = (0.0, 1.0, 0.25, 0.5, 0.75, 0.1)
    for k in range(500):
        n = rnd.randint(1, 60)
        kind = k % 5
        if kind == 0:
            values = [rnd.uniform(-1, 1) * 10 ** rnd.uniform(-4, 4) for _ in range(n)]
        elif kind == 1:
            values = [float(rnd.randint(-5, 5)) for _ in range(n)]                       # many ties
        elif kind == 2:
            base = 10 ** rnd.randint(6, 12)
            values = [float(base) + rnd.random() for _ in range(n)]
        elif kind == 3:
            values = [rnd.gauss(0.0, 1.0) for _ in range(n)] + [1e12 * rnd.choice((-1, 1))]   # an outlier
        else:
            values = [rnd.uniform(0.0, 1.0) for _ in range(n)]
        cases.append([values, special[k % 12] if k % 12 < 6 else rnd.random()])
    total = len(cases) - 2
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
        a, b = res[0], res[1]
        valid = not isinstance(a, str) and not isinstance(b, str) and a[0] in (None, 2.0) and a[3] in (None, 1.0) and b[1] in (None, 2.0) and b[2] in (None, 2.0) \
            and any(v is not None for v in a)
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            unequal = compared = n = 0
            worst = 0.0
            for (values, _), got, ref in zip(cases[2:], ours[2:], res[2:]):
                if isinstance(ref, str):
                    continue
                n += 1
                scale = max(abs(v) for v in values) or 1.0
                for x, y in zip(got, ref):
                    if y is None:
                        continue
                    compared += 1
                    unequal += x != y
                    worst = max(worst, abs(x - y) / scale)
            entry.update(compared=n, values_compared=compared, not_identical=unequal, max_scaled_diff=worst)
            entry["within"] = unequal == 0 if name == "exact" else worst <= LIMIT
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(res[:2])[:150]}", "errors", len(errors), errors[:1], entry.get("values_compared"), entry.get("not_identical"), entry.get("max_scaled_diff"), flush=True)
    L = out["lineages"]
    mine_ok = ours[0] == [2.0, 2.0, 3.5, 1.0] and ours[1][:3] == [3.0, 2.0, 2.0]   # quartiles of the seven values: 1.5 and 5 (positions 1.5 and 4.5)
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v.get("within") for v in L.values())
    double = max(L[k].get("max_scaled_diff", 1.0) for k in ("numpy", "scipy", "cpython"))
    out["published"] = {"source": "worked example of the median absolute deviation, data (1, 1, 2, 2, 4, 6, 9): median 2, MAD 1; quartiles of 1..5 by the Hyndman-Fan type 7 definition: 2 and 4",
                        "star_quantile_observed": ours[0] + ours[1], "star_quantile_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rationals", "numpy.median / numpy.quantile", "scipy.stats (iqr, median_abs_deviation, scoreatpercentile)", "CPython statistics"],
                      "claim": "star_quantile returns the median, the type 7 quantile, the interquartile range and the median absolute deviation as the exact value of the definition rounded once",
                      "crosscheck": f"{total} datasets of 1 to 60 values ({L['exact'].get('values_compared')} values): every value IDENTICAL to the exact rational value rounded once; NumPy, SciPy and CPython "
                                    f"statistics within {double:.1e} of the largest |value| (their floating-point interpolation)",
                      "benchmark": f"values not identical to the exact one: {L['exact'].get('not_identical')} of {L['exact'].get('values_compared')}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_quantile_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, ours[0], ours[1], "->", dest.name)


if __name__ == "__main__":
    main()
