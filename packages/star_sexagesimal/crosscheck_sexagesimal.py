"""Cross-check of star_sexagesimal against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_sexagesimal.py  ->  12_EVIDENCE/crosscheck_sexagesimal_20261006.json

Lineages, each in its own interpreter:
  erfa     ERFA a2af, a2tf (angle -> rounded integer fields), af2a, tf2a (fields -> angle), C. ERFA works in radians,
           so its input is the angle after one more rounding: at an exact tie the last unit may differ by one;
  astropy  astropy.coordinates.Angle: signed_dms / hms (unrounded float seconds) and the parser of strings such as
           "-23d26m21.448s" / "17h48m59.74s" (Python).
Probes (published): 23 deg 26' 21.448" = 23.4392911 deg (IAU 1976 obliquity; Meeus, Astronomical Algorithms, ch. 22 and
Example 13.a) and 17h 48m 59.74s = 267.248917 deg (Meeus Example 13.b). A lineage that does not return them is excluded.
Corpus (seed 20261006): 600 angles in [-360, 360] (100 of them within 1e-9 deg of a whole arcminute, where a field
would show 60 if the rounding were done per field) and 600 sets of fields.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_sexagesimal as sx  # noqa: E402

PROBE = [-23.4392911, 267.248917, "-", 23, 26, 21.448, "+", 17, 48, 59.74]
ERFA = ("import erfa, math\nD, R = math.degrees, math.radians\ndef f(a, b, s1, d, m, s, s2, h, mi, se):\n"
        "    x, y = erfa.a2af(3, R(a)), erfa.a2tf(4, R(b))\n"
        "    return {'dms': [x[0].decode()] + [int(v) for v in x[1].tolist()], 'hms': [y[0].decode()] + [int(v) for v in y[1].tolist()],\n"
        "            'deg': D(float(erfa.af2a(s1, d, m, s))), 'hdeg': D(float(erfa.tf2a(s2, h, mi, se)))}\n")
ASTROPY = ("from astropy.coordinates import Angle\nimport astropy.units as u\ndef f(a, b, s1, d, m, s, s2, h, mi, se):\n"
           "    x, y = Angle(a, u.deg).signed_dms, Angle(abs(b), u.deg).hms\n"
           "    return {'dms_float': [float(x.sign), float(x.d), float(x.m), float(x.s)], 'hms_float': [float(y.h), float(y.m), float(y.s)],\n"
           "            'deg': float(Angle(f'{s1}{d}d{m}m{s!r}s').deg), 'hdeg': float(Angle(f'{s2}{h}h{mi}m{se!r}s').deg)}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"erfa": (sys.executable, ERFA), "astropy": (str(ROOT / ".venvs" / "astropy" / "Scripts" / "python.exe"), ASTROPY)}


def units(fields, scale):
    """Signed count of 10**-decimals seconds in a set of integer fields."""
    n = ((fields[1] * 60 + fields[2]) * 60 + fields[3]) * scale + fields[4]
    return -n if fields[0] == "-" else n


def main():
    rnd = random.Random(20261006)
    cases = [PROBE]
    for k in range(600):
        a = rnd.uniform(-360, 360) if k < 500 else rnd.choice((-1, 1)) * (rnd.randint(0, 21599) / 60.0 + rnd.uniform(-1e-9, 1e-9))
        b = rnd.uniform(-360, 360) if k < 500 else rnd.choice((-1, 1)) * (rnd.randint(0, 1439) / 4.0 + rnd.uniform(-1e-9, 1e-9))
        cases.append([max(-360.0, min(360.0, a)), max(-360.0, min(360.0, b)), rnd.choice("+-"), rnd.randint(0, 359), rnd.randint(0, 59), rnd.uniform(0, 59.999999),
                      rnd.choice("+-"), rnd.randint(0, 23), rnd.randint(0, 59), rnd.uniform(0, 59.999999)])
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
        valid = isinstance(p, dict) and abs(p.get("deg", 0.0) + 23.4392911) < 2e-8 and abs(p.get("hdeg", 0.0) - 267.248917) < 5e-7
        if valid and name == "erfa":
            valid = p["dms"] == ["-", 23, 26, 21, 448] and p["hms"] == ["+", 17, 48, 59, 7401]
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            join = 0.0
            exact = off_by_one = worse = 0
            sec = 0.0
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                join = max(join, abs(sx.dms_to_deg(*c[2:6]) - x["deg"]), abs(sx.hms_to_deg(*c[6:10]) - x["hdeg"]))
                if "dms" in x:
                    for mine, theirs, scale in ((sx.deg_to_dms(c[0], 3), x["dms"], 1000), (sx.deg_to_hms(c[1], 4), x["hms"], 10000)):
                        d = abs(units(mine, scale) - units(theirs, scale))
                        exact, off_by_one, worse = exact + (d == 0 and list(mine) == theirs), off_by_one + (d == 1), worse + (d > 1 or (d == 0 and list(mine) != theirs))
                        if max(mine[2], mine[3], theirs[2], theirs[3]) > 59:
                            worse += 1
                else:
                    s, d, m, se = x["dms_float"]
                    mine = sx.deg_to_dms(c[0], 6)
                    sec = max(sec, abs(units(mine, 10 ** 6) / 1e6 - s * ((d * 60 + m) * 60 + se)))
                    h, mi, se = x["hms_float"]
                    sec = max(sec, abs(abs(units(sx.deg_to_hms(c[1], 6), 10 ** 6)) / 1e6 - ((h * 60 + mi) * 60 + se)))
            entry.update(compared=n, max_fields_to_deg_diff_deg=join)
            if "dms" in p:
                entry.update(split_identical=exact, split_one_unit_apart=off_by_one, split_worse=worse)
            else:
                entry.update(max_split_diff_seconds=sec)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "split" in k or "max" in k}, flush=True)
    L = out["lineages"]
    E, A = L["erfa"], L["astropy"]
    mine_ok = sx.deg_to_dms(-23.4392911, 3) == ("-", 23, 26, 21, 448) and sx.deg_to_hms(267.248917, 4) == ("+", 17, 48, 59, 7401)
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and mine_ok \
        and max(E["max_fields_to_deg_diff_deg"], A["max_fields_to_deg_diff_deg"]) < 1e-12 and E.get("split_worse") == 0 \
        and E.get("split_one_unit_apart", 99) <= 12 and E.get("split_identical", 0) + E.get("split_one_unit_apart", 0) == 1200 \
        and A.get("max_split_diff_seconds", 1.0) < 1e-6
    out["published"] = {"source": "IAU 1976 obliquity 23 deg 26' 21.448\" = 23.4392911 deg; Meeus Example 13.b 17h48m59.74s = 267.248917 deg", "star_sexagesimal_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["ERFA a2af / a2tf / af2a / tf2a (C)", "astropy Angle.signed_dms / hms and string parser", "Meeus, Astronomical Algorithms, ch. 22 and Example 13.b"],
                      "claim": "star_sexagesimal splits and joins angles as two independent libraries do, and never shows 60 in a field",
                      "crosscheck": f"600 angles and 600 sets of fields: fields to degrees within {max(E['max_fields_to_deg_diff_deg'], A['max_fields_to_deg_diff_deg']):.1e} deg; "
                                    f"rounded fields identical to ERFA in {E.get('split_identical')} of 1200 and one last unit apart in {E.get('split_one_unit_apart')} "
                                    f"(ERFA rounds after a radian conversion), never further and never a 60; unrounded seconds within {A.get('max_split_diff_seconds', 0):.1e} s of astropy",
                      "benchmark": f"cases one last unit apart from ERFA: {E.get('split_one_unit_apart')} of 1200"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_sexagesimal_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
