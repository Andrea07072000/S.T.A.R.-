"""Cross-check of star_tle against two independent TLE readers (S.T.A.R., 2026-10-06).

  python crosscheck_tle.py  ->  12_EVIDENCE/crosscheck_tle_20261006.json

Lineages, each in its own interpreter:
  sgp4    python-sgp4 Satrec.twoline2rv (Vallado's reference reader; angles in radians, rates per minute);
  orekit  Orekit TLE (Java; SI units).
Probe (published): the first element set of the SGP4 verification catalogue, satellite 5 (Vanguard 1): inclination
34.2682 deg, eccentricity 0.1859667, mean motion 10.82419157 rev/day as printed on the lines; a reader that returns
other values is excluded.
Corpus: the 29 well-formed element sets of SGP4-VER.TLE (field values), and 174 malformed ones in six kinds derived
from them with a fixed seed (verdicts only: which reader refuses what). Every numeric field of star_tle is compared
with both readers after unit conversion.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent / "star_audit")]
import star_tle as st  # noqa: E402
import tle_audit  # noqa: E402  (corpus of malformed element sets, already published with star_audit)

FIELDS = ("satnum", "epoch_year", "epoch_day", "ndot_over_2", "nddot_over_6", "bstar", "inclination_deg", "raan_deg", "eccentricity",
          "argp_deg", "mean_anomaly_deg", "mean_motion_rev_day", "rev_number", "element_number")
SGP4 = '''
import math
from sgp4.api import Satrec
XPDOTP = 1440.0 / (2.0 * math.pi)
def f(l1, l2):
    s = Satrec.twoline2rv(l1, l2)
    d = math.degrees
    year = s.epochyr + (2000 if s.epochyr < 57 else 1900)
    return {"satnum": s.satnum, "epoch_year": year, "epoch_day": s.epochdays, "ndot_over_2": s.ndot * XPDOTP * 1440.0,
            "nddot_over_6": s.nddot * XPDOTP * 1440.0 * 1440.0, "bstar": s.bstar, "inclination_deg": d(s.inclo), "raan_deg": d(s.nodeo),
            "eccentricity": s.ecco, "argp_deg": d(s.argpo), "mean_anomaly_deg": d(s.mo), "mean_motion_rev_day": s.no_kozai * XPDOTP,
            "rev_number": s.revnum, "element_number": s.elnum}
'''
OREKIT = '''
import math
import orekit_jpype
orekit_jpype.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data
setup_orekit_data("/root/orekit-data.zip", from_pip_library=False)
from org.orekit.propagation.analytical.tle import TLE
from org.orekit.time import TimeScalesFactory
def f(l1, l2):
    if not TLE.isFormatOK(l1, l2):
        raise ValueError("TLE.isFormatOK false")
    t = TLE(l1, l2)
    d = math.degrees
    c = t.getDate().getComponents(TimeScalesFactory.getUTC())
    day = c.getDate().getDayOfYear() + c.getTime().getSecondsInUTCDay() / 86400.0
    return {"satnum": t.getSatelliteNumber(), "epoch_year": c.getDate().getYear(), "epoch_day": day,
            "ndot_over_2": t.getMeanMotionFirstDerivative() * 86400.0 ** 2 / (2 * math.pi) / 2.0,
            "nddot_over_6": t.getMeanMotionSecondDerivative() * 86400.0 ** 3 / (2 * math.pi) / 6.0, "bstar": t.getBStar(),
            "inclination_deg": d(t.getI()), "raan_deg": d(t.getRaan()), "eccentricity": t.getE(), "argp_deg": d(t.getPerigeeArgument()),
            "mean_anomaly_deg": d(t.getMeanAnomaly()), "mean_motion_rev_day": t.getMeanMotion() * 86400.0 / (2 * math.pi),
            "rev_number": t.getRevolutionNumberAtEpoch(), "element_number": t.getElementNumber()}
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__)\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"sgp4": ([str(ROOT / ".venvs" / "sgp4" / "Scripts" / "python.exe"), "-W", "ignore", "-c"], SGP4),
           "orekit": (["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-W", "ignore", "-c"], OREKIT)}
PROBE = {"inclination_deg": 34.2682, "eccentricity": 0.1859667, "mean_motion_rev_day": 10.82419157, "satnum": 5}


def main():
    valid = tle_audit.base_tles(HERE / "fixtures" / "SGP4-VER.TLE")
    bad = [c for c in tle_audit.corpus() if c["kind"] != "valid"]
    cases = [list(p) for p in valid] + [[c["l1"], c["l2"]] for c in bad]
    mine = [st.parse(*p) for p in valid]
    verdict = {}
    for c in bad:
        try:
            st.parse(c["l1"], c["l2"])
            verdict.setdefault(c["kind"], [0, 0])[0] += 1
        except st.TleError:
            verdict.setdefault(c["kind"], [0, 0])[1] += 1
    out = {"valid_sets": len(valid), "malformed_sets": len(bad), "star_tle_accepted_refused_by_kind": verdict, "lineages": {}}
    for name, (cmd, driver) in DRIVERS.items():
        r = subprocess.run(cmd + [driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=1800)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        p = res[0]
        ok = isinstance(p, dict) and all(abs(p[k] - v) <= 1e-9 for k, v in PROBE.items())
        entry = {"probe_valid": ok, "errors": sum(isinstance(x, str) for x in res[:len(valid)])}
        if ok:
            worst = {k: 0.0 for k in FIELDS}
            for m, x in zip(mine, res[:len(valid)]):
                if isinstance(x, str):
                    continue
                if set(FIELDS) - set(x):
                    raise SystemExit(f"{name}: an answer lacks fields")
                for k in FIELDS:
                    scale = max(abs(m[k]), 1e-300) if k in ("ndot_over_2", "nddot_over_6", "bstar") and m[k] else 1.0
                    worst[k] = max(worst[k], abs(m[k] - x[k]) / scale)
            entry["max_field_diff"] = worst
            entry["max_diff"] = max(worst.values())
            acc = {}
            for c, x in zip(bad, res[len(valid):]):
                acc.setdefault(c["kind"], [0, 0])[0 if isinstance(x, dict) else 1] += 1
            entry["accepted_refused_by_kind"] = acc
        out["lineages"][name] = entry
        print(name, "valid" if ok else "EXCLUDED", "errors", entry["errors"], "max field diff %.1e" % entry.get("max_diff", math.nan),
              entry.get("accepted_refused_by_kind"), flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_tle_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("star_tle", verdict, "->", dest.name)


if __name__ == "__main__":
    main()
