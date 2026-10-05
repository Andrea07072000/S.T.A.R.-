"""Runs packet_audit on the installed CCSDS Space Packet decoders and writes 12_EVIDENCE/audit_packets_<date>.json."""
import json
import os
from datetime import date
from pathlib import Path

import frame_drivers as fd
import packet_audit as pa

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / ".venvs"
P = lambda n: [str(V / n / "Scripts/python.exe"), "-W", "ignore", "-c"]
SRC = dict(os.environ, PYTHONPATH=str(ROOT / "08_PROTOTYPES"))       # star_telemetry from source, not a stale venv
IMPLS = {
    "spacepackets": {"command": P("spacepackets"), "driver": fd.PKT_SPACEPACKETS, "lineage": "spacepackets 0.32 (robamu)"},
    "ccsdspy": {"command": P("ccsdspy"), "driver": fd.PKT_CCSDSPY, "lineage": "ccsdspy 2.0.1 (NASA/astropy community)"},
    "star_telemetry": {"command": P("telemetry_tag_claude"), "driver": fd.PKT_STAR, "env": SRC, "lineage": "S.T.A.R. star_telemetry"},
}
res = pa.audit(IMPLS)
res["implementations"] = {k: v["lineage"] for k, v in IMPLS.items()}
out = ROOT / "12_EVIDENCE" / f"audit_packets_{date.today():%Y%m%d}.json"
out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
for n, v in res["per_impl"].items():
    print(n, v["validated"], v["accepted"])
print("->", out.name)
