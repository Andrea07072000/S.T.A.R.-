"""Cross-check of star_precession against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_precession.py  ->  12_EVIDENCE/crosscheck_precession_20261006.json

Lineages, each in its own interpreter:
  erfa   ERFA pmat76 (the open SOFA, C): the full matrix;
  ephem  PyEphem (libastro): a direction given at epoch J2000 re-expressed at the epoch of date; its own code.
Probe (published): SOFA validation of pmat76 at (2400000.5, 50123.9999): first row 0.9999995504328350733,
0.8696632209480960785e-3, 0.3779153474959888345e-3. ERFA must reproduce it to 1e-14; PyEphem is probed on the
direction of the first axis at that date to 1e-6 rad: it carries its own precession code, measured here to differ
by a fraction of an arcsecond, while a convention error (transposed matrix, wrong sign) would be 1e-3 rad.
Corpus (seed 20261006): 500 dates over 1800-2200; for PyEphem 3 directions per date.
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
import star_precession as sp  # noqa: E402

SOFA_DATE, SOFA_ROW = (2400000.5, 50123.9999), (0.9999995504328350733, 0.8696632209480960785e-3, 0.3779153474959888345e-3)
ERFA = "import erfa\ndef f(d, fr, _):\n    return [[float(x) for x in row] for row in erfa.pmat76(d, fr)]\n"
EPHEM = '''
import ephem, math
def f(d, fr, dirs):
    out = []
    for ra, dec in dirs:
        e = ephem.Equatorial(ra, dec, epoch=ephem.J2000)
        n = ephem.Equatorial(e, epoch=ephem.Date(d + fr - 2415020.0))
        out.append([float(n.ra), float(n.dec)])
    return out
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"erfa": (sys.executable, ERFA), "ephem": (str(ROOT / ".venvs" / "ephem" / "Scripts" / "python.exe"), EPHEM)}


def unit(ra, dec):
    return (math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec))


def angle(a, b):
    c = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    return math.atan2(math.hypot(*c), sum(x * y for x, y in zip(a, b)))


def main():
    rnd = random.Random(20261006)
    cases = [[SOFA_DATE[0], SOFA_DATE[1], [[0.0, 0.0]]]]
    for _ in range(500):
        jd = rnd.uniform(sp.JD_MIN, sp.JD_MAX)
        cases.append([math.floor(jd) + 0.5, rnd.random() * 0.999, [[rnd.uniform(0, 2 * math.pi), math.asin(rnd.uniform(-0.98, 0.98))] for _ in range(3)]])
    out = {"dates": len(cases) - 1, "seed": 20261006, "lineages": {}}
    mine0 = sp.precession_matrix(*SOFA_DATE)
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        worst, compared = 0.0, 0
        if name == "erfa":
            valid = isinstance(res[0], list) and len(res[0]) == 3 and max(abs(a - b) for a, b in zip(res[0][0], SOFA_ROW)) < 1e-14
            for c, x in zip(cases[1:], res[1:]):
                if valid and isinstance(x, list) and len(x) == 3:
                    m = sp.precession_matrix(c[0], c[1])
                    worst = max(worst, max(abs(m[i][j] - x[i][j]) for i in range(3) for j in range(3)))
                    compared += 1
            unit_name = "max_matrix_element_diff"
        else:
            first_axis = tuple(mine0[i][0] for i in range(3))               # image of the J2000 x axis in the frame of date
            valid = isinstance(res[0], list) and len(res[0]) == 1 and angle(unit(*res[0][0]), first_axis) < 1e-6
            for c, x in zip(cases[1:], res[1:]):
                if valid and isinstance(x, list) and len(x) == len(c[2]):
                    for (ra, dec), got in zip(c[2], x):
                        worst = max(worst, angle(sp.mod_from_j2000(unit(ra, dec), c[0], c[1]), unit(*got)))
                        compared += 1
            worst = math.degrees(worst) * 3600.0
            unit_name = "max_direction_diff_arcsec"
        out["lineages"][name] = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1], "compared": compared, unit_name: worst}
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), "compared", compared, unit_name, "%.2e" % worst, flush=True)
    L = out["lineages"]
    pub = max(abs(a - b) for a, b in zip(mine0[0], SOFA_ROW))
    e, p = L["erfa"]["max_matrix_element_diff"], L["ephem"]["max_direction_diff_arcsec"]
    ok = all(v["probe_valid"] and not v["errors"] for v in L.values()) and L["erfa"]["compared"] == 500 and L["ephem"]["compared"] == 1500 \
        and e < 1e-13 and p < 1.0 and pub < 1e-15
    out["published"] = {"source": "SOFA validation of pmat76", "star_precession_first_row_abs_diff": pub}
    out["summary"] = {"ok": ok, "lineages": ["ERFA pmat76 (C, the open SOFA)", "PyEphem libastro epoch conversion", "SOFA validation values of pmat76"],
                      "claim": "star_precession reproduces the IAU 1976 precession of two independent implementations over 1800-2200",
                      "crosscheck": f"500 dates: every matrix element within {e:.1e} of ERFA; 1500 directions within {p:.1e} arcsec of PyEphem; "
                                    f"SOFA validation row reproduced within {pub:.1e}",
                      "benchmark": f"ERFA: max element difference {e:.1e}; PyEphem: max direction difference {p:.2e} arcsec"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_precession_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published diff %.1e" % pub, "->", dest.name)


if __name__ == "__main__":
    main()
