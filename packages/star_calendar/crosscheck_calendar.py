"""Cross-check of star_calendar against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_calendar.py  ->  12_EVIDENCE/crosscheck_calendar_20261006.json

Lineages, each in its own interpreter:
  erfa      ERFA/SOFA cal2jd and jd2cal (proleptic Gregorian, C);
  datetime  CPython datetime.date.toordinal / fromordinal (proleptic Gregorian, years 1-9999; JDN = ordinal + 1721425);
  spice     NAIF CSPICE str2et with the MIXED calendar selected (Julian before 1582-10-05, Gregorian after), including
            years B.C.: the only one of the three that knows the Julian calendar and the 1582 switch.
Probe (published, Meeus, Astronomical Algorithms, ch. 7): noon of 2000-01-01 is JD 2451545, of 1957-10-04 is 2436116,
of 1582-10-15 is 2299161 (each lineage on the dates it covers); spice also 333-01-27 (Julian) = 1842713.
Corpus (seed 20261006): 3000 random dates per lineage over its whole range plus every day from 1582-09-25 to
1582-10-25 for spice. Compared: the Julian Day Number, and the date recovered from it (erfa, datetime).
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_calendar as cal  # noqa: E402

KERNELS = (ROOT / "Space S.T.A.R" / "02_ORBIT_ASTRODYNAMICS" / "spice_kernels").as_posix()
ERFA = "import erfa\ndef f(y, m, d):\n    a, b = erfa.cal2jd(y, m, d)\n    n = int(round(float(a) + float(b) + 0.5))\n" \
       "    yy, mm, dd, _ = erfa.jd2cal(float(n), 0.0)\n    return [n, int(yy), int(mm), int(dd)]\n"
DATETIME = "import datetime\ndef f(y, m, d):\n    n = datetime.date(y, m, d).toordinal() + 1721425\n" \
           "    b = datetime.date.fromordinal(n - 1721425)\n    return [n, b.year, b.month, b.day]\n"
SPICE = f"KDIR = {KERNELS!r}\n" + '''
import spiceypy as sp
sp.furnsh(KDIR + "/naif0012.tls")
sp.timdef("SET", "CALENDAR", 10, "MIXED")        # the default is proleptic GREGORIAN: the probe on year 333 showed it
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
def f(y, m, d):
    era = f"{y} A.D." if y > 0 else f"{1 - y} B.C."
    et = sp.str2et(f"{era} {MONTHS[m - 1]} {d} 12:00:00 TDB")
    return [int(round(2451545.0 + et / 86400.0))]
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__)\nprint('@@' + json.dumps(out))\n")
PROBES = {"erfa": [((2000, 1, 1), 2451545), ((1957, 10, 4), 2436116), ((1582, 10, 15), 2299161)],
          "datetime": [((2000, 1, 1), 2451545), ((1957, 10, 4), 2436116), ((1582, 10, 15), 2299161)],
          "spice": [((2000, 1, 1), 2451545), ((1957, 10, 4), 2436116), ((1582, 10, 15), 2299161), ((333, 1, 27), 1842713)]}
SETUP = {"erfa": (ERFA, "gregorian", -4700), "datetime": (DATETIME, "gregorian", 1), "spice": (SPICE, "auto", -4700)}


def dates(calendar, first_year, rnd):
    out = []
    while len(out) < 3000:
        y, m, d = rnd.randint(first_year, 9999), rnd.randint(1, 12), rnd.randint(1, 31)
        try:
            cal.jdn(y, m, d, calendar)
            out.append([y, m, d])
        except ValueError:
            pass
    if calendar == "auto":
        out += [[1582, 9, d] for d in range(25, 31)] + [[1582, 10, d] for d in (1, 2, 3, 4, 15, 16, 20, 25)]
    return out


def main():
    rnd = random.Random(20261006)
    out = {"seed": 20261006, "lineages": {}}
    for name, (driver, calendar, first) in SETUP.items():
        cases = [list(p[0]) for p in PROBES[name]] + dates(calendar, first, rnd)
        r = subprocess.run([sys.executable, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        k = len(PROBES[name])
        valid = all(isinstance(x, list) and x and x[0] == p[1] for x, p in zip(res[:k], PROBES[name]))
        errors = sum(isinstance(x, str) for x in res)
        wrong_jdn = wrong_date = compared = 0
        if valid:
            for c, x in zip(cases[k:], res[k:]):
                if isinstance(x, str):
                    continue
                compared += 1
                n = cal.jdn(*c, calendar)
                wrong_jdn += n != x[0]
                if len(x) == 4:
                    wrong_date += list(cal.calendar_date(x[0], calendar)) != x[1:]
        out["lineages"][name] = {"probe_valid": valid, "errors": errors, "calendar": calendar, "compared": compared,
                                 "jdn_mismatches": wrong_jdn, "date_mismatches": wrong_date}
        print(name, "valid" if valid else f"EXCLUDED {res[:k]}", "errors", errors, "compared", compared, "jdn mismatches", wrong_jdn,
              "date mismatches", wrong_date, flush=True)
    L = out["lineages"]
    ok = all(v["probe_valid"] and not v["errors"] and v["compared"] >= 3000 and not v["jdn_mismatches"] and not v["date_mismatches"] for v in L.values())
    out["summary"] = {"ok": ok, "lineages": ["ERFA cal2jd / jd2cal (C)", "CPython datetime ordinals", "NAIF CSPICE str2et, MIXED calendar",
                                             "Meeus, Astronomical Algorithms, chapter 7 examples"],
                      "claim": "star_calendar gives the same Julian Day Number as three independent implementations over its whole range",
                      "crosscheck": "; ".join(f"{n} ({v['calendar']}): {v['compared']} dates, {v['jdn_mismatches']} day-number and "
                                              f"{v['date_mismatches']} date mismatches" for n, v in L.items())
                                    + "; spice covers the Julian calendar, years B.C. and the days around the 1582 switch",
                      "benchmark": "exact integer arithmetic: mismatches are counted, not measured; " + ", ".join(
                          f"{n} {v['jdn_mismatches']}/{v['compared']}" for n, v in L.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_calendar_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "->", dest.name)


if __name__ == "__main__":
    main()
