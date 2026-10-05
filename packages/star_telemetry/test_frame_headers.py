# SPDX-License-Identifier: Apache-2.0
"""Header fields of TM (CCSDS 132.0-B) and AOS (CCSDS 732.0-B) frames, each set to a distinct non-trivial value so that
mask/shift mutants cannot survive. Found 2026-10-04: the TM path read the MASTER channel count (octet 2) as the VC count
and the OCF flag as 'replay'. Oracles: frames packed by hand from the standard here, and by spacepackets (independent
lineage) when it is importable."""
import struct

import pytest

from star_telemetry import CCSDS_ASM, CcsdsTransferFrameEngine, compute_crc16_ccitt

L = 64


def pkt(apid, payload, seq=0):
    n = len(payload) - 1
    return bytes([(apid >> 8) & 0x07, apid & 0xFF, 0xC0 | (seq >> 8), seq & 0xFF, n >> 8, n & 0xFF]) + payload


def with_crc(body):
    return body + struct.pack(">H", compute_crc16_ccitt(body))


def tm(scid, vcid, mc, vc, fhp, data, ocf=None):
    w1 = (scid << 4) | (vcid << 1) | (1 if ocf is not None else 0)
    hdr = struct.pack(">HBBH", w1, mc, vc, 0x1800 | fhp)          # sync=0, order=0, segment len id = 11
    room = L - 6 - 2 - (4 if ocf is not None else 0)
    return with_crc(hdr + data.ljust(room, b"\xE0") + (ocf or b""))


def aos(scid, vcid, vcfc, replay, fhp, data):
    hdr = struct.pack(">H", (1 << 14) | (scid << 6) | vcid) + vcfc.to_bytes(3, "big") + bytes([0x80 if replay else 0])
    hdr += struct.pack(">H", fhp)
    return with_crc(hdr + data.ljust(L - 8 - 2, b"\xE0"))


def test_tm_header_fields_are_read_from_the_right_octets():
    e = CcsdsTransferFrameEngine(frame_length=L)
    h, _ = e.parse_frame(tm(scid=0x2A5, vcid=5, mc=200, vc=17, fhp=0x123, data=b""))
    assert (h.tfvn, h.scid, h.vcid, h.vcfc, h.fhp, h.replay_flag, h.fecf_valid) == (0, 0x2A5, 5, 17, 0x123, False, True)


def test_tm_ocf_is_excluded_from_the_data_field():
    e = CcsdsTransferFrameEngine(frame_length=L)
    _, d = e.parse_frame(tm(1, 2, 3, 4, 0, b"\x11" * 4, ocf=b"\xAA\xBB\xCC\xDD"))
    assert len(d) == L - 6 - 2 - 4 and not d.endswith(b"\xAA\xBB\xCC\xDD")
    _, d2 = e.parse_frame(tm(1, 2, 3, 4, 0, b"\x11" * 4))
    assert len(d2) == L - 6 - 2


def test_tm_secondary_header_is_skipped():
    w1 = (7 << 4) | (1 << 1)
    sec = bytes([0x02, 0x55, 0x66])                                  # version 0, length-1 = 2 -> 3 octets
    body = struct.pack(">HBBH", w1, 9, 9, 0x8000 | 0x1800) + sec
    p = pkt(0x33, b"PAYLOAD")
    frame = with_crc(body + p.ljust(L - len(body) - 2, b"\xE0"))
    _, d = CcsdsTransferFrameEngine(frame_length=L).parse_frame(frame)
    assert d.startswith(p)


def test_tm_interleaved_vcs_report_no_false_drops_and_8bit_wrap():
    # master channel count rises on every frame; each VC count rises only on its own frames and wraps at 256
    frames, mc = [], 0
    for vc_count in (254, 255, 0, 1):
        for vcid in (1, 2):
            frames.append(tm(0x10, vcid, mc & 0xFF, vc_count, 0, pkt(0x40 + vcid, bytes([vc_count]))))
            mc += 1
    e = CcsdsTransferFrameEngine(frame_length=L)
    out = e.process_raw_stream(b"".join(CCSDS_ASM + f for f in frames))
    assert len(out) == 8
    assert {v: e.virtual_channels[v].frames_dropped for v in (1, 2)} == {1: 0, 2: 0}


def test_tm_real_gap_is_counted():
    frames = [tm(0x10, 3, i, c, 0, pkt(0x50, b"x")) for i, c in enumerate((10, 11, 14))]
    e = CcsdsTransferFrameEngine(frame_length=L)
    e.process_raw_stream(b"".join(CCSDS_ASM + f for f in frames))
    assert e.virtual_channels[3].frames_dropped == 2


def test_aos_header_fields_distinct_values():
    e = CcsdsTransferFrameEngine(frame_length=L)
    h, d = e.parse_frame(aos(scid=0xB7, vcid=0x2D, vcfc=0x0A0B0C, replay=True, fhp=0x2F1, data=b""))
    assert (h.tfvn, h.scid, h.vcid, h.vcfc, h.replay_flag, h.fhp) == (1, 0xB7, 0x2D, 0x0A0B0C, True, 0x2F1)
    assert len(d) == L - 8 - 2
    h2, _ = e.parse_frame(aos(0xB7, 0x2D, 0xFFFFFF, False, 0, b""))
    assert h2.replay_flag is False and h2.vcfc == 0xFFFFFF


def test_aos_24bit_wrap_is_not_a_gap():
    frames = [aos(5, 6, c, False, 0, pkt(0x60, b"z")) for c in (0xFFFFFE, 0xFFFFFF, 0)]
    e = CcsdsTransferFrameEngine(frame_length=L)
    assert len(e.process_raw_stream(b"".join(CCSDS_ASM + f for f in frames))) == 3
    assert e.virtual_channels[6].frames_dropped == 0


def test_bad_crc_frame_counted_and_skipped():
    good = aos(5, 6, 1, False, 0, pkt(0x60, b"z"))
    bad = good[:-1] + bytes([good[-1] ^ 1])
    e = CcsdsTransferFrameEngine(frame_length=L)
    assert e.process_raw_stream(CCSDS_ASM + bad + CCSDS_ASM + good) and e.crc_errors == 1 and e.total_synced_frames == 2


def test_against_spacepackets_tm_packer():
    tmf = pytest.importorskip("spacepackets.ccsds.tm_frame")
    ph = tmf.TmFramePrimaryHeader(tmf.MasterChannelId(0, 0x1F3), 6, True, 77, 201,
                                  tmf.TransferFrameDataFieldStatus(False, False, False, 3, 0x0AB))
    raw = ph.pack()
    body = raw + b"\x00" * (L - len(raw) - 4 - 2) + b"\x01\x02\x03\x04"
    h, d = CcsdsTransferFrameEngine(frame_length=L).parse_frame(with_crc(body))
    assert (h.scid, h.vcid, h.vcfc, h.fhp) == (0x1F3, 6, 201, 0x0AB) and len(d) == L - 6 - 4 - 2
