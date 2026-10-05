"""Runs lambert_audit on every installed Lambert solver and writes 12_EVIDENCE/audit_lambert_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import frame_drivers as fd
import lambert_audit as la

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_lambert"))
IMPLS = {
    "hapsira_izzo": {"command": P("hapsira"), "driver": fd.LAM_HAPSIRA_IZZO, "lineage": "hapsira izzo (Izzo 2015, Householder)"},
    "hapsira_vallado": {"command": P("hapsira"), "driver": fd.LAM_HAPSIRA_VALLADO, "lineage": "hapsira vallado (universal variables, bisection)"},
    "orekit": {"command": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-c"], "driver": fd.LAM_OREKIT,
               "lineage": "Orekit IodLambert (Java)"},
    "star_lambert": {"command": ["python", "-c"], "driver": fd.LAM_STAR, "env": ENV,
                     "lineage": "S.T.A.R. star_lambert (Curtis Alg. 5.2, universal variables)"},
}
if __name__ == "__main__":
    os.environ.setdefault("MSYS_NO_PATHCONV", "1")
    res = la.audit(IMPLS)
    res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
    out = ROOT / "12_EVIDENCE" / f"audit_lambert_{date.today():%Y%m%d}.json"
    out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    print({n: (v["valid"], v["curtis_err_kms"]) for n, v in res["validation"].items()})
    print({n: {e: (round(b["max_err_kms"], 12), b["refused"]) for e, b in v.items()} for n, v in res["vs_truth"].items()})
    print(json.dumps(res["hostile"]), "->", out.name)
