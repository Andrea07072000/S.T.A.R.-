"""Runs propagation_audit on every installed two-body propagator and writes 12_EVIDENCE/audit_propagation_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import frame_drivers as fd
import propagation_audit as la

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_elements"))
IMPLS = {
    "hapsira_farnocchia": {"command": P("hapsira"), "driver": fd.PROP_HAPSIRA_FARNOCCHIA, "lineage": "hapsira farnocchia (mean-anomaly, near-parabolic safe)"},
    "hapsira_vallado": {"command": P("hapsira"), "driver": fd.PROP_HAPSIRA_VALLADO, "lineage": "hapsira vallado (universal variables, Newton)"},
    "orekit": {"command": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-c"], "driver": fd.PROP_OREKIT,
               "lineage": "Orekit KeplerianPropagator (Java)"},
    "spice": {"command": P("spiceypy"), "driver": fd.PROP_SPICE, "lineage": "NAIF CSPICE prop2b (C from Fortran, universal variables)"},
    "star_kepler": {"command": ["python", "-c"], "driver": fd.PROP_STAR_KEPLER,
                    "env": dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES" / "star_kepler")),
                    "lineage": "S.T.A.R. star_kepler (universal variables, bracketed Newton)"},
    "star_elements": {"command": ["python", "-c"], "driver": fd.PROP_STAR, "env": ENV,
                     "lineage": "S.T.A.R. star_elements (elements + bracketed Newton)"},
}
if __name__ == "__main__":
    os.environ.setdefault("MSYS_NO_PATHCONV", "1")
    res = la.audit(IMPLS)
    res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
    out = ROOT / "12_EVIDENCE" / f"audit_propagation_{date.today():%Y%m%d}.json"
    out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    print({n: (v["valid"], v["vallado_pos_err_km"]) for n, v in res["validation"].items()})
    print({n: {k: (float("%.3g" % b["max_pos_err_km"]), b["refused"]) for k, b in v.items() if b["max_pos_err_km"] > 1e-6 or b["refused"]} for n, v in res["vs_truth"].items()})
    print({n: max(b["max_pos_err_km"] for b in v.values()) for n, v in res["vs_truth"].items()})
    print(json.dumps(res["hostile"]), "->", out.name)
