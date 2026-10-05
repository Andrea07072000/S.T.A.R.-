# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 S.T.A.R.
"""
test_telemetry.py: Verification suite for star_telemetry engine federated with star_timescales CUC decoding.
"""

import os
import struct
from datetime import datetime, timezone
import pytest


from star_timescales import encode_cuc, cuc_to_utc
from star_telemetry import (
    CcsdsTransferFrameEngine,
    CCSDS_ASM,
    compute_crc16_ccitt,
    generate_ccsds_randomizer_sequence,
)


def build_synthetic_frame(scid=10, vcid=1, vcfc=0, fhp=0, payload=b"", frame_length=1115):
    """Builds a valid CCSDS AOS v2 Transfer Frame with ASM, 8-byte header, and CRC-16."""
    hdr_bytes = bytearray()
    w1 = (1 << 14) | ((scid & 0xFF) << 6) | (vcid & 0x3F)
    hdr_bytes.extend(struct.pack(">H", w1))
    hdr_bytes.append((vcfc >> 16) & 0xFF)
    hdr_bytes.append((vcfc >> 8) & 0xFF)
    hdr_bytes.append(vcfc & 0xFF)
    hdr_bytes.append(0x00)  # Signaling field (byte 5)
    hdr_bytes.extend(struct.pack(">H", fhp & 0x07FF))  # M_PDU header (bytes 6-7)

    target_data_len = frame_length - len(hdr_bytes) - 2
    if len(payload) < target_data_len:
        padded_data = payload + bytes([0xE0] * (target_data_len - len(payload)))
    else:
        padded_data = payload[:target_data_len]

    frame_without_crc = bytes(hdr_bytes) + padded_data
    crc = compute_crc16_ccitt(frame_without_crc)
    return CCSDS_ASM + frame_without_crc + struct.pack(">H", crc)



def test_secondary_header_cuc_timestamp():
    """Requirement: CCSDS Space Packet secondary header CUC timestamp is decoded to exact microsecond UTC."""
    test_utc = datetime(2026, 10, 2, 12, 30, 45, 123456, tzinfo=timezone.utc)
    cuc_bytes = encode_cuc(test_utc, coarse_octets=4, fine_octets=2, p_field=False)
    
    # Create CCSDS Space Packet with sec_header=1, APID=0x0123
    apid = 0x0123
    h1 = (0 << 13) | (0 << 12) | (1 << 11) | (apid & 0x07FF)
    h2 = (3 << 14) | (42 & 0x3FFF)  # standalone packet, seq=42
    
    packet_data = cuc_bytes + b"SENSOR_DATA_PAYLOAD_XYZ"
    length_field = len(packet_data) - 1
    raw_packet = struct.pack(">HHH", h1, h2, length_field) + packet_data
    
    frame = build_synthetic_frame(payload=raw_packet)
    engine = CcsdsTransferFrameEngine(frame_length=1115, has_fecf=True)
    packets = engine.process_raw_stream(frame)
    
    assert len(packets) == 1
    pkt = packets[0]
    assert pkt.apid == 0x0123
    assert pkt.sec_hdr_flag == 1
    assert pkt.timestamp_utc is not None
    
    # Verify timestamp round-trip within fine-octet truncation precision (~15 microseconds)
    diff_microsec = abs((pkt.timestamp_utc - test_utc).total_seconds()) * 1e6
    assert diff_microsec < 20.0, f"Timestamp divergence: {diff_microsec} microseconds"


def test_crc_rejection():
    """Requirement: Corrupted frames must be rejected by CRC-16 check."""
    frame = bytearray(build_synthetic_frame(payload=b"VALID"))
    # Corrupt one bit in payload
    frame[30] ^= 0x01
    
    engine = CcsdsTransferFrameEngine(frame_length=1115, has_fecf=True)
    packets = engine.process_raw_stream(bytes(frame))
    assert len(packets) == 0
    assert engine.crc_errors == 1


def test_multi_frame_spanning_packet():
    """Requirement: A packet larger than a single frame must reassemble across frame boundaries."""
    large_payload = b"X" * 1500
    apid = 0x0456
    h1 = (0 << 13) | (0 << 12) | (0 << 11) | (apid & 0x07FF)
    h2 = (3 << 14) | (100 & 0x3FFF)
    raw_large_packet = struct.pack(">HHH", h1, h2, len(large_payload) - 1) + large_payload
    
    # Split into 2 frames
    body_len = 1115 - 8 - 2
    part1 = raw_large_packet[:body_len]
    part2 = raw_large_packet[body_len:]
    
    f1 = build_synthetic_frame(vcid=2, vcfc=10, fhp=0, payload=part1)
    f2 = build_synthetic_frame(vcid=2, vcfc=11, fhp=len(part2), payload=part2)
    
    engine = CcsdsTransferFrameEngine(frame_length=1115, has_fecf=True)
    packets = engine.process_raw_stream(f1 + f2)
    
    assert len(packets) == 1
    pkt = packets[0]
    assert pkt.apid == 0x0456
    assert pkt.payload == large_payload


if __name__ == "__main__":
    print("Running star_telemetry verification suite...")
    test_secondary_header_cuc_timestamp()
    print(" [PASS] test_secondary_header_cuc_timestamp (CUC round-trip < 20 us)")
    test_crc_rejection()
    print(" [PASS] test_crc_rejection (CRC-16 bit-flip detected)")
    test_multi_frame_spanning_packet()
    print(" [PASS] test_multi_frame_spanning_packet (M-PDU boundary reassembly)")
    print("\nALL TELEMETRY TESTS QUALIFIED (3/3 PASSED)!")


def test_wrong_frame_length_is_rejected():
    import pytest as _pt
    from star_telemetry.engine import CcsdsTransferFrameEngine as _E
    with _pt.raises(ValueError):
        _E(frame_length=256, has_fecf=True).parse_frame(bytes(255))
    with _pt.raises(ValueError):
        _E(frame_length=256, has_fecf=True).parse_frame(bytes(257))
