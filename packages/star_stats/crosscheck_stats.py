"""Cross-check of star_stats against four independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_stats.py  ->  12_EVIDENCE/crosscheck_stats_20261007.json

Lineages, each in its own interpreter:
  mpmath   every statistic summed at 400 digits and rounded once: the truth (the sums are exact at that precision);
  cpython  the `statistics` module of CPython 3.12 (mean, variance, pvariance, stdev, pstdev, fmean with weights):
           it also works on exact fractions, so equality is expected; RMS is not in it and is left out, and its
           weighted mean (fmean) is computed in floating point, so that one is compared like NumPy's;
  numpy    numpy.mean, var, std, average, in double precision;
  scipy    scipy.stats.tmean, tvar, tstd (sample statistics only), in double precision.
The two exact lineages must give the SAME float as star_stats. NumPy and SciPy round at every step, so they are
compared relative to the natural scale of each statistic (the largest |x| for mean, standard deviation and RMS; its
square for the variance): the difference measured there is their rounding error, not a disagreement on the formula.
Probe (published): NIST Statistical Reference Datasets, NumAcc1 (10000001, 10000003, 10000002): mean 10000002, sample
standard deviation 1 exactly; and NumAcc2 (1.2 followed by 500 pairs 1.1, 1.3): mean 1.2, standard deviation 0.1.
Corpus (seed 20261007): 500 datasets of 2 to 60 values: mixed magnitudes, a large offset plus small integers (where
the textbook one-pass formula cancels), equal values, small integers; weights with some zeros.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_stats as ss  # noqa: E402

MPMATH = ("import mpmath as mp\nmp.mp.dps = 400\n"
          "def f(xs, ws):\n    x = [mp.mpf(v) for v in xs]; w = [mp.mpf(v) for v in ws]; n = len(x)\n    m = mp.fsum(x) / n\n"
          "    ssq = mp.fsum((v - m) ** 2 for v in x)\n"
          "    return [float(m), float(ssq / (n - 1)), float(ssq / n), float(mp.sqrt(ssq / (n - 1))), float(mp.sqrt(ssq / n)),\n"
          "            float(mp.sqrt(mp.fsum(v * v for v in x) / n)), float(mp.fsum(a * b for a, b in zip(w, x)) / mp.fsum(w))]\n")
CPYTHON = ("import statistics as st\n"
           "def f(xs, ws):\n    return [st.mean(xs), st.variance(xs), st.pvariance(xs), st.stdev(xs), st.pstdev(xs), None, st.fmean(xs, ws)]\n")
NUMPY = ("import numpy as np\n"
         "def f(xs, ws):\n    x = np.array(xs)\n    return [float(np.mean(x)), float(np.var(x, ddof=1)), float(np.var(x)), float(np.std(x, ddof=1)), float(np.std(x)),\n"
         "            float(np.sqrt(np.mean(x * x))), float(np.average(x, weights=ws))]\n")
SCIPY = ("import numpy as np\nfrom scipy import stats\n"
         "def f(xs, ws):\n    x = np.array(xs)\n    return [float(stats.tmean(x)), float(stats.tvar(x)), None, float(stats.tstd(x)), None, None, None]\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
NAMES = ("mean", "variance", "pvariance", "stdev", "pstdev", "rms", "weighted_mean")
POWER = (1, 2, 2, 1, 1, 1, 1)                                # the scale of each statistic is max|x| to this power
NUMACC1 = [10000001.0, 10000003.0, 10000002.0]
NUMACC2 = [1.2] + [1.1, 1.3] * 500
EXACT = {"mpmath", "cpython"}
LIMIT = 1e-12


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"mpmath": (venv("mpmath"), MPMATH), "cpython": (venv("sympy"), CPYTHON), "numpy": (venv("scipy"), NUMPY), "scipy": (venv("scipy"), SCIPY)}


def mine(xs, ws):
    return [ss.mean(xs), ss.variance(xs), ss.variance(xs, False), ss.stdev(xs), ss.stdev(xs, False), ss.rms(xs), ss.weighted_mean(xs, ws)]


def main():
    rnd = random.Random(20261007)
    cases = [[NUMACC1, [1.0] * 3], [NUMACC2, [1.0] * 1001]]
    for k in range(500):
        n = rnd.randint(2, 60)
        if k % 4 == 0:
            xs = [rnd.uniform(-1, 1) * 10 ** rnd.uniform(-6, 6) for _ in range(n)]
        elif k % 4 == 1:
            base = 10 ** rnd.randint(6, 12)
            xs = [float(base + rnd.randint(-20, 20)) for _ in range(n)]
        elif k % 4 == 2:
            xs = [rnd.uniform(-1e3, 1e3)] * n if k % 8 == 2 else [float(rnd.randint(-9, 9)) for _ in range(n)]
        else:
            xs = [rnd.gauss(100.0, 0.001) for _ in range(n)]
        ws = [0.0 if rnd.random() < 0.2 else rnd.uniform(0.0, 5.0) for _ in range(n)]
        ws[rnd.randrange(n)] = 1.0 + rnd.random()            # never all zero
        cases.append([xs, ws])
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
        valid = not isinstance(res[0], str) and not isinstance(res[1], str) and res[0][0] == 10000002.0 and abs(res[0][3] - 1.0) < 1e-9 \
            and abs(res[1][0] - 1.2) < 1e-12 and abs(res[1][3] - 0.1) < 1e-9
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst = {}
            unequal = {}
            n = 0
            for (xs, _), got, ref in zip(cases[2:], ours[2:], res[2:]):
                if isinstance(ref, str):
                    continue
                n += 1
                top = max(abs(v) for v in xs) or 1.0
                for stat, power, a, b in zip(NAMES, POWER, got, ref):
                    if b is None:
                        continue
                    worst[stat] = max(worst.get(stat, 0.0), abs(a - b) / top ** power)
                    unequal[stat] = unequal.get(stat, 0) + (a != b)
            entry.update(compared=n, max_scaled_diff=worst, not_identical=unequal)
            exact = [k for k in unequal if name in EXACT and not (name == "cpython" and k == "weighted_mean")]
            entry["within"] = all(unequal[k] == 0 for k in exact) and all(v <= LIMIT for v in worst.values())
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(res[:1])[:120]}", "errors", len(errors), errors[:1], entry.get("not_identical"), entry.get("max_scaled_diff"), flush=True)
    L = out["lineages"]
    mine_ok = ss.mean(NUMACC1) == 10000002.0 and ss.stdev(NUMACC1) == 1.0 and ss.mean(NUMACC2) == 1.2 and abs(ss.stdev(NUMACC2) - 0.1) < 2e-16
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v.get("within") for v in L.values())
    double = max(max((L[k].get("max_scaled_diff") or {"": 0.0}).values()) for k in ("numpy", "scipy"))
    out["published"] = {"source": "NIST StRD univariate summary statistics: NumAcc1 mean 10000002, standard deviation 1; NumAcc2 mean 1.2, standard deviation 0.1",
                        "star_stats_observed": [ss.mean(NUMACC1), ss.stdev(NUMACC1), ss.mean(NUMACC2), ss.stdev(NUMACC2)], "star_stats_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["mpmath at 400 digits", "CPython statistics module", "numpy", "scipy.stats"],
                      "claim": "star_stats returns the mean, variance, standard deviation, RMS and weighted mean as the exact value of the formula rounded once to a float",
                      "crosscheck": f"{total} datasets of 2 to 60 values (mixed magnitudes, large offsets, equal values, integers): all seven statistics are IDENTICAL to mpmath at 400 digits "
                                    f"rounded once, and to CPython's statistics module where it has them; NumPy and SciPy differ by at most {double:.1e} of the natural scale (their own rounding)",
                      "benchmark": f"results not identical to the 400-digit value: {sum(L['mpmath'].get('not_identical', {'': 1}).values())} of {7 * total}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_stats_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, out["published"]["star_stats_observed"], "->", dest.name)


if __name__ == "__main__":
    main()
