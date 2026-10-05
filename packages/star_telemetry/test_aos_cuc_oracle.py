# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 S.T.A.R.
"""
test_aos_cuc_oracle.py: STAR-VERIFY-001b Independent Oracle Verification Suite
for CCSDS AOS 732.0-B-4 Transfer Frames and CCSDS 301.0-B-4 CUC Timestamps.

Authorities / Standards:
- CCSDS 732.0-B-4: AOS Space Data Link Protocol (Section 4: Transfer Frame)
- CCSDS 301.0-B-4: Time Code Formats (Section 3.2: CCSDS Unsegmented Time Code)
- Independent Reference 1: First-principles hand-computed mathematical derivation
- Independent Reference 2: star_timescales public-verified reference implementation
"""

import struct
from datetime import datetime, timezone, timedelta
from fractions import Fraction
import pytest


from star_timescales import encode_cuc, decode_cuc, cuc_to_utc, cuc_p_field
from star_telemetry.engine import (
    CcsdsTransferFrameEngine,
    TransferFrameHeader,
    SpacePacket,
    VirtualChannelReceiver,
    CCSDS_ASM,
    compute_crc16_ccitt,
    generate_ccsds_randomizer_sequence,
)


# ==============================================================================
# SECTION 1: HAND-COMPUTED CCSDS 301.0-B-4 CUC ORACLES (FIRST PRINCIPLES)
# ==============================================================================

def test_cuc_hand_computed_historic_epoch_1972():
    """
    Hand-computed reference test vector 1:
    Epoch: 1972-01-01 00:00:00 UTC (Inception of UTC with leap seconds).
    
    Mathematical derivation from first principles:
    - Base CUC Level 1 Epoch: 1958-01-01 00:00:00 TAI
    - Interval 1958 to 1972: 14 years
    - Leap years: 1960, 1964, 1968 (3 leap days)
    - Total days = 14 * 365 + 3 = 5113 days
    - Days to seconds = 5113 * 86400 = 441,763,200 seconds
    - TAI - UTC offset at 1972-01-01 00:00:00 UTC is exactly +10.0 s
    - Total elapsed TAI seconds = 441,763,200 + 10 = 441,763,210 s
    - Hex representation of 441,763,210:
      441,763,210 = 0x1A54FE8A
    - Fine fraction (0.0 s) = 0x0000
    - P-field: 1 octet:
      extension=0 (bit 7)
      time code id = 001 (Level 1, bits 6-4) -> 0b001
      coarse octets - 1 = 4 - 1 = 3 = 0b11 (bits 3-2)
      fine octets = 2 = 0b10 (bits 1-0)
      P-field byte = (0b001 << 4) | (0b11 << 2) | (0b10) = 0x1E (decimal 30)
    """
    hand_coarse_int = 441763210
    hand_coarse_hex = b"\x1a\x54\xc5\x8a"
    hand_fine_hex = b"\x00\x00"
    hand_p_field = 0x1E
    hand_cuc_complete = bytes([hand_p_field]) + hand_coarse_hex + hand_fine_hex

    target_utc = datetime(1972, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # 1. Verify star_timescales matches hand calculation exactly
    derived_p = cuc_p_field(coarse_octets=4, fine_octets=2)
    assert derived_p == hand_p_field, f"P-field mismatch: {derived_p:#x} vs {hand_p_field:#x}"
    
    encoded_cuc = encode_cuc(target_utc, coarse_octets=4, fine_octets=2, p_field=True)
    assert encoded_cuc == hand_cuc_complete, (
        f"Encoded CUC mismatch!\nGot:  {encoded_cuc.hex()}\nHand: {hand_cuc_complete.hex()}"
    )

    # 2. Verify decode_cuc matches hand integer seconds
    decoded_tai_seconds = decode_cuc(hand_cuc_complete)
    assert decoded_tai_seconds == hand_coarse_int, (
        f"Decoded TAI seconds {decoded_tai_seconds} != {hand_coarse_int}"
    )

    # 3. Verify cuc_to_utc round-trip recovers exact 1972-01-01 UTC
    recovered_utc = cuc_to_utc(hand_cuc_complete)
    assert recovered_utc == target_utc


def test_cuc_hand_computed_campaign_epoch_2026():
    """
    Hand-computed reference test vector 2:
    Date: 2026-10-02 12:00:00.500000 UTC (S.T.A.R. Campaign date).
    
    Mathematical derivation from first principles:
    - Base CUC Level 1 Epoch: 1958-01-01 00:00:00 TAI
    - Interval 1958 to 2026: 68 years
    - Leap years in [1958, 2026):
      1960, 64, 68, 72, 76, 80, 84, 88, 92, 96, 2000, 04, 08, 12, 16, 20, 24 = 17 leap years
    - Days to 2026-01-01 = 68 * 365 + 17 = 24,820 + 17 = 24,837 days
    - Days in 2026 up to Oct 2:
      Jan: 31, Feb: 28, Mar: 31, Apr: 30, May: 31, Jun: 30, Jul: 31, Aug: 31, Sep: 30, Oct: 1
      Sum = 274 days
    - Total days = 24,837 + 274 = 25,111 days
    - Time of day: 12:00:00 = 43,200 seconds
    - Elapsed UTC seconds = 25,111 * 86,400 + 43,200 = 2,169,590,400 + 43,200 = 2,169,633,600 s
    - TAI - UTC offset in 2026 = +37.0 s (no leap seconds inserted since 2016-12-31)
    - Total elapsed TAI coarse seconds = 2,169,633,600 + 37 = 2,169,633,637 s
    - Hex representation of 2,169,633,637:
      2,169,633,637 = 0x8151FB65
    - Fine fraction: 0.500000 s
      With 2 fine octets (16 bits): 0.5 * 2^16 = 32,768 = 0x8000
    - Hand expected CUC bytes (without P-field): 0x8151FB658000
    - Hand expected CUC bytes (with P-field): 0x1E8151FB658000
    """
    hand_coarse_int = 2169633637
    hand_coarse_hex = b"\x81\x51\xfb\x65"
    hand_fine_hex = b"\x80\x00"
    hand_cuc_raw = hand_coarse_hex + hand_fine_hex
    hand_cuc_with_p = b"\x1e" + hand_cuc_raw

    target_utc = datetime(2026, 10, 2, 12, 0, 0, 500000, tzinfo=timezone.utc)

    # 1. Validate star_timescales against hand calculation
    encoded_cuc = encode_cuc(target_utc, coarse_octets=4, fine_octets=2, p_field=True)
    assert encoded_cuc == hand_cuc_with_p, (
        f"Encoded CUC mismatch!\nGot:  {encoded_cuc.hex()}\nHand: {hand_cuc_with_p.hex()}"
    )

    # 2. Validate decoded fraction
    decoded_tai = decode_cuc(hand_cuc_with_p)
    expected_tai_fraction = Fraction(2169633637) + Fraction(1, 2)
    assert decoded_tai == expected_tai_fraction

    # 3. Validate UTC instant recovery
    recovered_utc = cuc_to_utc(hand_cuc_with_p)
    assert recovered_utc == target_utc


def test_cuc_microsecond_quantization_bound():
    """
    Requirement: CUC with 2 fine octets has quantization resolution of 1 / 2^16 s = 15.258789 microseconds.
    Verify that any UTC instant within a 1-second interval round-trips with residual < 15.26 microseconds.
    """
    base_utc = datetime(2026, 10, 2, 23, 15, 0, 0, tzinfo=timezone.utc)
    for offset_us in [0, 100, 1000, 15258, 30000, 123456, 500000, 999990]:
        test_dt = base_utc + timedelta(microseconds=offset_us)
        cuc_code = encode_cuc(test_dt, coarse_octets=4, fine_octets=2, p_field=False)
        recovered_dt = cuc_to_utc(cuc_code, coarse_octets=4, fine_octets=2)
        diff_us = abs((recovered_dt - test_dt).total_seconds()) * 1e6
        # Truncation error must strictly be in [0, 15.26] us
        assert diff_us < 15.26, f"Quantization error {diff_us} us exceeds 15.26 us limit"


# ==============================================================================
# SECTION 2: INDEPENDENT BIT-EXACT ORACLE FOR CCSDS 732.0-B-4 AOS FRAMES
# ==============================================================================

class IndependentAosFrameOracle:
    """
    Independent reference decoder implemented directly from CCSDS 732.0-B-4 specification.
    Does NOT use star_telemetry.engine internal methods.
    """
    @staticmethod
    def decode_header(frame_bytes: bytes) -> dict:
        assert len(frame_bytes) >= 7, "AOS primary header must be at least 7 octets"
        # Octets 0-1: Transfer Frame Primary Header
        # Bit 0-1: Transfer Frame Version Number (must be 0b01)
        # Bit 2-9: Spacecraft Identifier (SCID, 8 bits)
        # Bit 10-15: Virtual Channel Identifier (VCID, 6 bits)
        b0, b1 = frame_bytes[0], frame_bytes[1]
        tfvn = (b0 >> 6) & 0x03
        scid = ((b0 & 0x3F) << 2) | ((b1 >> 6) & 0x03)
        vcid = b1 & 0x3F

        # Octets 2-4: Virtual Channel Frame Count (24 bits)
        vcfc = (frame_bytes[2] << 16) | (frame_bytes[3] << 8) | frame_bytes[4]

        # Octets 5-6: Signaling Field + First Header Pointer
        # Octet 5: Signaling Field
        signaling = frame_bytes[5]
        replay_flag = bool((signaling >> 7) & 0x01)

        # Octets 6-7: M_PDU Header (First Header Pointer, 11 bits)
        mpdu_w = (frame_bytes[6] << 8) | frame_bytes[7]
        fhp = mpdu_w & 0x07FF

        return {
            "tfvn": tfvn,
            "scid": scid,
            "vcid": vcid,
            "vcfc": vcfc,
            "replay_flag": replay_flag,
            "fhp": fhp,
        }

    @staticmethod
    def verify_crc16(frame_bytes: bytes) -> bool:
        assert len(frame_bytes) >= 10
        data = frame_bytes[:-2]
        received_crc = (frame_bytes[-2] << 8) | frame_bytes[-1]
        # Independent CRC-16 computation
        crc = 0xFFFF
        for b in data:
            crc ^= (b << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc == received_crc


def build_reference_aos_frame(scid: int, vcid: int, vcfc: int, fhp: int, payload: bytes, frame_len: int = 1115) -> bytes:
    """Builds a strictly conformant CCSDS 732.0-B-4 AOS frame with 8-byte header."""
    hdr = bytearray(8)
    # TFVN = 0b01 (AOS v2)
    # scid: 8 bits, vcid: 6 bits
    hdr[0] = (0x01 << 6) | ((scid >> 2) & 0x3F)
    hdr[1] = ((scid & 0x03) << 6) | (vcid & 0x3F)
    hdr[2] = (vcfc >> 16) & 0xFF
    hdr[3] = (vcfc >> 8) & 0xFF
    hdr[4] = vcfc & 0xFF
    hdr[5] = 0x00  # Signaling field
    hdr[6] = (fhp >> 8) & 0x07
    hdr[7] = fhp & 0xFF

    data_len = frame_len - 8 - 2  # 8-byte header, 2-byte FECF CRC
    if len(payload) < data_len:
        body = payload + bytes([0xE0] * (data_len - len(payload)))
    else:
        body = payload[:data_len]

    frame_without_crc = bytes(hdr) + body
    # Compute CRC-16
    crc = compute_crc16_ccitt(frame_without_crc)
    return frame_without_crc + struct.pack(">H", crc)


def test_aos_frame_header_differential_oracle():
    """
    Differential verification of AOS Transfer Frame header decoding between:
    1. IndependentAosFrameOracle (derived directly from CCSDS 732.0-B-4 standard)
    2. star_telemetry.engine.CcsdsTransferFrameEngine
    """
    test_cases = [
        {"scid": 42, "vcid": 1, "vcfc": 0, "fhp": 0},
        {"scid": 255, "vcid": 63, "vcfc": 16777215, "fhp": 2047},  # Boundary rollover
        {"scid": 128, "vcid": 31, "vcfc": 123456, "fhp": 2046},    # Idle data marker
        {"scid": 1, "vcid": 0, "vcfc": 1, "fhp": 48},              # Packet offset 48
    ]

    engine = CcsdsTransferFrameEngine(frame_length=1115, has_fecf=True)

    for tc in test_cases:
        frame_bytes = build_reference_aos_frame(
            scid=tc["scid"],
            vcid=tc["vcid"],
            vcfc=tc["vcfc"],
            fhp=tc["fhp"],
            payload=b"AOS_TEST_PAYLOAD",
            frame_len=1115,
        )

        # Oracle independent evaluation
        oracle_res = IndependentAosFrameOracle.decode_header(frame_bytes)
        oracle_crc_valid = IndependentAosFrameOracle.verify_crc16(frame_bytes)

        assert oracle_crc_valid is True
        assert oracle_res["tfvn"] == 1  # AOS v2
        assert oracle_res["scid"] == tc["scid"]
        assert oracle_res["vcid"] == tc["vcid"]
        assert oracle_res["vcfc"] == tc["vcfc"]
        assert oracle_res["fhp"] == tc["fhp"]

        # Engine evaluation
        engine_hdr, engine_data = engine.parse_frame(frame_bytes)

        # Cross-comparison: Engine vs Oracle
        assert engine_hdr.tfvn == oracle_res["tfvn"]
        assert engine_hdr.scid == oracle_res["scid"], f"SCID mismatch: {engine_hdr.scid} vs {oracle_res['scid']}"
        assert engine_hdr.vcid == oracle_res["vcid"], f"VCID mismatch: {engine_hdr.vcid} vs {oracle_res['vcid']}"
        assert engine_hdr.vcfc == oracle_res["vcfc"], f"VCFC mismatch: {engine_hdr.vcfc} vs {oracle_res['vcfc']}"
        assert engine_hdr.fhp == oracle_res["fhp"], f"FHP mismatch: {engine_hdr.fhp} vs {oracle_res['fhp']}"
        assert engine_hdr.fecf_valid is True


def test_aos_end_to_end_packet_with_cuc_secondary_header():
    """
    Full end-to-end integration test:
    Construct a real CCSDS Space Packet containing:
    - Primary Header: APID 0x02AA, sequence 100, sec_hdr_flag=1
    - Secondary Header: CCSDS 301.0-B Level 1 CUC timestamp (4 coarse, 2 fine)
    - Payload: Scientific sensor measurements
    Embed inside an AOS Transfer Frame (CCSDS 732.0-B-4) with Attached Sync Marker (0x1ACFFC1D).
    Pass through CcsdsTransferFrameEngine and verify bit-for-bit and microsecond-exact recovery.
    """
    campaign_utc = datetime(2026, 10, 2, 23, 20, 0, 750000, tzinfo=timezone.utc)
    cuc_bytes = encode_cuc(campaign_utc, coarse_octets=4, fine_octets=2, p_field=False)

    scientific_payload = b"\xDE\xAD\xBE\xEF" * 16  # 64 bytes telemetry data
    packet_body = cuc_bytes + scientific_payload

    # Pack CCSDS Space Packet header (6 bytes)
    apid = 0x02AA
    h1 = (0 << 13) | (0 << 12) | (1 << 11) | (apid & 0x07FF)
    h2 = (3 << 14) | (100 & 0x3FFF)
    raw_packet = struct.pack(">HHH", h1, h2, len(packet_body) - 1) + packet_body

    # Build AOS Frame
    frame = build_reference_aos_frame(scid=55, vcid=3, vcfc=42, fhp=0, payload=raw_packet, frame_len=1115)
    streaming_stream = CCSDS_ASM + frame

    engine = CcsdsTransferFrameEngine(frame_length=1115, has_fecf=True)
    packets = engine.process_raw_stream(streaming_stream)

    assert len(packets) == 1
    p = packets[0]
    assert p.apid == 0x02AA
    assert p.sec_hdr_flag == 1
    assert p.seq_count == 100
    assert p.payload[6:] == scientific_payload
    assert p.timestamp_utc is not None

    # Verify timestamp error is bounded by CUC 16-bit fine quantization (< 15.26 us)
    time_delta_us = abs((p.timestamp_utc - campaign_utc).total_seconds()) * 1e6
    assert time_delta_us < 15.26, f"CUC timestamp error {time_delta_us} us exceeded 15.26 us bound"


if __name__ == "__main__":
    print("=" * 70)
    print("STAR-VERIFY-001b: CCSDS AOS & CUC INDEPENDENT ORACLE TEST SUITE")
    print("=" * 70)
    test_cuc_hand_computed_historic_epoch_1972()
    print(" [PASS] test_cuc_hand_computed_historic_epoch_1972 (Exact TAI=441,763,210 s)")
    test_cuc_hand_computed_campaign_epoch_2026()
    print(" [PASS] test_cuc_hand_computed_campaign_epoch_2026 (Exact TAI=2,169,633,637.5 s)")
    test_cuc_microsecond_quantization_bound()
    print(" [PASS] test_cuc_microsecond_quantization_bound (All residuals < 15.26 us)")
    test_aos_frame_header_differential_oracle()
    print(" [PASS] test_aos_frame_header_differential_oracle (4/4 bitfields match oracle)")
    test_aos_end_to_end_packet_with_cuc_secondary_header()
    print(" [PASS] test_aos_end_to_end_packet_with_cuc_secondary_header (Full stream verified)")
    print("\nALL STAR-VERIFY-001b ORACLE TESTS PASSED (5/5 QUALIFIED)!")
