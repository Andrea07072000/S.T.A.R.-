"""Runs tdb_audit on every installed TDB - TT implementation and writes 12_EVIDENCE/audit_tdb_<date>.json."""
import json
from datetime import date
from pathlib import Path

import frame_drivers as fd
import tdb_audit as ta

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
PY = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
import os  # noqa: E402
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_tdb"),
           STAR_LSK=str(ROOT / "Space S.T.A.R" / "02_ORBIT_ASTRODYNAMICS" / "spice_kernels" / "naif0012.tls"))
IMPLS = {
    "erfa_dtdb": {"command": PY("astropy"), "driver": fd.TDB_ERFA, "lineage": "SOFA/ERFA dtdb (Fairhead-Bretagnon 1990, 787 terms)"},
    "astropy": {"command": PY("astropy"), "driver": fd.TDB_ASTROPY, "lineage": "SOFA/ERFA dtdb (Fairhead-Bretagnon 1990, 787 terms)"},
    "skyfield": {"command": PY("skyfield"), "driver": fd.TDB_SKYFIELD, "lineage": "skyfield (USNO Circular 179 eq. 2.6)"},
    "spice": {"command": PY("spiceypy"), "driver": fd.TDB_SPICE, "env": ENV, "lineage": "NAIF SPICE DELTET (K sin E)"},
    "star_tdb": {"command": ["python", "-c"], "driver": fd.TDB_STAR, "env": ENV, "lineage": "S.T.A.R. star_tdb"},
    "usno_c179_model": {"command": ["python", "-c"], "driver": fd.TDB_USNO_C179, "lineage": "model: USNO Circular 179 eq. 2.6 written from the paper"},
}
res = ta.audit(IMPLS)
res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
out = ROOT / "12_EVIDENCE" / f"audit_tdb_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
print({n: (round(v["max_dev_from_published_s"] * 1e6, 2), v["valid"]) for n, v in res["validation"].items()})
print({k: round(v["max_s"] * 1e6, 3) for k, v in res["pairs"].items()}, "->", out.name)
