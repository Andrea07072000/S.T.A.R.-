"""Cross-check of star_wrap against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_wrap.py  ->  12_EVIDENCE/crosscheck_wrap_20261006.json

Lineages, each in its own interpreter:
  erfa     ERFA anp and anpm (C, radians): wrap360 and wrap180, and difference as anpm(a - b);
  astropy  astropy.coordinates.Angle.wrap_at (NumPy, degrees): wrap360, wrap180, difference;
  scipy    scipy.stats.circmean (NumPy): circular_mean.
Probes (published): Meeus, Astronomical Algorithms, Example 25.a: L0 = -2318.19280 deg = 201.80720 deg and
M = -2241.00603 deg = 278.99397 deg. A lineage that does not return them within 1e-9 deg is excluded; scipy is
probed on the mean of (350, 10, 20) = 6.704953 deg, a value derived by hand (atan2 of the summed sines and cosines).
Corpus (seed 20261006): 600 angles (300 within +-720 deg, 200 up to 1e6 deg, 100 within 1e-9 deg of a multiple of 180)
and 600 samples of 2 to 50 angles spread over at most 200 deg.
ERFA works in radians: its answers carry the rounding of the conversion, larger for larger angles; the bound used
for it is 5e-10 deg up to 1e6 deg (one unit in the last place of 1e6 deg in radians is 2e-10 deg, and a difference carries two).
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_wrap as sw  # noqa: E402

PROBE = [-2318.19280, -2241.00603, [350.0, 10.0, 20.0]]
ERFA = ("import erfa, math\nD, R = math.degrees, math.radians\ndef f(a, b, s):\n"
        "    return {'w360': [D(float(erfa.anp(R(a)))), D(float(erfa.anp(R(b))))], 'w180': D(float(erfa.anpm(R(a)))), 'diff': D(float(erfa.anpm(R(a) - R(b))))}\n")
ASTROPY = ("from astropy.coordinates import Angle\nimport astropy.units as u\ndef f(a, b, s):\n"
           "    w = lambda x, at: float(Angle(x, u.deg).wrap_at(at * u.deg).deg)\n"
           "    return {'w360': [w(a, 360), w(b, 360)], 'w180': w(a, 180), 'diff': w(w(a, 360) - w(b, 360), 180)}\n")
SCIPY = "from scipy.stats import circmean\ndef f(a, b, s):\n    return {'mean': float(circmean(s, high=360.0, low=0.0))}\n"
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"erfa": (sys.executable, ERFA), "astropy": (venv("astropy"), ASTROPY), "scipy": (venv("scipy"), SCIPY)}


def circ(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def main():
    rnd = random.Random(20261006)
    cases = [PROBE]

    def angle(k):
        if k < 300:
            return rnd.uniform(-720, 720)
        if k < 500:
            return rnd.uniform(-1e6, 1e6)
        return 180.0 * rnd.randint(-9, 9) + rnd.uniform(-1e-9, 1e-9)

    for k in range(600):
        centre, spread = rnd.uniform(0, 360), rnd.uniform(1, 200)
        cases.append([angle(k), angle(k), [centre + rnd.uniform(-spread / 2, spread / 2) + 360.0 * rnd.randint(-2, 2) for _ in range(rnd.randint(2, 50))]])
    out = {"cases": len(cases) - 1, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        p = res[0]
        if name == "scipy":
            valid = isinstance(p, dict) and abs(p.get("mean", 0.0) - 6.704953) < 1e-6
        else:
            valid = isinstance(p, dict) and len(p.get("w360", [])) == 2 and abs(p["w360"][0] - 201.80720) < 1e-9 and abs(p["w360"][1] - 278.99397) < 1e-9
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"wrap360": None, "wrap180": None, "difference": None, "mean": None}
            out_of_range = n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                if "mean" in x:
                    mine = sw.circular_mean(c[2])
                    m["mean"] = max(m["mean"] or 0.0, circ(mine, x["mean"]))
                    out_of_range += not 0.0 <= mine < 360.0
                else:
                    a, b, d = sw.wrap360(c[0]), sw.wrap180(c[0]), sw.difference(c[0], c[1])
                    out_of_range += not (0.0 <= a < 360.0 and -180.0 <= b < 180.0 and -180.0 <= d < 180.0)
                    m["wrap360"] = max(m["wrap360"] or 0.0, circ(a, x["w360"][0]), circ(sw.wrap360(c[1]), x["w360"][1]))
                    m["wrap180"] = max(m["wrap180"] or 0.0, circ(b, x["w180"]))
                    m["difference"] = max(m["difference"] or 0.0, circ(d, x["diff"]))
            entry.update(compared=n, out_of_range=out_of_range, **{"max_" + k + "_diff_deg": v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:-9]: v for k, v in entry.items() if k.startswith("max_") and v is not None},
              "out of range", entry.get("out_of_range"), flush=True)
    L = out["lineages"]
    E, A, S = L["erfa"], L["astropy"], L["scipy"]
    mine_ok = abs(sw.wrap360(PROBE[0]) - 201.80720) < 1e-9 and abs(sw.wrap360(PROBE[1]) - 278.99397) < 1e-9
    w = [A.get("max_wrap360_diff_deg"), A.get("max_wrap180_diff_deg"), A.get("max_difference_diff_deg"),
         E.get("max_wrap360_diff_deg"), E.get("max_wrap180_diff_deg"), E.get("max_difference_diff_deg"), S.get("max_mean_diff_deg")]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 and v.get("out_of_range") == 0 for v in L.values()) and mine_ok \
        and all(x is not None for x in w) and max(w[:3]) < 1e-9 and max(w[3:6]) < 5e-10 and w[6] < 1e-11
    out["published"] = {"source": "Meeus Example 25.a: -2318.19280 deg = 201.80720 deg; -2241.00603 deg = 278.99397 deg", "star_wrap_reproduces": mine_ok}
    if all(x is not None for x in w):
        out["summary"] = {"ok": ok, "lineages": ["ERFA anp / anpm (C)", "astropy Angle.wrap_at", "scipy.stats.circmean", "Meeus, Astronomical Algorithms, Example 25.a"],
                          "claim": "star_wrap reduces, differences and averages angles as three independent libraries do, and always returns values inside the stated ranges",
                          "crosscheck": f"600 angles up to 1e6 deg (100 within 1e-9 deg of a multiple of 180): within {max(w[:3]):.1e} deg of astropy and {max(w[3:6]):.1e} deg of ERFA "
                                        f"(which rounds through radians); 600 circular means within {w[6]:.1e} deg of SciPy; every result inside its range",
                          "benchmark": f"largest differences: astropy {max(w[:3]):.1e} deg, ERFA {max(w[3:6]):.1e} deg, SciPy mean {w[6]:.1e} deg"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_wrap_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
