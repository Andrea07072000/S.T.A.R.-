"""Cross-check of star_moon against three independent ephemerides (S.T.A.R., 2026-10-06).

  python crosscheck_moon.py  ->  12_EVIDENCE/crosscheck_moon_20261006.json

Lineages, each in its own interpreter:
  spice_de440  NAIF CSPICE reading JPL DE440 (numerical integration), geometric position in J2000 rotated to the mean
               equator and equinox of date with ERFA's IAU 1976 precession;
  astropy      astropy get_body("moon") with its built-in analytical ephemeris, in PrecessedGeocentric of date;
  ephem        PyEphem (libastro), astrometric geocentric place with the equinox of date.
Probe (published): Vallado Example 5-3, 1994 April 28 0h: (-134240.626, -311571.590, -126693.785) km. The ephemerides
are precise and the published value comes from the low-precision series, so the probe asks each lineage to be within
the STATED accuracy of the series of that value (0.5 deg, 3000 km): it catches a wrong frame or body, nothing finer.
Corpus (seed 20261006): 2000 dates over 1950-2050 plus the two limits. Measured: angle between the two directions and
difference in distance - this is the real accuracy of the series, to be compared with the stated 0.3 deg / 0.2 deg.
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
import star_moon as sm  # noqa: E402

VALLADO_JD, VALLADO = 2449470.5, (-134240.626, -311571.590, -126693.785)
KERNELS = (ROOT / "Space S.T.A.R" / "02_ORBIT_ASTRODYNAMICS" / "spice_kernels").as_posix()
SPICE = f"KDIR = {KERNELS!r}\n" + '''
import spiceypy as sp, erfa
for k in ("de440s.bsp", "naif0012.tls", "pck00010.tpc"):
    sp.furnsh(KDIR + "/" + k)
def f(jd):
    p, _ = sp.spkpos("MOON", (jd - 2451545.0) * 86400.0, "J2000", "NONE", "EARTH")
    m = erfa.pmat76(jd, 0.0)
    return [float(sum(m[i][j] * p[j] for j in range(3))) for i in range(3)]
'''
ASTROPY = '''
from astropy.time import Time
from astropy.coordinates import get_body, PrecessedGeocentric
import astropy.units as u
def f(jd):
    t = Time(jd, format="jd", scale="tdb")
    c = get_body("moon", t).transform_to(PrecessedGeocentric(equinox=t, obstime=t)).cartesian
    return [float(c.x.to_value(u.km)), float(c.y.to_value(u.km)), float(c.z.to_value(u.km))]
'''
EPHEM = '''
import ephem, math
AU = 149597870.7
def f(jd):
    b = ephem.Moon()
    d = ephem.Date(jd - 2415020.0)
    b.compute(d, epoch=d)
    ra, dec, r = float(b.a_ra), float(b.a_dec), float(b.earth_distance) * AU
    return [r * math.cos(dec) * math.cos(ra), r * math.cos(dec) * math.sin(ra), r * math.sin(dec)]
'''
RUNNER = ("\nimport json, sys\nout = []\nfor jd in json.load(sys.stdin):\n    try:\n        out.append(f(jd))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
V = ROOT / ".venvs"
DRIVERS = {"spice_de440": (sys.executable, SPICE), "astropy": (str(V / "astropy" / "Scripts" / "python.exe"), ASTROPY),
           "ephem": (str(V / "ephem" / "Scripts" / "python.exe"), EPHEM)}


def separation(a, b):
    cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    return (math.degrees(math.atan2(math.hypot(*cross), sum(x * y for x, y in zip(a, b)))), abs(math.hypot(*a) - math.hypot(*b)))


def main():
    rnd = random.Random(20261006)
    dates = [VALLADO_JD, sm.JD_1950, sm.JD_2050] + [round(rnd.uniform(sm.JD_1950, sm.JD_2050), 6) for _ in range(2000)]
    mine = [sm.moon_vector_km(jd) for jd in dates]
    pub = separation(mine[0], VALLADO)
    out = {"dates": len(dates) - 1, "seed": 20261006, "published": {"source": "Vallado Example 5-3", "star_moon_abs_diff_km": max(
        abs(a - b) for a, b in zip(mine[0], VALLADO))}, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(dates), capture_output=True, text=True, timeout=1800)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(dates):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        pa, pd = separation(res[0], VALLADO) if isinstance(res[0], list) and len(res[0]) == 3 else (math.inf, math.inf)
        valid = pa <= 0.5 and pd <= 3000.0
        entry = {"probe_valid": valid, "probe_angle_deg": pa, "probe_distance_diff_km": pd, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            angles, dists = [], []
            for m, x in zip(mine[1:], res[1:]):
                if isinstance(x, list) and len(x) == 3:
                    a, d = separation(m, x)
                    angles.append(a)
                    dists.append(d)
            angles.sort()
            entry.update(compared=len(angles), max_angle_deg=angles[-1], p95_angle_deg=angles[int(0.95 * len(angles))],
                         max_distance_diff_km=max(dists), mean_distance_diff_km=sum(dists) / len(dists))
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1],
              {k: round(v, 4) for k, v in entry.items() if isinstance(v, float)}, flush=True)
    L = out["lineages"]
    worst_a = max(v.get("max_angle_deg", 9.0) for v in L.values())
    worst_d = max(v.get("max_distance_diff_km", 1e9) for v in L.values())
    ok = (all(v["probe_valid"] and not v["errors"] and v.get("compared", 0) >= 2000 for v in L.values())
          and worst_a < 0.5 and worst_d < 3000.0 and out["published"]["star_moon_abs_diff_km"] < 1e-3)
    out["summary"] = {"ok": ok, "lineages": ["JPL DE440 through NAIF CSPICE (numerical integration)", "astropy get_body (built-in analytical ephemeris)",
                                             "PyEphem libastro", "Vallado Example 5-3 printed values"],
                      "claim": "star_moon stays within the accuracy stated for the Almanac series against three independent ephemerides, 1950-2050",
                      "crosscheck": f"{len(dates) - 1} dates: direction within {worst_a:.3f} deg and distance within {worst_d:.0f} km of every ephemeris "
                                    f"(DE440: max {L['spice_de440'].get('max_angle_deg', 9):.3f} deg, 95th percentile "
                                    f"{L['spice_de440'].get('p95_angle_deg', 9):.3f} deg); Vallado Example 5-3 reproduced within "
                                    f"{out['published']['star_moon_abs_diff_km']:.1e} km",
                      "benchmark": "measured accuracy of the series by ephemeris: " + "; ".join(
                          f"{n}: max {v.get('max_angle_deg', 9):.3f} deg, 95 % within {v.get('p95_angle_deg', 9):.3f} deg, distance max "
                          f"{v.get('max_distance_diff_km', 0):.0f} km, mean {v.get('mean_distance_diff_km', 0):.0f} km" for n, v in L.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_moon_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published diff %.1e km" % out["published"]["star_moon_abs_diff_km"], pub, "->", dest.name)


if __name__ == "__main__":
    main()
