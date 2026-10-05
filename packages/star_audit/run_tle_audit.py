"""Runs tle_audit on the installed TLE readers and writes 12_EVIDENCE/audit_tle_<date>.json."""
import json
from datetime import date
from pathlib import Path

import frame_drivers as fd
import tle_audit as ta

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
IMPLS = {
    "sgp4_twoline2rv": {"command": P("basilisk"), "driver": fd.TLE_SGP4_API, "lineage": "python-sgp4 2.x Satrec.twoline2rv (Vallado C++)"},
    "skyfield": {"command": P("skyfield"), "driver": fd.TLE_SKYFIELD, "lineage": "skyfield EarthSatellite (uses python-sgp4)"},
    "pyorbital": {"command": P("pyorbital"), "driver": fd.TLE_PYORBITAL, "lineage": "pyorbital tlefile.Tle"},
    "orekit": {"command": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-c"], "driver": fd.TLE_OREKIT,
               "lineage": "Orekit 13.1 TLE (Java) with isFormatOK"},
}
res = ta.audit(IMPLS)
res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
out = ROOT / "12_EVIDENCE" / f"audit_tle_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
for n, v in res["per_impl"].items():
    print(n, v["validated"], v["accepted"])
print("->", out.name)
