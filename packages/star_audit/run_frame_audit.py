"""Runs frame_audit on every installed implementation and writes 12_EVIDENCE/audit_frames_<date>.json."""
import json
import sys
from datetime import date
from pathlib import Path

import frame_audit as fa
import frame_drivers as fd

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
IMPLS = {
    "astropy": {"command": [str(V / "astropy/Scripts/python.exe"), "-W", "ignore", "-c"], "driver": fd.ASTROPY,
                "lineage": "astropy/ERFA (IAU 2006/2000A, CIO)"},
    "skyfield": {"command": [str(V / "skyfield/Scripts/python.exe"), "-c"], "driver": fd.SKYFIELD,
                 "lineage": "skyfield (IAU 2000A/2006, equinox)"},
    "vallado_fk5": {"command": [str(V / "astropy/Scripts/python.exe"), "-W", "ignore", "-c"], "driver": fd.VALLADO_FK5,
                    "lineage": "Vallado TEME->J2000, IAU-1976/1980 (FK5) via ERFA primitives"},
    "vallado_fk5_bias": {"command": [str(V / "astropy/Scripts/python.exe"), "-W", "ignore", "-c"],
                         "driver": fd.VALLADO_FK5_BIAS, "lineage": "as vallado_fk5 + IAU 2000 frame bias (ERFA bp00)"},
    "orekit": {"command": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-c"], "driver": fd.OREKIT,
               "lineage": "Orekit 13.1 (Java, IERS 2010)"},
}
only = sys.argv[1:] or list(IMPLS)
res = fa.audit({k: IMPLS[k] for k in only})
res["implementations"] = {k: IMPLS[k]["lineage"] for k in only}
out = ROOT / "12_EVIDENCE" / f"audit_frames_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res["validation"]))
print({k: (None if v["max_m"] is None else round(v["max_m"], 4), v["n"]) for k, v in res["pairs"].items()})
print({k: len(v) for k, v in res["refused"].items()}, "->", out.name)
