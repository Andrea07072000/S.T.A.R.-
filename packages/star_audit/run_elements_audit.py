"""Runs elements_audit on every installed rv -> elements implementation and writes 12_EVIDENCE/audit_elements_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import elements_audit as ea
import frame_drivers as fd

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_elements"))
IMPLS = {
    "sgp4_vallado": {"command": P("basilisk"), "driver": fd.EL_SGP4_VALLADO, "lineage": "Vallado C++ rv2coe via python-sgp4 ext"},
    "hapsira": {"command": P("hapsira"), "driver": fd.EL_HAPSIRA, "lineage": "poliastro / hapsira 0.18"},
    "skyfield": {"command": P("skyfield"), "driver": fd.EL_SKYFIELD, "lineage": "skyfield elementslib"},
    "star_elements": {"command": ["python", "-c"], "driver": fd.EL_STAR, "env": ENV, "lineage": "S.T.A.R. star_elements (Curtis Alg. 4.2)"},
}
res = ea.audit(IMPLS)
res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
out = ROOT / "12_EVIDENCE" / f"audit_elements_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
print({n: v["valid"] for n, v in res["validation"].items()})
print({n: max(v["max_dev"].values()) for n, v in res["regular_vs_truth"].items()})
print(json.dumps(res["singular_conventions"]), "->", out.name)
