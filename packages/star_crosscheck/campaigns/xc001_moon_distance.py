# -*- coding: utf-8 -*-
"""Campagna XC-001: distanza geocentrica Terra-Luna con motori di lignaggio diverso, ognuno nel suo venv.

Lignaggi: JPL DE440 (SPICE, skyfield, jplephem: UN solo testimone) · ERFA/VSOP87+ELP-like builtin di astropy ·
PyEphem (ELP/Meeus). Tolleranza 50 km: i modelli analitici della Luna non sono a livello di metro; la campagna
misura QUANTO divergono, non lo assume.
"""
import json
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
K = (ROOT / "Space S.T.A.R/02_ORBIT_ASTRODYNAMICS/spice_kernels").as_posix()
PY = lambda n: str(V / n / "Scripts" / "python.exe")  # noqa: E731

SPICE = f"""
import spiceypy as s
VERSION = s.tkvrsn('TOOLKIT')
s.furnsh(r'{K}/naif0012.tls'); s.furnsh(r'{K}/de440s.bsp')
def compute(i):
    et = s.str2et(i['utc'].replace('T', ' ') + ' UTC')   # SPICE non accetta 'T' + ' UTC'
    p, _ = s.spkpos('301', et, 'J2000', 'NONE', '399')
    return (p[0]**2 + p[1]**2 + p[2]**2) ** 0.5
"""
SKYFIELD = f"""
from skyfield.api import load
import skyfield; VERSION = skyfield.__version__
eph = load(r'{K}/de440s.bsp'); ts = load.timescale(builtin=True)
def compute(i):
    from datetime import datetime, timezone
    t = ts.from_datetime(datetime.fromisoformat(i['utc']).replace(tzinfo=timezone.utc))
    return float((eph['moon'] - eph['earth']).at(t).distance().km)
"""
JPLEPHEM = f"""
from jplephem.spk import SPK
import jplephem; VERSION = jplephem.__version__ if hasattr(jplephem,'__version__') else 'jplephem'
k = SPK.open(r'{K}/de440s.bsp')
def compute(i):
    from datetime import datetime, timezone
    d = datetime.fromisoformat(i['utc']).replace(tzinfo=timezone.utc)
    jd_utc = d.timestamp() / 86400.0 + 2440587.5
    # TAI-UTC dalla tabella IERS (Bulletin C): la prima versione usava 37 s fisso -> 5 s di errore nel 2000,
    # trovato DA QUESTA CAMPAGNA (jplephem 0,161 km lontano da skyfield con lo stesso DE440)
    leaps = [(datetime(2017,1,1,tzinfo=timezone.utc),37),(datetime(2015,7,1,tzinfo=timezone.utc),36),
             (datetime(2012,7,1,tzinfo=timezone.utc),35),(datetime(2009,1,1,tzinfo=timezone.utc),34),
             (datetime(2006,1,1,tzinfo=timezone.utc),33),(datetime(1999,1,1,tzinfo=timezone.utc),32)]
    dat = next(v for t, v in leaps if d >= t)
    jd_tdb = jd_utc + (dat + 32.184) / 86400.0           # TT (TDB-TT < 2 ms, trascurabile qui)
    p = k[3, 301].compute(jd_tdb) - k[3, 399].compute(jd_tdb)
    return float((p ** 2).sum() ** 0.5)
"""
ASTROPY = """
import astropy; VERSION = astropy.__version__
from astropy.time import Time
from astropy.coordinates import get_body, solar_system_ephemeris
solar_system_ephemeris.set('builtin')
def compute(i):
    return float(get_body('moon', Time(i['utc'], scale='utc')).distance.to('km').value)
"""
EPHEM = """
import ephem; VERSION = ephem.__version__
def compute(i):
    m = ephem.Moon(i['utc'].replace('T', ' '))
    return float(m.earth_distance * 149597870.7)
"""

ENGINES = [
    Engine("spiceypy", "JPL DE440", python=PY("spiceypy"), code=SPICE),
    Engine("skyfield", "JPL DE440", python=PY("skyfield"), code=SKYFIELD),
    Engine("jplephem", "JPL DE440", python=PY("jplephem"), code=JPLEPHEM),
    Engine("astropy-builtin", "ERFA builtin (analytic)", python=PY("astropy"), code=ASTROPY),
    Engine("pyephem", "PyEphem/libastro (analytic)", python=PY("ephem"), code=EPHEM),
]

if __name__ == "__main__":
    out = []
    for utc in ("2000-01-01T12:00:00", "2026-10-03T00:00:00", "2030-06-15T06:00:00"):
        b = crosscheck("geocentric Moon distance", {"utc": utc}, ENGINES, tolerance=50.0, unit="km")
        out.append(b)
        vals = {r["engine"]: (round(r["value"][0], 3) if r["state"] == "OK" else r["state"]) for r in b["engines"]}
        print(utc, b["verdict"], vals, "lineages:", b["independent_lineages"])
        for p in b["pairs"]:
            print(f"   {p['a']:16} vs {p['b']:16} diff {p['diff']:10.3f} km  same_lineage={p['same_lineage']}")
    Path(__file__).resolve().parents[1].joinpath("evidence", "XC-001_moon_distance_evidence.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    sys.exit(0)
