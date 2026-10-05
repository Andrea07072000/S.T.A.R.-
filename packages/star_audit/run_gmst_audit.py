"""Runs gmst_audit on every installed GMST implementation and writes 12_EVIDENCE/audit_gmst_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import frame_drivers as fd
import gmst_audit as ga

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_sidereal"))
IMPLS = {
    "erfa_gmst82": {"command": P("astropy"), "driver": fd.GMST_ERFA82, "lineage": "SOFA/ERFA gmst82 (IAU 1982)"},
    "erfa_gmst06": {"command": P("astropy"), "driver": fd.GMST_ERFA06, "lineage": "SOFA/ERFA gmst06 (IAU 2006)"},
    "astropy": {"command": P("astropy"), "driver": fd.GMST_ASTROPY, "lineage": "SOFA/ERFA gmst06 (IAU 2006)"},
    "skyfield": {"command": P("skyfield"), "driver": fd.GMST_SKYFIELD, "lineage": "skyfield (IAU 2006, own code)"},
    "sgp4_gstime": {"command": P("basilisk"), "driver": fd.GMST_SGP4, "lineage": "Vallado C++ via python-sgp4 (IAU 1982)"},
    "pyorbital": {"command": P("pyorbital"), "driver": fd.GMST_PYORBITAL, "lineage": "pyorbital (IAU 1982, own code)"},
    "star_sidereal": {"command": ["python", "-c"], "driver": fd.GMST_STAR, "env": ENV, "lineage": "S.T.A.R. star_sidereal (IAU 1982)"},
}
res = ga.audit(IMPLS)
res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
out = ROOT / "12_EVIDENCE" / f"audit_gmst_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
print({n: (round(v["vallado_err_arcsec"], 5), v["valid"]) for n, v in res["validation"].items()})
print({k: round(v["max_arcsec"], 5) for k, v in res["pairs"].items()}, "->", out.name)
