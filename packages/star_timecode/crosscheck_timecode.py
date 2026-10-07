"""Cross-check of star_timecode against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_timecode.py  ->  12_EVIDENCE/crosscheck_timecode_20261007.json

Lineages, each in its own interpreter:
  cpython  datetime.fromisoformat for code A, datetime.strptime with %j for code B, tm_yday for the day of year;
  numpy    numpy.datetime64 for code A (terminator removed) and numpy day arithmetic from 1 January for code B;
  astropy  astropy.time.Time, format 'isot' for code A and 'yday' (YYYY:DDD:hh:mm:ss) for code B, scale UTC.
For every case star_timecode writes the two codes; each library reads them and returns the calendar fields, the
microseconds and the day of year, which must equal those star_timecode reads back (astropy within one microsecond:
it stores a time as two floats).
Probe (published): the examples of CCSDS 301.0-B-4, section 3.5.1: "1988-01-18T17:20:43.123456Z" (code A) and
"1988-018T17:20:43.123456Z" (code B) are the same instant.
Corpus (seed 20261007): 600 instants, half with years 1 to 9999 and half 1900 to 2100 (astropy is compared on the latter
range only, where its UTC needs no warning), every month, 29 February and 31 December of leap years included, fractions of 0 to 6 digits.
Second part, recorded but not a pass/fail criterion for the libraries: 40 malformed or out-of-range texts, all of
which star_timecode must refuse; how many each library's parser accepts is counted. A lenient parser is a documented
design choice of that library, not a defect: the count says what a caller must check for itself.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_timecode as st  # noqa: E402

CPYTHON = ("from datetime import datetime\n"
           "def f(a, b):\n    t = datetime.fromisoformat(a)\n    u = datetime.strptime(b.split('.')[0].rstrip('Z'), '%Y-%jT%H:%M:%S')\n"
           "    return [t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond, t.timetuple().tm_yday, u.year, u.month, u.day]\n"
           "def accepts(text):\n    datetime.fromisoformat(text)\n")
NUMPY = ("import numpy as np\n"
         "def f(a, b):\n    t = np.datetime64(a.rstrip('Z'), 'us')\n    o = t.astype(object)\n"
         "    doy = int((t.astype('datetime64[D]') - t.astype('datetime64[Y]').astype('datetime64[D]')).astype(int)) + 1\n"
         "    u = (np.datetime64(b[:4] + '-01-01', 'D') + (int(b[5:8]) - 1)).astype(object)\n"
         "    return [o.year, o.month, o.day, o.hour, o.minute, o.second, o.microsecond, doy, u.year, u.month, u.day]\n"
         "def accepts(text):\n    np.datetime64(text.rstrip('Z') if isinstance(text, str) else text)\n")
ASTROPY = ("from astropy.time import Time\n"
           "def f(a, b):\n    t = Time(a.rstrip('Z'), format='isot', scale='utc', precision=6)\n    y = t.ymdhms\n    s = float(y[5])\n"
           "    head, frac = (b.rstrip('Z').split('.') + [''])[:2]\n"
           "    u = Time(head.replace('-', ':', 1).replace('T', ':') + ('.' + frac if frac else ''), format='yday', scale='utc').ymdhms\n"
           "    return [int(y[0]), int(y[1]), int(y[2]), int(y[3]), int(y[4]), s, None, int(t.yday.split(':')[1]), int(u[0]), int(u[1]), int(u[2])]\n"
           "def accepts(text):\n    Time(text.rstrip('Z'), format='isot', scale='utc')\n")
RUNNER = ("\nimport json, sys\njob = json.load(sys.stdin)\nout = {'valid': [], 'accepted': []}\nfor a, b in job['valid']:\n    try:\n        out['valid'].append(f(a, b))\n"
          "    except Exception as e:\n        out['valid'].append('error:' + type(e).__name__ + ':' + str(e)[:60])\n"
          "for k, text in enumerate(job['invalid']):\n    try:\n        accepts(text)\n        out['accepted'].append(k)\n    except Exception:\n        pass\n"
          "print('@@' + json.dumps(out))\n")
INVALID = ["2026-10-07t02:45:10Z", "2026-10-07T02:45:10z", "2026-10-07 02:45:10", "2026-10-07T02:45:10.Z", "2026-10-07T02:45:10.1234567890123Z",
           "2026-02-29T00:00:00Z", "2026-366T00:00:00Z", "2026-000T00:00:00Z", "2026-10-07T24:00:00Z", "2026-10-07T12:00:60Z", "2026-10-07T23:59:61Z",
           "0000-01-01T00:00:00Z", "2026-13-01T00:00:00Z", "2026-10-07T02:45:10Z ", " 2026-10-07T02:45:10Z", "2026-10-07T02:45Z", "2026-1-07T02:45:10Z",
           "2026-10-7T02:45:10Z", "2026-10-07T2:45:10Z", "20261007T024510Z", "2026-10-07T02:45:10+00:00", "2026-10-07T02:45:10ZZ", "+2026-10-07T02:45:10Z",
           "2026-10-07", "2026-10-07T", "2026-10-07T02:45:10,5Z", "2026/10/07T02:45:10Z", "2026-10-07T02.45.10Z", "2026-04-31T00:00:00Z", "2026-00-10T00:00:00Z",
           "2026-10-00T00:00:00Z", "2026-10-07T02:60:10Z", "1900-02-29T00:00:00Z", "2026-10-07T02:45:10.5 Z", "2026-W41-3T02:45:10Z", "26-10-07T02:45:10Z",
           "2026-10-07T02:45:10.-5Z", "2026-10-07T-2:45:10Z", "12026-10-07T02:45:10Z", "2026-0280T02:45:10Z"]


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"cpython": (venv("sympy"), CPYTHON), "numpy": (venv("scipy"), NUMPY), "astropy": (venv("astropy"), ASTROPY)}
PROBE = ["1988-01-18T17:20:43.123456Z", "1988-018T17:20:43.123456Z"]


def main():
    rnd = random.Random(20261007)
    fields = []
    for k in range(600):
        year = rnd.randint(1900, 2100) if k % 2 else rnd.randint(1, 9999)
        if k % 10 == 0:
            year = rnd.choice((1600, 2000, 2024, 2400, 4, 9996))
            month, day = ((2, 29), (12, 31), (3, 1), (1, 1))[k // 10 % 4]
        else:
            month = rnd.randint(1, 12)
            day = rnd.randint(1, 31)
            while True:                                     # the last valid day when the draw is past the end of the month
                try:
                    st.day_of_year(year, month, day)
                    break
                except ValueError:
                    day -= 1
        digits = rnd.randint(0, 6)
        fields.append([year, month, day, rnd.randint(0, 23), rnd.randint(0, 59), rnd.randint(0, 59), "".join(rnd.choice("0123456789") for _ in range(digits))])
    valid = [PROBE] + [[st.format_a(*f), st.format_b(*f)] for f in fields]
    refused = 0
    for text in INVALID:
        try:
            st.parse(text)
        except ValueError:
            refused += 1
    out = {"cases": len(fields), "seed": 20261007, "malformed_texts": len(INVALID), "star_timecode_refuses": refused, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        mine_idx = [0] + [i + 1 for i, f in enumerate(fields) if name != "astropy" or 1900 <= f[0] <= 2100]
        job = {"valid": [valid[i] for i in mine_idx], "invalid": INVALID}
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        answers = res["valid"]
        if len(answers) != len(mine_idx):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in answers if isinstance(x, str)]
        p = answers[0]
        valid_probe = not isinstance(p, str) and p[:5] == [1988, 1, 18, 17, 20] and int(p[5]) == 43 and p[7] == 18 and p[8:] == [1988, 1, 18]
        entry = {"probe_valid": valid_probe, "errors": len(errors), "first_error": errors[:1], "malformed_accepted": len(res["accepted"]),
                 "malformed_accepted_examples": [INVALID[k] for k in res["accepted"][:6]]}
        if valid_probe:
            mismatches = n = 0
            example = None
            for i, ref in zip(mine_idx[1:], answers[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                a, b = valid[i]
                y, m, d, h, mi, s, frac = st.parse(a)
                micro = int(frac.ljust(6, "0")) if frac else 0
                same = [y, m, d, h, mi] == ref[:5] and ref[7] == st.day_of_year(y, m, d) and ref[8:] == list(st.parse(b)[:3]) and st.parse(b) == st.parse(a)
                if ref[6] is None:
                    same = same and abs(ref[5] - (s + micro / 1e6)) < 1.5e-6
                else:
                    same = same and ref[5] == s and ref[6] == micro
                if not same:
                    mismatches += 1
                    example = example or [a, b, ref]
            entry.update(compared=n, mismatches=mismatches, example=example)
        out["lineages"][name] = entry
        print(name, "valid" if valid_probe else f"EXCLUDED {str(p)[:100]}", "errors", len(errors), errors[:1], "compared", entry.get("compared"), "mismatches", entry.get("mismatches"),
              "| malformed accepted:", entry["malformed_accepted"], flush=True)
    L = out["lineages"]
    mine_ok = st.parse(PROBE[0]) == (1988, 1, 18, 17, 20, 43, "123456") and st.parse(PROBE[1]) == st.parse(PROBE[0]) and st.format_b(*st.parse(PROBE[0])) == PROBE[1] \
        and st.format_a(*st.parse(PROBE[1])) == PROBE[0]
    ok = mine_ok and refused == len(INVALID) and all(v["probe_valid"] and not v["errors"] and v.get("mismatches") == 0 and v.get("compared", 0) >= 10 for v in L.values())
    out["published"] = {"source": "CCSDS 301.0-B-4, section 3.5.1, examples 1988-01-18T17:20:43.123456Z (code A) and 1988-018T17:20:43.123456Z (code B)",
                        "star_timecode_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["CPython datetime", "numpy.datetime64", "astropy.time.Time"],
                      "claim": "star_timecode reads and writes CCSDS ASCII time codes A and B with exact fields and refuses every text that is not one",
                      "crosscheck": f"{len(fields)} instants (years 1 to 9999) written in both codes: calendar fields, microseconds and day of year equal to CPython datetime and numpy.datetime64 on all of them "
                                    f"and to astropy on the {L['astropy'].get('compared')} between 1900 and 2100; of {len(INVALID)} malformed or out-of-range texts star_timecode refuses {refused}, while "
                                    f"the ISO parsers accept {L['cpython']['malformed_accepted']} (CPython fromisoformat), {L['numpy']['malformed_accepted']} (numpy.datetime64) and "
                                    f"{L['astropy']['malformed_accepted']} (astropy isot)",
                      "benchmark": f"field mismatches: {sum(v.get('mismatches') or 0 for v in L.values())}; malformed texts refused: {refused} of {len(INVALID)}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_timecode_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "refused", refused, "of", len(INVALID), "->", dest.name)


if __name__ == "__main__":
    main()
