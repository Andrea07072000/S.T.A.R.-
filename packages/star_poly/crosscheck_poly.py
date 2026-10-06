"""Cross-check of star_poly against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_poly.py  ->  12_EVIDENCE/crosscheck_poly_20261006.json

Lineages, each in its own interpreter:
  sympy   sympy.real_roots on the exact rational value of every coefficient: the distinct real roots, their NUMBER
          decided exactly, evaluated to 30 digits and rounded. This is the truth for both the count and the values.
  mpmath  mpmath.polyroots at 60 digits: every root (real and complex) of the same polynomial;
  numpy   numpy.roots (companion-matrix eigenvalues, double precision).
mpmath and NumPy cannot say how many roots are real when two are close, so for them the check is that every root
returned by star_poly is a root of theirs (to 1e-12 relative for mpmath, 1e-5 for NumPy, whose clustered roots are
poor); the number of real roots is checked against SymPy only.
Probe (published): the textbook case of cancellation x^2 - 1e8 x + 1, whose roots are 1e8 and 1e-8 (e.g. Forsythe,
"Pitfalls in computation", 1970; Numerical Recipes 5.6), and x^3 - 6 x^2 + 11 x - 6 = (x - 1)(x - 2)(x - 3).
Corpus (seed 20261006): 300 quadratics and 300 cubics: random coefficients of mixed magnitude, polynomials built from
small integer roots (so that double and triple roots are exact), and roots separated by up to 1e12; plus 40 with a
leading coefficient between 1e-30 and 1e-10, where one root runs away towards infinity.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_poly as sp  # noqa: E402

SYMPY = ("from sympy import Poly, Rational, symbols, real_roots\nfrom fractions import Fraction\nx = symbols('x')\n"
         "def R(v):\n    f = Fraction(v); return Rational(f.numerator, f.denominator)\n"
         "def f(cs):\n"
         "    p = Poly(sum(R(c) * x ** (len(cs) - 1 - i) for i, c in enumerate(cs)), x)\n"
         "    return {'real': sorted(float(r.evalf(30)) for r in set(real_roots(p)))}\n")
MPMATH = ("import mpmath as mp\nmp.mp.dps = 60\ndef f(cs):\n"
          "    rs = mp.polyroots([mp.mpf(c) for c in cs], maxsteps=2000, extraprec=2000)\n"
          "    return {'all': [[float(mp.re(r)), float(mp.im(r))] for r in rs]}\n")
NUMPY = "import numpy as np\ndef f(cs):\n    return {'all': [[float(r.real), float(r.imag)] for r in np.roots(cs)]}\n"
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"sympy": (venv("sympy"), SYMPY), "mpmath": (venv("mpmath"), MPMATH), "numpy": (venv("scipy"), NUMPY)}


def mine(cs):
    return sp.quadratic_roots(*cs) if len(cs) == 3 else sp.cubic_roots(*cs)


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


def main():
    rnd = random.Random(20261006)
    cases = [[1.0, -1e8, 1.0], [1.0, -6.0, 11.0, -6.0]]

    def coeff():
        return rnd.uniform(-1, 1) * 10 ** rnd.uniform(-3, 6)

    def from_roots(roots, lead):
        cs = [lead]
        for r in roots:                                     # multiply by (x - r): exact for small integers
            cs = [a - r * b for a, b in zip(cs + [0.0], [0.0] + cs)]
        return cs

    for k in range(300):
        if k % 3 == 0:
            cases.append([coeff() or 1.0, coeff(), coeff()])
        elif k % 3 == 1:
            r = rnd.randint(-9, 9)
            cases.append(from_roots([r, r if k % 2 else rnd.randint(-9, 9)], float(rnd.choice((1, 2, -3)))))
        else:
            small = 10 ** rnd.uniform(-6, 0) * rnd.choice((-1, 1))
            cases.append(from_roots([small, small * 10 ** rnd.uniform(0, 12)], 1.0))
    for k in range(300):
        if k % 3 == 0:
            cases.append([coeff() or 1.0, coeff(), coeff(), coeff()])
        elif k % 3 == 1:
            r = rnd.randint(-9, 9)
            pick = (r, r, r) if k % 4 == 1 else ((r, r, rnd.randint(-9, 9)) if k % 4 == 3 else (rnd.randint(-9, 9), rnd.randint(-9, 9), rnd.randint(-9, 9)))
            cases.append(from_roots(list(pick), float(rnd.choice((1, 2, -3)))))
        else:
            small = 10 ** rnd.uniform(-4, 0) * rnd.choice((-1, 1))
            cases.append(from_roots([small, small * 10 ** rnd.uniform(1, 6), -small * 10 ** rnd.uniform(6, 12)], 1.0))
    for k in range(40):                                     # a tiny leading coefficient: one root runs away towards infinity (found by hand, 2026-10-06)
        tiny = 10 ** rnd.uniform(-30, -10) * rnd.choice((-1, 1))
        cases.append([tiny, coeff(), coeff()] if k % 2 else [tiny, coeff(), coeff(), coeff()])
    total = len(cases) - 2
    out = {"cases": total, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        if name == "sympy":
            valid = isinstance(res[0], dict) and len(res[0]["real"]) == 2 and abs(res[0]["real"][0] / 1e-8 - 1.0) < 1e-12 and res[1]["real"] == [1.0, 2.0, 3.0]
        else:
            valid = isinstance(res[1], dict) and sorted(round(a[0], 6) for a in res[1]["all"]) == [1.0, 2.0, 3.0]
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst = 0.0
            count_mismatch = n = missing = 0
            example = None
            for cs, x in zip(cases[2:], res[2:]):
                if isinstance(x, str):
                    continue
                n += 1
                got = mine(cs)
                if "real" in x:
                    if len(got) != len(x["real"]):
                        count_mismatch += 1
                        example = example or [cs, list(got), x["real"]]
                        continue
                    for a, b in zip(got, x["real"]):
                        d = rel(a, b) if b != 0.0 else abs(a)
                        if d > worst:
                            worst, example = d, [cs, list(got), x["real"]]
                else:
                    tol = 1e-12 if name == "mpmath" else 1e-5
                    scale = max(abs(a[0]) + abs(a[1]) for a in x["all"]) or 1.0
                    for g in got:                           # every root of ours must be one of theirs
                        d = min(abs(g - a[0]) + abs(a[1]) for a in x["all"]) / max(abs(g), 1e-300 if name == "mpmath" else 1e-9 * scale)
                        worst = max(worst, min(d, 1e9))
                        missing += d > tol
            entry.update(compared=n, real_root_count_mismatches=count_mismatch, roots_of_ours_not_found=missing, max_root_rel_diff=worst, example=example if name == "sympy" else None)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[:2]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if k in ("compared", "real_root_count_mismatches",
              "roots_of_ours_not_found", "max_root_rel_diff")}, flush=True)
    L = out["lineages"]
    S, M, N = L["sympy"], L["mpmath"], L["numpy"]
    probe = sp.quadratic_roots(1.0, -1e8, 1.0)
    mine_ok = len(probe) == 2 and abs(probe[0] / 1e-8 - 1.0) < 1e-15 and sp.cubic_roots(1.0, -6.0, 11.0, -6.0) == (1.0, 2.0, 3.0)
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == total for v in L.values()) and mine_ok and S["real_root_count_mismatches"] == 0 \
        and S["max_root_rel_diff"] < 1e-12 and M["roots_of_ours_not_found"] == 0 and N["roots_of_ours_not_found"] == 0
    out["published"] = {"source": "x^2 - 1e8 x + 1 has the roots 1e8 and 1e-8 (Forsythe 1970; Numerical Recipes 5.6); x^3 - 6x^2 + 11x - 6 = (x-1)(x-2)(x-3)",
                        "star_poly_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy real_roots on exact rational coefficients", "mpmath polyroots at 60 digits", "numpy.roots"],
                      "claim": "star_poly returns the right NUMBER of distinct real roots of a quadratic or a cubic, double and triple roots included, and each root to the last digits",
                      "crosscheck": f"{total} quadratics and cubics (random, exact multiple roots, roots separated by up to 1e12, leading coefficients down to 1e-30): the number of real roots equals SymPy's exact count "
                                    f"in every case ({S['real_root_count_mismatches']} mismatches) and the roots agree within {S['max_root_rel_diff']:.1e} relative; every root is a root "
                                    f"for mpmath at 60 digits (1e-12) and for NumPy (1e-5)",
                      "benchmark": f"largest relative difference from the exact roots: {S['max_root_rel_diff']:.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_poly_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name, "| example:", S.get("example"))


if __name__ == "__main__":
    main()
