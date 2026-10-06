"""Cross-check of star_chebyshev against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_chebyshev.py  ->  12_EVIDENCE/crosscheck_chebyshev_20261007.json

Lineages, each in its own interpreter:
  spice   CSPICE chbval / chbder through SpiceyPy: the routines that evaluate the Chebyshev segments of SPK ephemerides
          (their interval convention, midpoint and radius, is the one of `evaluate_on`);
  numpy   numpy.polynomial.chebyshev.chebval, and chebder followed by chebval for the derivative;
  mpmath  the series summed term by term with mpmath.chebyt and the derivative n U_(n-1) with mpmath.chebyu at 40
          digits: no recurrence shared with the module, and the truth for the rounding error.
Probe (published): the example of the NAIF documentation of chbval and chbder: coefficients (1, 3, 0.5, 1, 0.5, -1, 1)
on the interval of midpoint 0.5 and radius 3, at t = 1: value -0.340878, first derivative 0.382716.
Corpus (seed 20261007): 600 series of 1 to 40 terms, coefficients of mixed magnitude (some decaying like those of an
ephemeris), each evaluated at a point of an interval with random midpoint and radius, the two ends included.
Differences are relative to the sum of |c_k| for the value and to the sum of k^2 |c_k| / radius for the derivative,
the natural scales of the two sums. The limit is 1e-14 against the two double-precision lineages and 5e-14 against
mpmath, which also sees the rounding of x = (t - mid) / radius to a double: an error of one unit in the last place of
x changes a series of 40 terms by up to k^2 times as much.
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
import star_chebyshev as sc  # noqa: E402

SPICE = ("import spiceypy as sp\n"
         "def f(cs, t, mid, radius):\n    d = sp.chbder(cs, len(cs) - 1, [mid, radius], t, 1)\n    return [float(sp.chbval(cs, len(cs) - 1, [mid, radius], t)), float(d[1])]\n")
NUMPY = ("import numpy as np\nfrom numpy.polynomial import chebyshev as C\n"
         "def f(cs, t, mid, radius):\n    x = (t - mid) / radius\n    d = C.chebder(cs) if len(cs) > 1 else [0.0]\n    return [float(C.chebval(x, cs)), float(C.chebval(x, d)) / radius]\n")
MPMATH = ("import mpmath as mp\nmp.mp.dps = 40\n"
          "def f(cs, t, mid, radius):\n    x = (mp.mpf(t) - mp.mpf(mid)) / mp.mpf(radius)\n"
          "    p = mp.fsum(mp.mpf(c) * mp.chebyt(k, x) for k, c in enumerate(cs))\n"
          "    d = mp.fsum(mp.mpf(c) * k * mp.chebyu(k - 1, x) for k, c in enumerate(cs) if k)\n    return [float(p), float(d / mp.mpf(radius))]\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
PROBE = [[1.0, 3.0, 0.5, 1.0, 0.5, -1.0, 1.0], 1.0, 0.5, 3.0]
LIMIT = {"spice": 1e-14, "numpy": 1e-14, "mpmath": 5e-14}


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"spice": (venv("spiceypy"), SPICE), "numpy": (venv("scipy"), NUMPY), "mpmath": (venv("mpmath"), MPMATH)}


def main():
    rnd = random.Random(20261007)
    cases = [PROBE]
    for k in range(600):
        n = rnd.randint(1, 40)
        if k % 3 == 0:
            cs = [rnd.uniform(-1, 1) * 10 ** rnd.uniform(-3, 3) for _ in range(n)]
        elif k % 3 == 1:
            cs = [rnd.uniform(-1, 1) * 1e8 * 10 ** (-0.4 * j) for j in range(n)]          # decaying, like an ephemeris segment
        else:
            cs = [float(rnd.randint(-9, 9)) for _ in range(n)]
        mid, radius = rnd.uniform(-1e6, 1e6), 10 ** rnd.uniform(-3, 5)
        x = (-1.0, 1.0, 0.0)[k % 30] if k % 30 < 3 else rnd.uniform(-1.0, 1.0)
        t = mid + radius * x
        while abs((t - mid) / radius) > 1.0:                # the rounded end fell outside: step back towards the midpoint, float by float
            t = math.nextafter(t, mid)
        cases.append([cs, t, mid, radius])
    total = len(cases) - 1
    mine = [sc.evaluate_on(*c) for c in cases]
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
        valid = not isinstance(res[0], str) and abs(res[0][0] + 0.340878) < 5e-7 and abs(res[0][1] - 0.382716) < 5e-7
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst_p = worst_d = 0.0
            n = 0
            for (cs, t, mid, radius), got, ref in zip(cases[1:], mine[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                scale_p = sum(abs(c) for c in cs) or 1.0
                scale_d = (sum(k * k * abs(c) for k, c in enumerate(cs)) or 1.0) / radius
                worst_p = max(worst_p, abs(got[0] - ref[0]) / scale_p)
                worst_d = max(worst_d, abs(got[1] - ref[1]) / scale_d)
            entry.update(compared=n, max_value_diff=worst_p, max_derivative_diff=worst_d, limit=LIMIT[name])
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[:1]}", "errors", len(errors), errors[:1], entry.get("max_value_diff"), entry.get("max_derivative_diff"), flush=True)
    L = out["lineages"]
    mine_ok = abs(mine[0][0] + 0.340878) < 5e-7 and abs(mine[0][1] - 0.382716) < 5e-7
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v["max_value_diff"] <= LIMIT[k] and v["max_derivative_diff"] <= LIMIT[k] for k, v in L.items())
    worst = max(max(v.get("max_value_diff") or 0.0, v.get("max_derivative_diff") or 0.0) for v in L.values())
    out["published"] = {"source": "NAIF CSPICE documentation of chbval and chbder: coefficients (1, 3, 0.5, 1, 0.5, -1, 1), midpoint 0.5, radius 3, t = 1: -0.340878 and 0.382716",
                        "star_chebyshev_observed": list(mine[0]), "star_chebyshev_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["CSPICE chbval / chbder (SpiceyPy)", "numpy.polynomial.chebyshev", "mpmath chebyt / chebyu at 40 digits"],
                      "claim": "star_chebyshev evaluates a Chebyshev series and its first derivative on an interval given by midpoint and radius, the convention of SPK ephemeris segments",
                      "crosscheck": f"{total} series of 1 to 40 terms at points of random intervals, ends included: value and derivative agree with CSPICE, NumPy and mpmath at 40 digits within {worst:.1e} "
                                    f"of the natural scale of the sum (sum of |c_k|; sum of k^2 |c_k| / radius)",
                      "benchmark": f"largest scaled difference from mpmath at 40 digits: value {L['mpmath'].get('max_value_diff', 0):.1e}, derivative {L['mpmath'].get('max_derivative_diff', 0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_chebyshev_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, mine[0], "->", dest.name)


if __name__ == "__main__":
    main()
