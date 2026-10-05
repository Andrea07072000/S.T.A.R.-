# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 S.T.A.R.
"""
test_nasa_jpl_fprime_native_oracle.py: STAR-VERIFY-001d
Independent Oracle Verification of star_telemetry against binary frames produced
by the native compiled C++ test harness of NASA Jet Propulsion Laboratory (JPL)
F Prime Flight Software Framework (nasa/fprime).

Provenance:
- Native executable: build-fprime-automatic-native-ut/bin/Linux/export_fprime_frames_exe
- Source: Space S.T.A.R/01_FRAMEWORKS_FLIGHT_SOFTWARE/fprime
- Upstream: https://github.com/nasa/fprime (Apache-2.0)
- Verified Frames Binary: 08_PROTOTYPES/star_telemetry/fprime_native_frames.bin
- Ground Truth Metadata: 08_PROTOTYPES/star_telemetry/fprime_native_metadata.json
Verifies: R1, R2 (README).
"""

import json
from pathlib import Path
import pytest
from star_telemetry.engine import (
    CcsdsTransferFrameEngine,
    VirtualChannelReceiver,
    compute_crc16_ccitt,
)

BASE_DIR = Path(__file__).resolve().parent
BIN_PATH = BASE_DIR / "fprime_native_frames.bin"
META_PATH = BASE_DIR / "fprime_native_metadata.json"


def test_fprime_native_oracle_frames_exist():
    assert BIN_PATH.exists(), f"Missing binary frames: {BIN_PATH}"
    assert META_PATH.exists(), f"Missing metadata: {META_PATH}"
    assert BIN_PATH.stat().st_size == (256 * 4 + 254), "Binary size must match 4*256 + 254 bytes"


def test_fprime_native_oracle_frame_decoding():
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    with open(BIN_PATH, "rb") as f:
        raw_stream = f.read()

    frames_meta = meta["frames"]
    offset = 0

    # Test Frame 0: Nominal Single Packet (256 bytes)
    m0 = frames_meta[0]
    raw_frame_0 = raw_stream[offset : offset + m0["frame_size"]]
    offset += m0["frame_size"]

    engine_256 = CcsdsTransferFrameEngine(frame_length=256, has_fecf=True)
    hdr0, data0 = engine_256.parse_frame(raw_frame_0)

    assert hdr0.tfvn == 1, "TFVN must be 1 (AOS v2)"
    assert hdr0.scid == 68, f"SCID must match F Prime ComCfg::SpacecraftId (68), got {hdr0.scid}"
    assert hdr0.vcid == 7, "VCID must match 7"
    assert hdr0.vcfc == 0, "VC Frame Count must be 0"
    assert hdr0.fhp == 0, "FHP must be 0"
    assert hdr0.fecf_valid is True, "FECF CRC-16 must be valid"

    vc7 = engine_256.get_or_create_vc(7)
    pkts0 = vc7.process_frame_data(hdr0.vcfc, hdr0.fhp, data0)
    assert len(pkts0) == 1, f"Expected 1 packet, got {len(pkts0)}"
    assert pkts0[0].apid == 1
    assert pkts0[0].seq_count == 10
    assert len(pkts0[0].payload) == 50
    # Nominal frame 0: 50 bytes of payload (i & 0xFF per F Prime createSppPacket)
    assert pkts0[0].payload == bytes([i & 0xFF for i in range(50)])


def test_fprime_native_oracle_multiple_packets():
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    with open(BIN_PATH, "rb") as f:
        raw_stream = f.read()

    # Frame 1 is at offset 256
    m1 = meta["frames"][1]
    raw_frame_1 = raw_stream[256 : 256 + m1["frame_size"]]

    engine_256 = CcsdsTransferFrameEngine(frame_length=256, has_fecf=True)
    hdr1, data1 = engine_256.parse_frame(raw_frame_1)

    assert hdr1.tfvn == 1
    assert hdr1.scid == 68
    assert hdr1.vcid == 0
    assert hdr1.vcfc == 1
    assert hdr1.fhp == 0
    assert hdr1.fecf_valid is True

    vc0 = engine_256.get_or_create_vc(0)
    pkts1 = vc0.process_frame_data(hdr1.vcfc, hdr1.fhp, data1)
    assert len(pkts1) == 3, f"Expected 3 packets, got {len(pkts1)}"

    assert pkts1[0].apid == 16
    assert pkts1[0].seq_count == 1
    assert pkts1[0].payload == bytes([i & 0xFF for i in range(20)])

    assert pkts1[1].apid == 17
    assert pkts1[1].seq_count == 2
    assert pkts1[1].payload == bytes([i & 0xFF for i in range(25)])

    assert pkts1[2].apid == 18
    assert pkts1[2].seq_count == 3
    assert pkts1[2].payload == bytes([i & 0xFF for i in range(30)])


def test_fprime_native_oracle_spanning_packets():
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    with open(BIN_PATH, "rb") as f:
        raw_stream = f.read()

    # Frame 2 & 3: Spanning packet across 2 frames
    m2 = meta["frames"][2]
    m3 = meta["frames"][3]

    raw_frame_2 = raw_stream[256 * 2 : 256 * 2 + m2["frame_size"]]
    raw_frame_3 = raw_stream[256 * 3 : 256 * 3 + m3["frame_size"]]

    engine_256 = CcsdsTransferFrameEngine(frame_length=256, has_fecf=True)
    hdr2, data2 = engine_256.parse_frame(raw_frame_2)
    hdr3, data3 = engine_256.parse_frame(raw_frame_3)

    assert hdr2.vcfc == 2
    assert hdr2.fhp == 0
    assert hdr3.vcfc == 3
    assert hdr3.fhp == 56  # 302 total - 246 in first frame = 56 bytes remaining

    vc0 = engine_256.get_or_create_vc(0)
    pkts_f2 = vc0.process_frame_data(hdr2.vcfc, hdr2.fhp, data2)
    assert len(pkts_f2) == 0, "Packet spans into next frame; should not complete in frame 2"

    pkts_f3 = vc0.process_frame_data(hdr3.vcfc, hdr3.fhp, data3)
    assert len(pkts_f3) == 2, f"Expected 2 completed packets in frame 3, got {len(pkts_f3)}"

    # Reconstructed spanning packet
    spanning_pkt = pkts_f3[0]
    assert spanning_pkt.apid == 32
    assert spanning_pkt.seq_count == 42
    assert len(spanning_pkt.payload) == 296
    assert spanning_pkt.payload == bytes([i & 0xFF for i in range(296)]), "Spanning packet reconstructed payload mismatch"

    # Subsequent packet in frame 3
    next_pkt = pkts_f3[1]
    assert next_pkt.apid == 33
    assert next_pkt.seq_count == 43
    assert len(next_pkt.payload) == 20
    assert next_pkt.payload == bytes([i & 0xFF for i in range(20)])


def test_fprime_native_oracle_no_fecf_frame():
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    with open(BIN_PATH, "rb") as f:
        raw_stream = f.read()

    # Frame 4 is at offset 256*4 = 1024, size is 254 bytes
    m4 = meta["frames"][4]
    raw_frame_4 = raw_stream[1024 : 1024 + m4["frame_size"]]

    engine_254 = CcsdsTransferFrameEngine(frame_length=254, has_fecf=False)
    hdr4, data4 = engine_254.parse_frame(raw_frame_4)

    assert hdr4.tfvn == 1
    assert hdr4.scid == 68
    assert hdr4.vcid == 2
    assert hdr4.vcfc == 4
    assert hdr4.fhp == 0

    vc2 = engine_254.get_or_create_vc(2)
    pkts4 = vc2.process_frame_data(hdr4.vcfc, hdr4.fhp, data4)
    assert len(pkts4) == 1
    assert pkts4[0].apid == 64
    assert pkts4[0].seq_count == 99
    assert len(pkts4[0].payload) == 40
    assert pkts4[0].payload == bytes([i & 0xFF for i in range(40)])
