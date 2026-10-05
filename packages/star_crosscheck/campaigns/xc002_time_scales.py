# -*- coding: utf-8 -*-
"""XC-002: TAI-UTC and TT-UTC — star_timescales vs astropy vs pyerfa (ERFA) vs skyfield, each in its own venv,
plus the published IERS value (Bulletin C, leap-second history) as reference.

Lineage note (honest): astropy uses ERFA internally for UTC<->TAI, so astropy and pyerfa are ONE lineage
("IAU SOFA/ERFA"). star_timescales (own table, S.T.A.R.) and skyfield (its own builtin leap-second table) are
separate lineages. Dates chosen around leap seconds, including the day after a leap (the classic off-by-one).
"""
import json
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
PY = lambda n: str(V / n / "Scripts" / "python.exe")  # noqa: E731

STAR_TS = """
from datetime import datetime, timezone
import star_timescales as s
VERSION = '0.2.0'
def compute(i):
    t = datetime.fromisoformat(i['utc']).replace(tzinfo=timezone.utc)
    return [float(s.tai_minus_utc(t)), float(s.tt_minus_utc(t))]
"""
ASTROPY = """
import astropy; VERSION = astropy.__version__
from astropy.time import Time
from datetime import datetime
def _sec(iso):   # civil seconds of an ISO timestamp (calendar arithmetic, no Julian-date floats)
    d = datetime.fromisoformat(iso[:19]); return d.timestamp() + float('0' + iso[19:]) if len(iso) > 19 else d.timestamp()
def compute(i):
    # first version subtracted Julian dates: ~10 us float resolution and a non-uniform UTC JD on leap days
    t = Time(i['utc'], scale='utc', precision=6)
    return [round(_sec(t.tai.isot) - _sec(t.utc.isot), 6), round(_sec(t.tt.isot) - _sec(t.utc.isot), 6)]
"""
PYERFA = """
import erfa; VERSION = erfa.__version__
def compute(i):
    y, m, d = (int(x) for x in i['utc'][:10].split('-'))
    hh, mm, ss = (float(x) for x in i['utc'][11:19].split(':'))
    dat = erfa.dat(y, m, d, (hh * 3600 + mm * 60 + ss) / 86400)
    return [float(dat), float(dat + 32.184)]
"""
SKYFIELD = """
import skyfield; VERSION = skyfield.__version__
from skyfield.api import load
from datetime import datetime, timezone
ts = load.timescale(builtin=True)
def _cal_sec(c):
    y, mo, d, h, mi, s = c
    return datetime(int(y), int(mo), int(d), int(h), int(mi)).replace(tzinfo=timezone.utc).timestamp() + float(s)
def compute(i):
    t = ts.from_datetime(datetime.fromisoformat(i['utc']).replace(tzinfo=timezone.utc))
    u = _cal_sec(t.utc)
    return [round(_cal_sec(t.tai_calendar()) - u, 6), round(_cal_sec(t.tt_calendar()) - u, 6)]
"""

# Published reference: IERS Bulletin C leap-second history (TAI-UTC), TT-TAI = 32.184 s by definition.
CASES = [("1999-06-30T12:00:00", 32), ("2005-12-31T23:59:59", 32), ("2006-01-01T00:00:00", 33),
         ("2012-06-30T23:59:59", 34), ("2012-07-01T00:00:01", 35), ("2016-12-31T23:59:59", 36),
         ("2017-01-01T00:00:00", 37), ("2026-10-03T12:00:00", 37)]

ENGINES = [
    Engine("star_timescales", "S.T.A.R. leap-second table", python=PY("star_timescales_ci"), code=STAR_TS),
    Engine("astropy", "IAU SOFA/ERFA", python=PY("astropy"), code=ASTROPY),
    Engine("pyerfa", "IAU SOFA/ERFA", python=PY("star_timescales_ci"), code=PYERFA),
    Engine("skyfield", "skyfield builtin leap-second table", python=PY("skyfield"), code=SKYFIELD),
]

if __name__ == "__main__":
    out = []
    for utc, dat in CASES:
        b = crosscheck("TAI-UTC, TT-UTC", {"utc": utc}, ENGINES, 1e-6, "s",
                       reference={"value": [dat, dat + 32.184], "source": "IERS Bulletin C leap-second history; TT-TAI = 32.184 s (IAU)"})
        out.append(b)
        print(utc, b["verdict"], {r["engine"]: r.get("value", r.get("error", "")[:60]) for r in b["engines"]},
              "lineages", len(b["independent_lineages"]))
    p = Path(__file__).resolve().parents[1] / "evidence" / "XC-002_time_scales_evidence.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
