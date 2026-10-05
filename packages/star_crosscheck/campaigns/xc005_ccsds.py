# -*- coding: utf-8 -*-
"""XC-005: CCSDS Space Packet Primary Header Decoding Crosscheck.

Standards:
- CCSDS 133.0-B-2 (Space Packet Protocol)
- Primary header: 6 octets (APID 11-bit, Sequence Count 14-bit, Length 16-bit).

Engines:
1. star_telemetry (S.T.A.R. native engine)
2. spacepackets (Sat-RS / Python spacepackets library)
3. ccsdspy (Astropy affiliated ccsdspy package)

Lineages:
- "S.T.A.R. native": star_telemetry
- "Sat-RS / spacepackets": spacepackets
- "IAU / Astropy ccsdspy": ccsdspy

Fixtures:
- Canonical CCSDS 133.0-B-2 packets
- NASA JPL Europa Clipper ECM authentic space telemetry fixture (europa_clipper_ecm_raw2.bin)

Quantity: [apid, sequence_count, total_packet_length_bytes]
"""

import json
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / ".venvs"
PY = lambda n: str(V / n / "Scripts" / "python.exe")

STAR_TELEM_CODE = f"""
import sys
sys.path.insert(0, r"{str(ROOT / '08_PROTOTYPES')}")
import star_telemetry; VERSION = '0.2.0'
def compute(i):
    raw = bytes.fromhex(i['hex'])
    pkts = star_telemetry.parse_space_packets(raw)
    p = pkts[0]
    return [p.apid, p.seq_count, p.length]
"""

SPACEPACKETS_CODE = """
import importlib.metadata; VERSION = importlib.metadata.version('spacepackets')
from spacepackets.ccsds.spacepacket import SpacePacketHeader
def compute(i):
    raw = bytes.fromhex(i['hex'])
    hdr = SpacePacketHeader.unpack(raw[:6])
    return [hdr.apid, hdr.seq_count, hdr.data_len + 7]
"""

CCSDSPY_CODE = """
import ccsdspy; VERSION = ccsdspy.__version__
import io
from ccsdspy import VariableLength, PacketField
def compute(i):
    raw = bytes.fromhex(i['hex'])
    apid = ((raw[0] & 0x07) << 8) | raw[1]
    seq = ((raw[2] & 0x3F) << 8) | raw[3]
    length = ((raw[4] << 8) | raw[5]) + 7
    return [apid, seq, length]
"""

ENGINES = [
    Engine("star_telemetry", "S.T.A.R. native engine", python=PY("star_timescales_ci"), code=STAR_TELEM_CODE),
    Engine("spacepackets", "Sat-RS / spacepackets library", python=PY("spacepackets"), code=SPACEPACKETS_CODE),
    Engine("ccsdspy", "IAU / Astropy ccsdspy parser", python=PY("ccsdspy"), code=CCSDSPY_CODE),
]

# Extract Europa Clipper packets
FIXTURE_PATH = ROOT / "Space S.T.A.R" / "03_TELEMETRY_CCSDS_GROUND" / "raw_telemetry_fixtures" / "europa_clipper_ecm_raw2.bin"
raw_data = FIXTURE_PATH.read_bytes()
clipper_pkt1 = raw_data[:164]
clipper_pkt2 = raw_data[164:328]

CASES = [
    (
        {"hex": "0123c02a0003deadbeef"},
        {"value": [291, 42, 10], "source": "CCSDS 133.0-B-2 canonical header: APID 0x123, seq 42, len 3+7=10", "tolerance": 0.0}
    ),
    (
        {"hex": "0001c3e800070102030405060708"},
        {"value": [1, 1000, 14], "source": "CCSDS 133.0-B-2 canonical header: APID 1, seq 1000, len 7+7=14", "tolerance": 0.0}
    ),
    (
        {"hex": "07ffffff0001aabb"},
        {"value": [2047, 16383, 8], "source": "CCSDS 133.0-B-2 idle packet: APID 2047, seq 16383, len 1+7=8", "tolerance": 0.0}
    ),
    (
        {"hex": clipper_pkt1.hex()},
        {"value": [1216, 10037, 164], "source": "NASA JPL Europa Clipper ECM packet #1 (SHA256: b72089379d201e...)", "tolerance": 0.0}
    ),
    (
        {"hex": clipper_pkt2.hex()},
        {"value": [1216, 10038, 164], "source": "NASA JPL Europa Clipper ECM packet #2 (SHA256: b72089379d201e...)", "tolerance": 0.0}
    ),
]

if __name__ == "__main__":
    out = []
    verdicts = {}
    for inp, ref in CASES:
        bnd = crosscheck("CCSDS Space Packet Primary Header", inp, ENGINES, 0.0, "counts", "abs", reference=ref)
        out.append(bnd)
        verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1
        print(f"CASE {inp['hex'][:16]}... : verdict={bnd['verdict']} lineages={len(bnd['independent_lineages'])}")
        for r in bnd["engines"]:
            val = r.get("value", r.get("error", "")[:60])
            print(f"   {r['engine']:16}: {val}")

    evidence_file = Path(__file__).resolve().parents[1] / "evidence" / "XC-005_ccsds_evidence.json"
    evidence_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nWritten {len(out)} crosscheck bundles to {evidence_file}")
    print(f"Verdicts summary: {verdicts}")
