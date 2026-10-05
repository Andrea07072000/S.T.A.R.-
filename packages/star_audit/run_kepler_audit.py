"""Runs kepler_audit on every installed Kepler-equation solver and writes 12_EVIDENCE/audit_kepler_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import frame_drivers as fd
import kepler_audit as ka

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_elements"))
IMPLS = {
    "hapsira": {"command": P("hapsira"), "driver": fd.KEP_HAPSIRA, "lineage": "poliastro / hapsira (numba)"},
    "basilisk": {"command": P("basilisk"), "driver": fd.KEP_BASILISK, "lineage": "Basilisk 2.12 utilities.orbitalMotion (pure Python)"},
    "orekit": {"command": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-c"], "driver": fd.KEP_OREKIT,
               "lineage": "Orekit KeplerianAnomalyUtility (Java)"},
    "spice": {"command": P("spiceypy"), "driver": fd.KEP_SPICE, "lineage": "NAIF CSPICE conics (C from Fortran), E from perifocal state"},
    "star_elements": {"command": ["python", "-c"], "driver": fd.KEP_STAR, "env": ENV,
                      "lineage": "S.T.A.R. star_elements (safeguarded Newton, Vallado Alg. 2 start)"},
}
if __name__ == "__main__":
    os.environ.setdefault("MSYS_NO_PATHCONV", "1")
    res = ka.audit(IMPLS)
    res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
    out = ROOT / "12_EVIDENCE" / f"audit_kepler_{date.today():%Y%m%d}.json"
    out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    print({n: (v["valid"], v["vallado_err_rad"]) for n, v in res["validation"].items()})
    print({n: max(b["max_err_rad"] for b in v.values()) for n, v in res["vs_truth"].items()})
    print({n: sum(b["refused"] for b in v.values()) for n, v in res["vs_truth"].items()})
    print(json.dumps(res["hostile"], indent=1), "->", out.name)
