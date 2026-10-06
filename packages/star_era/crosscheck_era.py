"""Cross-check of star_era against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_era.py  ->  12_EVIDENCE/crosscheck_era_20261006.json

Lineages, each in its own interpreter:
  erfa      ERFA (the open SOFA): era00 and gmst06, C;
  skyfield  skyfield.earthlib.earth_rotation_angle (pure Python, own code); it has no IAU 2006 GMST, so only ERA.
Probe (published): the SOFA validation values era00(2400000.5, 54388.0) = 0.4022837240028158102 rad and
gmst06(2400000.5, 53736.0, 2400000.5, 53736.0) = 1.754174971870091203 rad; a lineage that misses its probe by more
than 1e-9 rad (a convention error, not rounding) is excluded; star_era itself must match to 1e-12 rad.
Corpus (seed 20261006): 1000 dates uniform over 1800-2200 as (integer day + .5, fraction) pairs; TT = UT1 + 69.184 s.
Compared in arcseconds on the circle.
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
import star_era as se  # noqa: E402

DT = 69.184 / 86400.0
ERFA = f"DT = {DT!r}\n" + "import erfa\ndef f(d, fr):\n    return [float(erfa.era00(d, fr)), float(erfa.gmst06(d, fr, d, fr + DT))]\n"
SKY = "import math\nfrom skyfield.earthlib import earth_rotation_angle\ndef f(d, fr):\n    return [float(earth_rotation_angle(d, fr)) * 2 * math.pi, None]\n"
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"erfa": (sys.executable, ERFA), "skyfield": (str(ROOT / ".venvs" / "skyfield" / "Scripts" / "python.exe"), SKY)}
PROBE_ERA = ([2400000.5, 54388.0], 0.4022837240028158102)
PROBE_GMST = ([2400000.5, 53736.0], 1.754174971870091203)


def arcsec(a_deg, b_rad):
    return abs((a_deg - math.degrees(b_rad) + 180.0) % 360.0 - 180.0) * 3600.0


def main():
    rnd = random.Random(20261006)
    cases = [PROBE_ERA[0], PROBE_GMST[0]] + [[math.floor(rnd.uniform(se.JD_MIN, se.JD_MAX - 1)) + 0.5, rnd.random()] for _ in range(1000)]
    out = {"dates": len(cases) - 2, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = isinstance(res[0], list) and len(res[0]) == 2 and abs(res[0][0] - PROBE_ERA[1]) < 1e-9
        if name == "erfa":                               # the GMST probe is run with TT = UT1, as in the SOFA validation
            g = subprocess.run([py, "-c", "import erfa; print(repr(float(erfa.gmst06(2400000.5, 53736.0, 2400000.5, 53736.0))))"],
                               capture_output=True, text=True)
            valid = valid and abs(float(g.stdout) - PROBE_GMST[1]) < 1e-12
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            d_era = d_gmst = 0.0
            n_gmst = 0
            for c, x in zip(cases[2:], res[2:]):
                if isinstance(x, str):
                    continue
                d_era = max(d_era, arcsec(se.era_deg(*c), x[0]))
                if x[1] is not None:
                    d_gmst = max(d_gmst, arcsec(se.gmst06_deg(c[0], c[1], c[0], c[1] + DT), x[1]))
                    n_gmst += 1
            entry.update(max_era_diff_arcsec=d_era, max_gmst06_diff_arcsec=d_gmst if n_gmst else None, gmst_cases=n_gmst)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), {k: v for k, v in entry.items() if "diff" in k}, flush=True)
    L = out["lineages"]
    mine_era = abs(math.radians(se.era_deg(*PROBE_ERA[0])) - PROBE_ERA[1])
    mine_gmst = abs(math.radians(se.gmst06_deg(*PROBE_GMST[0], *PROBE_GMST[0])) - PROBE_GMST[1])
    era = max(v.get("max_era_diff_arcsec", 1.0) for v in L.values())
    gmst = L["erfa"].get("max_gmst06_diff_arcsec") or 1.0
    ok = all(v["probe_valid"] and not v["errors"] for v in L.values()) and era < 1e-5 and gmst < 1e-6 and mine_era < 1e-12 and mine_gmst < 1e-12
    out["published"] = {"source": "SOFA validation values", "star_era_abs_diff_rad": mine_era, "star_gmst06_abs_diff_rad": mine_gmst}
    out["summary"] = {"ok": ok, "lineages": ["ERFA era00 / gmst06 (C, the open SOFA)", "Skyfield earth_rotation_angle (pure Python)",
                                             "SOFA validation values for era00 and gmst06"],
                      "claim": "star_era reproduces the IAU 2000 Earth Rotation Angle and the IAU 2006 GMST of two independent implementations",
                      "crosscheck": f"{len(cases) - 2} dates over 1800-2200: ERA within {era:.1e} arcsec of ERFA and Skyfield, GMST 2006 within {gmst:.1e} "
                                    f"arcsec of ERFA; SOFA validation values reproduced within {mine_era:.1e} rad (ERA) and {mine_gmst:.1e} rad (GMST)",
                      "benchmark": "largest difference by lineage: " + "; ".join(
                          f"{n}: ERA {v.get('max_era_diff_arcsec', float('nan')):.1e} arcsec" + (f", GMST {v['max_gmst06_diff_arcsec']:.1e} arcsec"
                                                                                            if v.get("max_gmst06_diff_arcsec") is not None else "")
                          for n, v in L.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_era_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", out["published"], "->", dest.name)


if __name__ == "__main__":
    main()
