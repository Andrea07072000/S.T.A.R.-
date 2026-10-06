"""Cross-check of star_epoch against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_epoch.py  ->  12_EVIDENCE/crosscheck_epoch_20261006.json

Lineages, each in its own interpreter:
  erfa      ERFA epj, epb, epj2jd, epb2jd (C): the four functions;
  skyfield  Time.J and Timescale.J (Python): Julian epochs only, both directions;
  spice     SPICE constants b1900, b1950, j1900, j1950, j2100 (C): five fixed points, both kinds of epoch.
Probes (published): B1950.0 = JD 2433282.4235 and J1950.0 = JD 2433282.5 (Lieske 1979; Meeus, Astronomical
Algorithms, ch. 21). A lineage whose value for its probe is further than 5e-5 day is excluded.
Corpus (seed 20261006): 600 dates over 1600-2400 with a random fraction and 600 epochs over 1600-2400.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_epoch as ep  # noqa: E402

B1950, J1950 = 2433282.4235, 2433282.5
ERFA = ("import erfa\ndef f(jd, fr, e):\n"
        "    return {'epj': float(erfa.epj(jd, fr)), 'epb': float(erfa.epb(jd, fr)), 'j2jd': [float(x) for x in erfa.epj2jd(e)],\n"
        "            'b2jd': [float(x) for x in erfa.epb2jd(e)]}\n")
SKYFIELD = ("from skyfield.api import load\nts = load.timescale(builtin=True)\ndef f(jd, fr, e):\n"
            "    return {'epj': float(ts.tt_jd(jd, fr).J), 'j2jd': [float(ts.J(e).tt), 0.0]}\n")
SPICE = ("import spiceypy as sp\ndef f(jd, fr, e):\n"
         "    return {'fixed': {'B1900': sp.b1900(), 'B1950': sp.b1950(), 'J1900': sp.j1900(), 'J1950': sp.j1950(), 'J2100': sp.j2100()}}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"erfa": (sys.executable, ERFA), "skyfield": (venv("skyfield"), SKYFIELD), "spice": (venv("spiceypy"), SPICE)}


def jd_diff(mine, other):
    """Difference in days between two two-part dates, summed so that the large parts cancel first."""
    return abs((mine[0] - other[0]) + (mine[1] - other[1]))


def probe(name, x):
    if not isinstance(x, dict):
        return False
    if name == "erfa":
        return len(x.get("b2jd", [])) == 2 and abs(sum(x["b2jd"]) - B1950) < 5e-5
    if name == "skyfield":
        return len(x.get("j2jd", [])) == 2 and abs(sum(x["j2jd"]) - J1950) < 5e-5
    return abs(x.get("fixed", {}).get("B1950", 0.0) - B1950) < 5e-5 and len(x["fixed"]) == 5


def main():
    rnd = random.Random(20261006)
    cases = [[2433282.5, 0.0, 1950.0]] + [[float(rnd.randint(2305447, 2597641)) + 0.5, rnd.uniform(0, 1), rnd.uniform(1600.0, 2400.0)] for _ in range(600)]
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
        valid = probe(name, res[0])
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"epj": None, "epb": None, "j2jd": None, "b2jd": None, "fixed": None}
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                if "epj" in x:
                    m["epj"] = max(m["epj"] or 0.0, abs(ep.julian_epoch(c[0], c[1]) - x["epj"]))
                if "epb" in x:
                    m["epb"] = max(m["epb"] or 0.0, abs(ep.besselian_epoch(c[0], c[1]) - x["epb"]))
                if "j2jd" in x:
                    m["j2jd"] = max(m["j2jd"] or 0.0, jd_diff(ep.jd_from_julian_epoch(c[2]), x["j2jd"]))
                if "b2jd" in x:
                    m["b2jd"] = max(m["b2jd"] or 0.0, jd_diff(ep.jd_from_besselian_epoch(c[2]), x["b2jd"]))
            if "fixed" in res[0]:
                fx = res[0]["fixed"]
                m["fixed"] = max(jd_diff((ep.jd_from_besselian_epoch if k[0] == "B" else ep.jd_from_julian_epoch)(float(k[1:])), (v, 0.0)) for k, v in fx.items())
            entry.update(compared=n, max_julian_epoch_diff_yr=m["epj"], max_besselian_epoch_diff_yr=m["epb"], max_jd_from_julian_diff_day=m["j2jd"],
                         max_jd_from_besselian_diff_day=m["b2jd"], max_fixed_point_diff_day=m["fixed"])
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if "max" in k and v is not None}, flush=True)
    L = out["lineages"]
    mine = abs(sum(ep.jd_from_besselian_epoch(1950.0)) - B1950)
    E, S, C = L["erfa"], L["skyfield"], L["spice"]
    need = [E.get("max_julian_epoch_diff_yr"), E.get("max_besselian_epoch_diff_yr"), E.get("max_jd_from_julian_diff_day"), E.get("max_jd_from_besselian_diff_day"),
            S.get("max_julian_epoch_diff_yr"), S.get("max_jd_from_julian_diff_day"), C.get("max_fixed_point_diff_day")]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and all(x is not None for x in need) \
        and max(need[0], need[1], need[4]) < 1e-11 and max(need[2], need[3]) < 1e-10 and need[5] < 2e-9 and need[6] < 1e-8 and mine < 5e-5
    out["published"] = {"source": "B1950.0 = JD 2433282.4235 (Lieske 1979; Meeus ch. 21)", "star_epoch_abs_diff_day": mine}
    if all(x is not None for x in need):
        out["summary"] = {"ok": ok, "lineages": ["ERFA epj / epb / epj2jd / epb2jd (C)", "skyfield Time.J / Timescale.J (Julian epochs)",
                                                 "SPICE b1900 / b1950 / j1900 / j1950 / j2100", "Lieske 1979: B1950.0 = JD 2433282.4235"],
                          "claim": "star_epoch converts Julian and Besselian epochs to and from Julian Dates as three independent libraries do",
                          "crosscheck": f"600 dates and 600 epochs over 1600-2400: epochs within {max(need[0], need[1]):.1e} yr of ERFA and Julian epochs within "
                                        f"{need[4]:.1e} yr of skyfield; dates within {max(need[2], need[3]):.1e} day of ERFA and {need[5]:.1e} day of skyfield "
                                        f"(one float there); five SPICE fixed points within {need[6]:.1e} day; B1950.0 within {mine:.1e} day of the printed value",
                          "benchmark": "Besselian epochs have one full library lineage (ERFA) plus two SPICE fixed points; Julian epochs have two (ERFA, skyfield) plus three SPICE fixed points"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_epoch_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published diff %.1e day" % mine, "->", dest.name)


if __name__ == "__main__":
    main()
