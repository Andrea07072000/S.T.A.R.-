# -*- coding: utf-8 -*-
"""leapsec_audit — how time libraries convert UTC to TAI across leap seconds (S.T.A.R., 2026-10-04).

Truth: TAI = UTC + DeltaAT from IERS Bulletin C, written out by hand for each probe (including instants INSIDE the
leap second 23:59:60.x, where TAI = next day 00:00:(DeltaAT_old + x)). Each library is driven ONLY through its
documented UTC-string -> TAI-string API, in its own interpreter. Outcome per probe: OK (string equal to truth to the
ms) · WRONG (different TAI) · REJECTED (library refuses the instant) · PAST_TABLE (date beyond the library's leap
table: no truth exists; we record whether the library warns). Lesson from a first, invalid probe (IMPROVEMENT_LOG
2026-10-04 16:10): never derive TAI-UTC from MJD differences across a 86401-s day.
"""
from __future__ import annotations

import json
import subprocess
from typing import Dict

from audit_guard import driver_rows  # one result row per case, or a declared error (2026-10-06)

PROBES = [  # (UTC ISO, truth TAI ISO or None when the date is beyond any published leap table)
    ("2016-12-31T23:59:59.500", "2017-01-01T00:00:35.500"),
    ("2016-12-31T23:59:60.500", "2017-01-01T00:00:36.500"),
    ("2017-01-01T00:00:00.500", "2017-01-01T00:00:37.500"),
    ("1972-06-30T23:59:60.000", "1972-07-01T00:00:10.000"),
    ("1972-07-01T00:00:00.000", "1972-07-01T00:00:11.000"),
    ("1999-06-01T00:00:00.000", "1999-06-01T00:00:32.000"),
    ("2035-01-01T00:00:00.000", None),
]

DRIVERS = {
    "erfa": (
        "import erfa\n"
        "def to_tai(s):\n"
        "    d, t = s.split('T'); y, m, dd = map(int, d.split('-')); hh, mm, ss = t.split(':')\n"
        "    u1, u2 = erfa.dtf2d('UTC', y, m, dd, int(hh), int(mm), float(ss))\n"
        "    a1, a2 = erfa.utctai(u1, u2)\n"
        "    y, m, dd, f = erfa.d2dtf('TAI', 3, a1, a2)\n"
        "    return '%04d-%02d-%02dT%02d:%02d:%02d.%03d' % (y, m, dd, f[0], f[1], f[2], f[3])\n"),
    "astropy": (
        "from astropy.time import Time\n"
        "def to_tai(s):\n"
        "    return Time(s, scale='utc', format='isot', precision=3).tai.isot\n"),
    "skyfield": (
        "from skyfield.api import load\n"
        "ts = load.timescale()\n"
        "def to_tai(s):\n"
        "    d, t = s.split('T'); y, m, dd = map(int, d.split('-')); hh, mm, ss = t.split(':')\n"
        "    y2, m2, d2, H, M, S = ts.utc(y, m, dd, int(hh), int(mm), float(ss)).tai_calendar()\n"
        "    S = round(S, 3)\n"
        "    return '%04d-%02d-%02dT%02d:%02d:%06.3f' % (y2, m2, d2, H, M, S)\n"),
}

RUNNER = ("\nimport json, sys, warnings\nout = []\nfor s in json.loads(sys.stdin.read()):\n"
          "    with warnings.catch_warnings(record=True) as w:\n        warnings.simplefilter('always')\n"
          "        try:\n            out.append({'tai': to_tai(s), 'warned': bool(w)})\n"
          "        except Exception as e:\n            out.append({'error': type(e).__name__ + ': ' + str(e)[:80], 'warned': bool(w)})\n"
          "print(json.dumps(out))\n")


def classify(truth, res) -> str:
    if "error" in res:
        return "REJECTED"
    if truth is None:
        return "PAST_TABLE_WARNED" if res["warned"] else "PAST_TABLE_SILENT"
    return "OK" if res["tai"] == truth else "WRONG"


def audit(python_exe: str, driver: str) -> Dict:
    r = subprocess.run([python_exe, "-c", driver + RUNNER], input=json.dumps([p for p, _ in PROBES]),
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"library run failed: {r.stderr[-300:]}")
    res = driver_rows(r.stdout, len(PROBES))
    rows = [{"utc": p, "truth": t, **x, "verdict": classify(t, x)} for (p, t), x in zip(PROBES, res)]
    return {"rows": rows, "summary": {v: sum(r["verdict"] == v for r in rows) for v in sorted({r["verdict"] for r in rows})}}
