"""Runs ccsds_audit on the installed TM decoders and writes 12_EVIDENCE/audit_ccsds_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import ccsds_audit as ca
import frame_drivers as fd

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
SRC_ENV = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES"))   # star_telemetry from source (0.2.3), not a stale venv
IMPLS = {
    "spacepackets": {"command": [str(V / "spacepackets/Scripts/python.exe"), "-c"], "driver": fd.TM_SPACEPACKETS,
                     "lineage": "spacepackets 0.32.0 (robamu, Python)"},
    "star_telemetry": {"command": [str(V / "telemetry_tag_ref/Scripts/python.exe"), "-W", "ignore", "-c"],
                       "driver": fd.TM_STAR_PY, "env": SRC_ENV, "lineage": "star_telemetry 0.2.3 (S.T.A.R., Python)"},
    "star_aos_c": {"command": [str(V / "telemetry_tag_ref/Scripts/python.exe"), "-c"], "driver": fd.TM_STAR_C,
                   "env": dict(os.environ, STAR_AOS_SRC="/mnt/" + str(ROOT)[0].lower() + str(ROOT)[2:].replace(chr(92), "/")
                               + "/08_PROTOTYPES/star_telemetry_c/src"),
                   "lineage": "star_aos C (S.T.A.R., C99, host build in WSL)"},
    # superseded release kept as a control: the audit must catch its known TM defect (fixed in 0.2.3)
    "star_telemetry_0_2_1": {"command": [str(V / "telemetry_clean2_ref/Scripts/python.exe"), "-W", "ignore", "-c"],
                             "driver": fd.TM_STAR_PY, "lineage": "star_telemetry 0.2.1 as installed (superseded control)"},
}
res = ca.audit(IMPLS)
res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
out = ROOT / "12_EVIDENCE" / f"audit_ccsds_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
print({n: {k: (v if isinstance(v, (int, bool)) else len(v)) for k, v in s.items()} for n, s in res["per_impl"].items()})
print("disagreements", len(res["accept_disagreements"]), "->", out.name)
