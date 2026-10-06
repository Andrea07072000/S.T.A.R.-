"""Cross-check of star_units against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_units.py  ->  12_EVIDENCE/crosscheck_units_20261006.json

Lineages, each in its own interpreter:
  scipy    scipy.constants (the NIST / CODATA table of conversion factors) and scipy.constants.convert_temperature;
  astropy  astropy.units with the imperial system enabled (its own unit definitions and its temperature equivalencies).
           It has no kgf and no atm: pairs with those are compared with SciPy only.
Probes (published, exact by definition): SciPy on 1 lbf = 4.4482216152605 N (NIST SP 811: the pound 0.45359237 kg times
standard gravity 9.80665 m/s2); astropy on 1 in = 0.0254 m and 1 au = 149597870700 m (IAU 2012 B2).
Corpus: EVERY ordered pair of units of the same dimension (no sampling), and every ordered pair of temperature units
at seven temperatures.
Known before writing this file: astropy builds lbf from a slug rounded to 32.174049 lb and holds the BTU to nine digits,
so its lbf, slug, psi, hp, ft*lbf, lbf*s and BTU differ from the exact definitions by up to 2e-8 relative. Those
pairs are compared with their own, looser bound and counted; every other pair must agree to rounding.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_units as su  # noqa: E402

SCIPY_NAMES = {"m": "1", "km": "kilo", "cm": "centi", "mm": "milli", "in": "inch", "ft": "foot", "yd": "yard", "mi": "mile", "nmi": "nautical_mile", "au": "au",
               "ly": "light_year", "pc": "parsec", "kg": "1", "g": "gram", "t": "metric_ton", "lb": "pound", "oz": "oz", "slug": "slug", "s": "1", "min": "minute",
               "h": "hour", "day": "day", "week": "week", "julian_year": "Julian_year", "N": "1", "kN": "kilo", "lbf": "lbf", "kgf": "kgf", "dyn": "dyn", "Pa": "1",
               "kPa": "kilo", "MPa": "mega", "bar": "bar", "atm": "atm", "psi": "psi", "torr": "torr", "rad": "1", "deg": "degree", "arcmin": "arcmin",
               "arcsec": "arcsec", "mas": "arcsec * milli", "rev": "2 * pi", "m/s": "1", "km/s": "kilo", "km/h": "kmh", "mph": "mph", "kn": "knot", "ft/s": "foot",
               "J": "1", "kJ": "kilo", "MJ": "mega", "Wh": "hour", "kWh": "kilo * hour", "eV": "eV", "cal": "calorie", "BTU": "Btu", "erg": "erg",
               "ft*lbf": "foot * lbf", "W": "1", "kW": "kilo", "hp": "hp", "N*s": "1", "lbf*s": "lbf", "kN*s": "kilo"}
ASTROPY_NAMES = {"m": "m", "km": "km", "cm": "cm", "mm": "mm", "in": "inch", "ft": "ft", "yd": "yd", "mi": "mi", "nmi": "nmi", "au": "AU", "ly": "lyr", "pc": "pc",
                 "kg": "kg", "g": "g", "t": "t", "lb": "lb", "oz": "oz", "slug": "slug", "s": "s", "min": "min", "h": "h", "day": "d", "week": "wk",
                 "julian_year": "yr", "N": "N", "kN": "kN", "lbf": "lbf", "dyn": "dyn", "Pa": "Pa", "kPa": "kPa", "MPa": "MPa", "bar": "bar", "psi": "psi",
                 "torr": "Torr", "rad": "rad", "deg": "deg", "arcmin": "arcmin", "arcsec": "arcsec", "mas": "mas", "rev": "cycle", "m/s": "m/s", "km/s": "km/s",
                 "km/h": "km/h", "mph": "mi/h", "kn": "kn", "ft/s": "ft/s", "J": "J", "kJ": "kJ", "MJ": "MJ", "Wh": "W h", "kWh": "kW h", "eV": "eV", "cal": "cal",
                 "BTU": "BTU", "erg": "erg", "ft*lbf": "ft lbf", "W": "W", "kW": "kW", "hp": "hp", "N*s": "N s", "lbf*s": "lbf s", "kN*s": "kN s"}
ASTROPY_ROUNDED = {"lbf", "slug", "psi", "hp", "ft*lbf", "lbf*s", "BTU"}
TEMP_SCIPY = {"K": "Kelvin", "degC": "Celsius", "degF": "Fahrenheit", "degR": "Rankine"}
TEMP_ASTROPY = {"K": "K", "degC": "deg_C", "degF": "deg_F", "degR": "deg_R"}
SCIPY = ("import scipy.constants as sc\nNS = {k: getattr(sc, k) for k in dir(sc)}\nN = %r\nT = %r\n"
         "def f(kind, v, a, b):\n"
         "    if kind == 't':\n        return float(sc.convert_temperature(v, T[a], T[b]))\n"
         "    return v * float(eval(N[a], NS)) / float(eval(N[b], NS))\n") % (SCIPY_NAMES, TEMP_SCIPY)
ASTROPY = ("import astropy.units as u\nfrom astropy.units import imperial\nu.add_enabled_units(imperial)\nN = %r\nT = %r\n"
           "def f(kind, v, a, b):\n"
           "    if kind == 't':\n        return float((v * u.Unit(T[a])).to_value(u.Unit(T[b]), equivalencies=u.temperature()))\n"
           "    if a not in N or b not in N:\n        return None\n"
           "    return float((v * u.Unit(N[a])).to_value(u.Unit(N[b])))\n") % (ASTROPY_NAMES, TEMP_ASTROPY)
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"scipy": (str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), SCIPY), "astropy": (str(ROOT / ".venvs" / "astropy" / "Scripts" / "python.exe"), ASTROPY)}


def main():
    assert set(SCIPY_NAMES) == set(su.UNITS), "the SciPy table must name every unit"
    cases = [["u", 1.0, "lbf", "N"], ["u", 1.0, "in", "m"], ["u", 1.0, "au", "m"]]
    dims = sorted({d for d, _ in su.UNITS.values()})
    for d in dims:
        names = su.units(d)
        cases += [["u", 1.0, a, b] for a in names for b in names if a != b]
    temps = [0.0, 1.0, 100.0, 273.15, 300.0, 1234.5, 5772.0]
    kelvin_pairs = [["t", k, a, b] for a in su.TEMPERATURES for b in su.TEMPERATURES if a != b for k in temps]
    for c in kelvin_pairs:                                  # the same seven temperatures expressed in the source unit
        c[1] = su.convert_temperature(c[1], "K", c[2])
    cases += kelvin_pairs
    out = {"unit_pairs": len(cases) - 3 - len(kelvin_pairs), "temperature_cases": len(kelvin_pairs), "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        if name == "scipy":
            valid = res[0] == 4.4482216152605
        else:
            valid = isinstance(res[1], float) and abs(res[1] / 0.0254 - 1.0) < 1e-15 and res[2] == 149597870700.0
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            exact = rounded = temp = 0.0
            n = n_rounded = n_temp = skipped = 0
            worst = None
            for c, x in zip(cases[3:], res[3:]):
                if isinstance(x, str):
                    continue
                if x is None:
                    skipped += 1
                    continue
                if c[0] == "t":
                    n_temp += 1
                    temp = max(temp, abs(su.convert_temperature(c[1], c[2], c[3]) - x))
                    continue
                d = abs(su.convert(c[1], c[2], c[3]) / x - 1.0)
                if name == "astropy" and (c[2] in ASTROPY_ROUNDED or c[3] in ASTROPY_ROUNDED):
                    n_rounded += 1
                    rounded = max(rounded, d)
                else:
                    n += 1
                    if d > exact:
                        exact, worst = d, c[2] + " -> " + c[3]
            entry.update(pairs_compared=n, max_rel_diff=exact, worst_pair=worst, pairs_with_a_unit_the_library_rounds=n_rounded, max_rel_diff_on_those=rounded,
                         pairs_the_library_lacks=skipped, temperature_cases=n_temp, max_temperature_diff_K=temp)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[:3]}", "errors", len(errors), errors[:1], {k: v for k, v in entry.items() if k not in ("probe_valid", "errors", "first_error")}, flush=True)
    L = out["lineages"]
    S, A = L["scipy"], L["astropy"]
    total = out["unit_pairs"]
    mine_ok = su.convert(1.0, "lbf", "N") == 4.4482216152605 and su.convert(1.0, "in", "m") == 0.0254 and su.convert(1.0, "au", "m") == 149597870700.0
    ok = all(v["probe_valid"] and not v["errors"] for v in L.values()) and mine_ok and S.get("pairs_compared") == total and S.get("max_rel_diff", 1.0) < 1e-15 \
        and A.get("pairs_compared", 0) + A.get("pairs_with_a_unit_the_library_rounds", 0) + A.get("pairs_the_library_lacks", 0) == total \
        and A.get("max_rel_diff", 1.0) < 1e-15 and A.get("max_rel_diff_on_those", 1.0) < 5e-8 \
        and max(S.get("max_temperature_diff_K", 1.0), A.get("max_temperature_diff_K", 1.0)) < 1e-9
    out["published"] = {"source": "NIST SP 811: 1 lbf = 4.4482216152605 N; 1 in = 0.0254 m; IAU 2012 B2: 1 au = 149597870700 m", "star_units_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["scipy.constants (NIST / CODATA factors)", "astropy.units with imperial units", "NIST SP 811, SI Brochure, IAU 2012 B2 (exact definitions)"],
                      "claim": "star_units converts between every pair of its units as two independent libraries do, and where they differ it follows the exact definitions",
                      "crosscheck": f"all {total} ordered pairs of units of the same dimension: within {S.get('max_rel_diff', 0):.1e} relative of SciPy on every pair; within "
                                    f"{A.get('max_rel_diff', 0):.1e} of astropy on {A.get('pairs_compared')} pairs, and within {A.get('max_rel_diff_on_those', 0):.1e} on the "
                                    f"{A.get('pairs_with_a_unit_the_library_rounds')} pairs with a unit astropy holds rounded (lbf, slug, psi, hp, ft*lbf, lbf*s, BTU); "
                                    f"{A.get('pairs_the_library_lacks')} pairs involve kgf or atm, which astropy lacks; {out['temperature_cases']} temperature conversions within "
                                    f"{max(S.get('max_temperature_diff_K', 0), A.get('max_temperature_diff_K', 0)):.1e} K of both",
                      "benchmark": f"SciPy {S.get('max_rel_diff', 0):.1e} (worst pair {S.get('worst_pair')}); astropy {A.get('max_rel_diff', 0):.1e} / {A.get('max_rel_diff_on_those', 0):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_units_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "exact definitions reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
