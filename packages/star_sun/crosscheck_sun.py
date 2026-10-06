"""Cross-check of star_sun.sun_vector_au against three independent ephemerides (S.T.A.R., 2026-10-06).

  python crosscheck_sun.py  ->  12_EVIDENCE/crosscheck_sun_20261006.json

Lineages, each in its own interpreter:
  spice_de440  NAIF CSPICE reading JPL DE440 (numerically integrated ephemeris), geometric and apparent (LT+S)
               position in J2000, rotated to the mean equator and equinox of date with ERFA's IAU 1976 precession;
  astropy      astropy get_sun (ERFA epv00 analytical series, apparent) expressed in PrecessedGeocentric of date;
  ephem        PyEphem (libastro, VSOP87), astrometric geocentric place with the equinox of date.
Corpus: 402 dates, the two limits 1950-01-01 and 2050-01-01 plus 400 from a fixed seed. Every lineage is first PROBED
on the published value (Vallado, Example 5-1, 2006 April 2 0h: 0.9771945, 0.1924424, 0.0834308 AU, MOD): within
0.01 deg and 1e-4 AU, or it is excluded. Measured: angle between the two Sun directions (deg), distance difference.
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
import star_sun  # noqa: E402

VALLADO_JD, VALLADO = 2453827.5, (0.9771945, 0.1924424, 0.0834308)
KERNELS = ROOT / "Space S.T.A.R" / "02_ORBIT_ASTRODYNAMICS" / "spice_kernels"
SPICE = ("import spiceypy as sp, erfa, datetime\n"
         "for k in ('de440s.bsp', 'naif0012.tls', 'pck00010.tpc'):\n    sp.furnsh(KDIR + '/' + k)\n"
         "def f(jd):\n"
         "    utc = datetime.datetime(2000, 1, 1, 12) + datetime.timedelta(days=jd - 2451545.0)\n"
         "    et = sp.str2et(utc.strftime('%Y-%m-%dT%H:%M:%S.%f'))\n"
         "    p, _ = sp.spkpos('SUN', et, 'J2000', ABCORR, 'EARTH')\n"
         "    m = erfa.pmat76(jd, 0.0)\n"
         "    au = 149597870.7\n"
         "    return [float(sum(m[i][j] * p[j] for j in range(3)) / au) for i in range(3)]\n")
DRIVERS = {
    "spice_de440_geometric": (sys.executable, f"KDIR = {KERNELS.as_posix()!r}\nABCORR = 'NONE'\n" + SPICE),
    "spice_de440_apparent": (sys.executable, f"KDIR = {KERNELS.as_posix()!r}\nABCORR = 'LT+S'\n" + SPICE),
    "astropy": (str(ROOT / ".venvs" / "astropy" / "Scripts" / "python.exe"),
                "from astropy.time import Time\nfrom astropy.coordinates import get_sun, PrecessedGeocentric\nimport astropy.units as u\n"
                "def f(jd):\n    t = Time(jd, format='jd', scale='utc')\n"
                "    c = get_sun(t).transform_to(PrecessedGeocentric(equinox=t, obstime=t)).cartesian\n"
                "    return [float(c.x.to_value(u.au)), float(c.y.to_value(u.au)), float(c.z.to_value(u.au))]\n"),
    "ephem": (str(ROOT / ".venvs" / "ephem" / "Scripts" / "python.exe"),
              "import ephem, math\ndef f(jd):\n    s = ephem.Sun()\n    d = ephem.Date(jd - 2415020.0)\n    s.compute(d, epoch=d)\n"
              "    ra, dec, r = float(s.a_ra), float(s.a_dec), float(s.earth_distance)\n"
              "    return [r * math.cos(dec) * math.cos(ra), r * math.cos(dec) * math.sin(ra), r * math.sin(dec)]\n"),
}
RUNNER = ("\nimport json, sys\nout = []\nfor jd in json.load(sys.stdin):\n    try:\n        out.append(f(jd))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def separation(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    return math.degrees(math.atan2(math.sqrt(sum(x * x for x in cross)), sum(x * y for x, y in zip(a, b)))), abs(na - nb)


def corpus():
    rnd = random.Random(20261006)
    return [VALLADO_JD, star_sun.JD_1950, star_sun.JD_2050] + [round(rnd.uniform(star_sun.JD_1950, star_sun.JD_2050), 6) for _ in range(400)]


def main():
    dates = corpus()
    mine = [star_sun.sun_vector_au(jd) for jd in dates]
    ang, dist = separation(mine[0], VALLADO)
    out = {"dates": len(dates) - 1, "seed": 20261006,
           "published": {"source": "Vallado, Example 5-1", "star_sun_angle_deg": ang, "star_sun_distance_diff_au": dist}, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(dates), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        errors = [x for x in res if isinstance(x, str)]
        if len(res) != len(dates):
            raise SystemExit(f"{name}: {len(res)} answers for {len(dates)} dates")
        pa, pd = separation(res[0], VALLADO) if isinstance(res[0], list) else (math.inf, math.inf)
        valid = pa <= 0.01 and pd <= 1e-4
        entry = {"probe_valid": valid, "probe_angle_deg": pa, "probe_distance_diff_au": pd, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            decades = {}
            for jd, m, x in zip(dates[1:], mine[1:], res[1:]):
                if isinstance(x, list):
                    a, d = separation(m, x)
                    key = f"{1950 + 10 * min(9, int((jd - star_sun.JD_1950) / 3652.5))}s"
                    old = decades.get(key, (0.0, 0.0))
                    decades[key] = (max(old[0], a), max(old[1], d))
            entry["max_angle_deg_by_decade"] = {k: v[0] for k, v in sorted(decades.items())}
            entry["max_angle_deg"] = max(v[0] for v in decades.values())
            entry["max_distance_diff_au"] = max(v[1] for v in decades.values())
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "probe %.5f deg" % pa, "errors", len(errors), errors[:1],
              "max %.5f deg, %.2e AU" % (entry["max_angle_deg"], entry["max_distance_diff_au"]) if valid else "", flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_sun_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("published example: star_sun angle %.6f deg, distance diff %.2e AU ->" % (ang, dist), dest.name)


if __name__ == "__main__":
    main()
