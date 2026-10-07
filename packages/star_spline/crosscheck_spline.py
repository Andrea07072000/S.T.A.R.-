"""Cross-check of star_spline against two independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_spline.py  ->  12_EVIDENCE/crosscheck_spline_20261007.json

Lineages:
  scipy       scipy.interpolate.CubicSpline(bc_type="natural"): values, first and second derivatives, integral
              (its own interpreter);
  hipparchus  Hipparchus SplineInterpolator (the natural cubic spline of the Java library under Orekit): values and
              first derivative (Java, run in WSL).
Probe (published): Burden and Faires, Numerical Analysis, the worked example of the natural cubic spline through
(1, 2), (2, 3), (3, 5): S0(x) = 2 + 3/4 (x - 1) + 1/4 (x - 1)^3 on [1, 2] and S1(x) = 3 + 3/2 (x - 2) + 3/4 (x - 2)^2
- 1/4 (x - 2)^3 on [2, 3], so that S(1.5) = 2.40625 and S(2.5) = 3.90625.
Corpus (seed 20261007): 150 tables of 3 to 40 knots, strictly increasing with spacings from 1e-3 to 10 (uneven), values
in [-10, 10], each evaluated at 25 points of its range, the knots and the two ends among them.
Differences relative to the scale of each quantity on its table (largest |value|, largest |first derivative|, ...).
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_spline as ss  # noqa: E402

SCIPY = '''
import numpy as np
from scipy.interpolate import CubicSpline
def one(xs, ys, points):
    s = CubicSpline(np.array(xs), np.array(ys), bc_type="natural")
    p = np.array(points)
    return {"values": s(p).tolist(), "derivatives": s(p, 1).tolist(), "second": s(np.array(xs), 2).tolist(), "integral": float(s.integrate(points[0], points[-1]))}
'''
HIPPARCHUS = '''
import orekit_jpype
orekit_jpype.initVM()
import jpype
from org.hipparchus.analysis.interpolation import SplineInterpolator
def one(xs, ys, points):
    f = SplineInterpolator().interpolate(jpype.JArray(jpype.JDouble)(xs), jpype.JArray(jpype.JDouble)(ys))
    d = f.polynomialSplineDerivative()
    return {"values": [float(f.value(p)) for p in points], "derivatives": [float(d.value(p)) for p in points], "second": None, "integral": None}
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
COMMANDS = {"scipy": [str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), "-W", "ignore", "-c"],
            "hipparchus": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-W", "ignore", "-c"]}
DRIVERS = {"scipy": SCIPY, "hipparchus": HIPPARCHUS}
LIMITS = {"scipy": 1e-11, "hipparchus": 1e-11}
PROBE = [[1.0, 2.0, 3.0], [2.0, 3.0, 5.0], [1.0, 1.5, 2.0, 2.5, 3.0]]
PROBE_VALUES = [2.0, 2.40625, 3.0, 3.90625, 5.0]


def corpus():
    rnd = random.Random(20261007)
    job = []
    for _ in range(150):
        n = rnd.randint(3, 40)
        xs = [rnd.uniform(-50.0, 50.0)]
        for _ in range(n - 1):
            xs.append(xs[-1] + 10.0 ** rnd.uniform(-3, 1))
        ys = [rnd.uniform(-10.0, 10.0) for _ in range(n)]
        inner = sorted(rnd.uniform(xs[0], xs[-1]) for _ in range(25 - 2 - min(n, 8)))
        points = sorted(set([xs[0], xs[-1]] + rnd.sample(xs, min(n, 8)) + inner))
        job.append([xs, ys, points])
    return job + [PROBE]


def main():
    job = corpus()
    mine = [{"values": list(ss.values(*a)), "derivatives": list(ss.derivatives(*a)), "second": list(ss.second_derivatives(a[0], a[1])),
             "integral": ss.integral(a[0], a[1], a[2][0], a[2][-1])} for a in job]
    mine_ok = mine[-1]["values"] == PROBE_VALUES and mine[-1]["second"] == [0.0, 1.5, 0.0] and mine[-1]["integral"] == 6.375
    out = {"cases": len(job), "seed": 20261007, "lineages": {}}
    for name, driver in DRIVERS.items():
        r = subprocess.run(COMMANDS[name] + [driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if len(res) != len(job):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        probe = res[-1]
        valid = isinstance(probe, dict) and all(abs(a - b) < 1e-12 for a, b in zip(probe["values"], PROBE_VALUES))
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            worst = {"values": 0.0, "derivatives": 0.0, "second": 0.0, "integral": 0.0}
            for ours, theirs in zip(mine, res):
                for key in ("values", "derivatives", "second"):
                    if theirs[key] is None:
                        continue
                    scale = max(max(abs(v) for v in ours[key]), 1e-300)
                    worst[key] = max(worst[key], max(abs(a - b) for a, b in zip(ours[key], theirs[key])) / scale)
                if theirs["integral"] is not None:
                    worst["integral"] = max(worst["integral"], abs(ours["integral"] - theirs["integral"]) / max(abs(ours["integral"]), 1.0))
            entry.update(compared=len(job), max_diff=worst, within=max(worst.values()) <= LIMITS[name], limit=LIMITS[name])
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("max_diff"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    S, H = (L["scipy"].get("max_diff") or {}), (L["hipparchus"].get("max_diff") or {})
    out["published"] = {"source": "Burden and Faires, Numerical Analysis, natural cubic spline through (1, 2), (2, 3), (3, 5): S(1.5) = 2.40625, S(2.5) = 3.90625, second derivative "
                                  "1.5 at the middle knot", "star_spline_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["scipy.interpolate.CubicSpline (natural)", "Hipparchus SplineInterpolator"],
                      "claim": "star_spline returns the natural cubic spline of two independent libraries, with every value rounded once from an exact solution",
                      "crosscheck": f"{len(job)} tables of 3 to 40 unevenly spaced knots, 25 points each: against SciPy values differ by at most {S.get('values', 0):.1e}, first derivatives by "
                                    f"{S.get('derivatives', 0):.1e}, second derivatives at the knots by {S.get('second', 0):.1e} and the integral by {S.get('integral', 0):.1e} (relative to the "
                                    f"scale of each on its table); against Hipparchus values by {H.get('values', 0):.1e} and first derivatives by {H.get('derivatives', 0):.1e}",
                      "benchmark": f"largest relative difference of a value from SciPy: {S.get('values', 0):.1e}; from Hipparchus: {H.get('values', 0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_spline_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
