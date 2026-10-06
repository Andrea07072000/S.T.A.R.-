"""Cross-check of star_interp against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_interp.py  ->  12_EVIDENCE/crosscheck_interp_20261006.json

Lineages, each in its own interpreter:
  sympy  sympy.polys.polyfuncs.interpolate on the exact rational value of every float: the interpolating polynomial
         and its derivative in EXACT arithmetic, rounded once at the end. This is the truth the others are measured against.
  scipy  scipy.interpolate.BarycentricInterpolator and its derivative (double precision);
  numpy  numpy.polynomial.Polynomial.fit of full degree and its derivative (a least-squares fit that passes through the
         points; double precision, a different algorithm).
Probe (published): Meeus, Astronomical Algorithms, Example 3.a: the distance of Mars on 1992 November 7, 8, 9 at 0h TD is
0.884226, 0.877366, 0.870531 AU; on November 8 at 4h 21m it is 0.876125 AU. A lineage further than 5e-7 is excluded.
Corpus (seed 20261006): 600 tables of 2 to 11 points, as an ephemeris has them: nearly equally spaced nodes (jittered
by up to 30 % of the step), in random order, values of a smooth function or random; x anywhere within the nodes
(half of them in the central interval, where interpolation is meant to be used).
Differences are relative to the largest tabulated value.
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
import star_interp as si  # noqa: E402

MEEUS = ([7.0, 8.0, 9.0], [0.884226, 0.877366, 0.870531], 8.0 + 4.35 / 24.0, 0.876125)
SYMPY = ("from sympy import Rational, symbols, diff\nfrom sympy.polys.polyfuncs import interpolate\nfrom fractions import Fraction\nt = symbols('t')\n"
         "def R(v):\n    f = Fraction(v); return Rational(f.numerator, f.denominator)\n"
         "def f(xs, ys, x):\n"
         "    p = interpolate([(R(a), R(b)) for a, b in zip(xs, ys)], t)\n"
         "    return {'v': float(p.subs(t, R(x))), 'd': float(diff(p, t).subs(t, R(x)))}\n")
SCIPY = ("from scipy.interpolate import BarycentricInterpolator\ndef f(xs, ys, x):\n"
         "    b = BarycentricInterpolator(xs, ys, rng=20261006)    # SciPy permutes the nodes at random: seeded, or two runs differ in the last digits\n"
         "    return {'v': float(b(x)), 'd': float(b.derivative(x))}\n")
NUMPY = ("import numpy as np\ndef f(xs, ys, x):\n"
         "    p = np.polynomial.Polynomial.fit(xs, ys, len(xs) - 1)\n    return {'v': float(p(x)), 'd': float(p.deriv()(x))}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"sympy": (venv("sympy"), SYMPY), "scipy": (venv("scipy"), SCIPY), "numpy": (venv("scipy"), NUMPY)}


def main():
    rnd = random.Random(20261006)
    cases = [list(MEEUS[:3])]
    for k in range(600):
        n = rnd.randint(2, 11)
        step, x0 = 10 ** rnd.uniform(-2, 3), rnd.uniform(-1e4, 1e4)
        xs = [x0 + step * (i + rnd.uniform(-0.3, 0.3)) for i in range(n)]
        if k % 2:
            a, w, ph = 10 ** rnd.uniform(-3, 6), rnd.uniform(0.2, 2.0) / (step * n), rnd.uniform(0, 6.28)
            ys = [a * math.sin(w * (v - x0) + ph) + 0.3 * a for v in xs]
        else:
            ys = [rnd.uniform(-1, 1) * 10 ** rnd.uniform(-3, 6) for _ in xs]
        s = sorted(xs)
        mid = (n - 1) // 2
        lo, hi = (s[mid], s[mid + 1]) if k % 4 < 2 else (s[0], s[-1])
        order = list(range(n))
        rnd.shuffle(order)
        x = rnd.uniform(lo, hi) if k % 10 else s[rnd.randrange(n)]            # one in ten exactly at a node
        cases.append([[xs[i] for i in order], [ys[i] for i in order], x])
    out = {"cases": len(cases) - 1, "seed": 20261006, "lineages": {}}
    truth = None
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=1800)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = isinstance(res[0], dict) and abs(res[0].get("v", 0.0) - MEEUS[3]) < 5e-7
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            if name == "sympy":
                truth = res
            v = d = lib_v = 0.0
            n_cases = 0
            for c, x, tr in zip(cases[1:], res[1:], (truth or res)[1:]):
                if isinstance(x, str):
                    continue
                n_cases += 1
                scale = max(abs(y) for y in c[1])
                span = max(c[0]) - min(c[0])
                v = max(v, abs(si.lagrange(*c) - x["v"]) / scale)
                d = max(d, abs(si.lagrange_derivative(*c) - x["d"]) * span / (scale * len(c[0]) ** 2))
                lib_v = max(lib_v, abs(x["v"] - tr["v"]) / scale)
            entry.update(compared=n_cases, max_value_rel_diff=v, max_derivative_scaled_diff=d, max_library_value_error_vs_exact=lib_v)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if k.startswith("max_")}, flush=True)
    L = out["lineages"]
    mine = abs(si.lagrange(*MEEUS[:3]) - MEEUS[3])
    S = L["sympy"]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and mine < 5e-7 \
        and S["max_value_rel_diff"] < 1e-11 and S["max_derivative_scaled_diff"] < 1e-10 \
        and max(L["scipy"]["max_value_rel_diff"], L["numpy"]["max_value_rel_diff"]) < 1e-8
    out["published"] = {"source": "Meeus Example 3.a: 0.876125 AU", "star_interp_abs_diff": mine}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rational interpolation", "scipy.interpolate.BarycentricInterpolator", "numpy.polynomial.Polynomial.fit",
                                             "Meeus, Astronomical Algorithms, Example 3.a"],
                      "claim": "star_interp evaluates the interpolating polynomial and its derivative to the accuracy double precision allows, as measured against exact arithmetic",
                      "crosscheck": f"600 tables of 2 to 11 jittered, unsorted nodes: value within {S['max_value_rel_diff']:.1e} of the exact polynomial (relative to the largest "
                                    f"tabulated value) and derivative within {S['max_derivative_scaled_diff']:.1e} (scaled by span and n^2); within "
                                    f"{L['scipy']['max_value_rel_diff']:.1e} of SciPy and {L['numpy']['max_value_rel_diff']:.1e} of NumPy, whose own errors against the exact value "
                                    f"are {L['scipy']['max_library_value_error_vs_exact']:.1e} and {L['numpy']['max_library_value_error_vs_exact']:.1e}; Meeus example within {mine:.1e}",
                      "benchmark": f"error against exact arithmetic: star_interp {S['max_value_rel_diff']:.1e}, SciPy {L['scipy']['max_library_value_error_vs_exact']:.1e}, "
                                   f"NumPy {L['numpy']['max_library_value_error_vs_exact']:.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_interp_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "Meeus diff %.1e" % mine, "->", dest.name)


if __name__ == "__main__":
    main()
