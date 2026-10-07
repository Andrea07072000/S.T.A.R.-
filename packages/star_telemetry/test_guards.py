# SPDX-License-Identifier: Apache-2.0
"""Guard tests added by the reviewer on 2026-10-07, after the corrected mutation runner measured engine.py at 0.83, below
the present 0.85 gate. Writing them showed three defects of packet reassembly, fixed in 0.2.7:
  1. a packet that ended exactly at the end of a frame carrying no packet start (first header pointer 2047) was lost;
  2. after a lost frame, continuation data were kept and then read as if they began with a packet header;
  3. an unfinished packet followed by a frame whose first header pointer is 0 stayed in the buffer and was later joined
     to bytes that did not belong to it.
Every expected value is a packet built here octet by octet from CCSDS 133.0-B (6-octet primary header).
Verifies: R1, R2, R3 (README)."""
import struct
from datetime import datetime, timezone

import pytest

from star_timescales import encode_cuc

from star_telemetry import CCSDS_ASM, CcsdsTransferFrameEngine, VirtualChannelReceiver, compute_crc16_ccitt, parse_space_packets

NO_START = 2047          # first header pointer: no packet starts in this frame
ONLY_IDLE = 2046         # first header pointer: the frame carries idle data only


def pkt(apid, payload, seq=0, flags=3, ptype=0, sec=0, version=0):
    w1 = (version << 13) | (ptype << 12) | (sec << 11) | apid
    return struct.pack(">HHH", w1, (flags << 14) | seq, len(payload) - 1) + payload


def body(n, start):
    return bytes((start + k) % 251 for k in range(n))


def aos(vcfc, fhp, data, length, scid=0x5A, vcid=3, fecf=True):
    hdr = struct.pack(">H", (1 << 14) | (scid << 6) | vcid) + vcfc.to_bytes(3, "big") + bytes([0]) + struct.pack(">H", fhp)
    room = length - 8 - (2 if fecf else 0)
    assert len(data) <= room
    frame = hdr + data.ljust(room, bytes([0xE0]))
    if fecf:
        frame += struct.pack(">H", compute_crc16_ccitt(frame))
    return frame


def test_default_counter_is_24_bits_wide():
    assert VirtualChannelReceiver(3).vcfc_mask == 0xFFFFFF
    assert CcsdsTransferFrameEngine(64).get_or_create_vc(5).vcfc_mask == 0xFFFFFF
    vc = VirtualChannelReceiver(3)
    vc.process_frame_data(0xFFFFFF, 0, pkt(1, b"ab"))
    vc.process_frame_data(0, 0, pkt(1, b"cd"))                     # 0xFFFFFF + 1 wraps to 0: nothing was lost
    assert vc.frames_dropped == 0 and vc.frames_received == 2
    vc.process_frame_data(3, 0, pkt(1, b"ef"))                     # 1 and 2 are missing
    assert vc.frames_dropped == 2


def test_packet_over_three_frames_and_header_split_between_frames():
    a, p, b, c = pkt(0x10, body(4, 1)), pkt(0x155, body(30, 7), seq=0x2AAA), pkt(0x2AA, body(4, 90)), pkt(0, body(2, 50))
    assert (len(a), len(p), len(b), len(c)) == (10, 36, 10, 8)
    vc = VirtualChannelReceiver(1)
    assert vc.process_frame_data(0, 0, a + p[:6]) == [vc.reassembled_packets[0]] and vc.reassembled_packets[0].raw_packet == a
    assert vc.process_frame_data(1, NO_START, p[6:22]) == []
    got = vc.process_frame_data(2, 14, p[22:] + b[:2])             # two octets of the next header: not enough to read it
    assert [g.raw_packet for g in got] == [p] and got[0].apid == 0x155 and got[0].seq_count == 0x2AAA and got[0].payload == body(30, 7)
    got = vc.process_frame_data(3, 8, b[2:] + c)
    assert [g.raw_packet for g in got] == [b, c] and got[1].apid == 0          # APID 0 is an ordinary packet
    assert [g.raw_packet for g in vc.reassembled_packets] == [a, p, b, c] and vc.frames_dropped == 0 and len(vc.assembly_buffer) == 0


def test_packet_ending_exactly_at_the_end_of_a_frame_without_packet_start_is_delivered():
    a, p, c = pkt(0x10, body(4, 1)), pkt(0x155, body(16, 7)), pkt(0x20, body(10, 30))
    assert len(p) == 22 and len(c) == 16
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:6])
    got = vc.process_frame_data(1, NO_START, p[6:])                # the packet is complete here: it is delivered here
    assert [g.raw_packet for g in got] == [p] and len(vc.assembly_buffer) == 0
    got = vc.process_frame_data(2, 0, c)
    assert [g.raw_packet for g in got] == [c]
    assert [g.raw_packet for g in vc.reassembled_packets] == [a, p, c]


def test_after_a_lost_frame_continuation_data_are_not_read_as_a_packet():
    a, p, d = pkt(0x10, body(4, 1)), pkt(0x155, body(40, 7)), pkt(0x30, body(4, 60))
    looks_like_a_packet = pkt(0x77, body(16, 3))                    # 22 octets that would parse as a packet
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:6])
    assert vc.process_frame_data(2, NO_START, looks_like_a_packet[:16]) == []      # frame 1 was lost
    assert vc.frames_dropped == 1 and len(vc.assembly_buffer) == 0
    got = vc.process_frame_data(3, 6, looks_like_a_packet[16:] + d)
    assert [g.raw_packet for g in got] == [d]
    assert [g.apid for g in vc.reassembled_packets] == [0x10, 0x30]


def test_unfinished_packet_is_dropped_when_the_next_frame_starts_with_a_packet():
    a, p, c, e = pkt(0x10, body(4, 1)), pkt(0x155, body(9, 7)), pkt(0x20, body(10, 30)), pkt(0x40, b"z")
    assert len(p) == 15 and len(e) == 7
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:6])
    assert [g.raw_packet for g in vc.process_frame_data(1, 0, c)] == [c]           # pointer 0: the unfinished packet cannot go on
    assert len(vc.assembly_buffer) == 0
    got = vc.process_frame_data(2, 9, body(9, 200) + e)             # nine octets that would complete the stale header
    assert [g.raw_packet for g in got] == [e]
    assert [g.apid for g in vc.reassembled_packets] == [0x10, 0x20, 0x40]


def test_pending_packet_whose_length_does_not_match_is_dropped():
    a, p, d = pkt(0x10, body(4, 1)), pkt(0x155, body(16, 7)), pkt(0x30, body(4, 60))
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:6])
    got = vc.process_frame_data(1, 6, p[6:12] + d)                  # 12 octets of a packet that declares 22
    assert [g.raw_packet for g in got] == [d]
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:6])
    got = vc.process_frame_data(1, 6, pkt(0x155, body(16, 7))[6:12] + d)
    assert [g.apid for g in got] == [0x30]
    vc = VirtualChannelReceiver(1)                                  # more octets than the packet declares: dropped, not cut
    short = pkt(0x155, body(3, 7))
    vc.process_frame_data(0, 0, a + short[:6])
    got = vc.process_frame_data(1, 6, body(6, 100) + d)
    assert [g.raw_packet for g in got] == [d]
    vc = VirtualChannelReceiver(1)                                  # and the same in a frame without packet start
    vc.process_frame_data(0, 0, a + short[:6])
    assert vc.process_frame_data(1, NO_START, body(16, 100)) == [] and len(vc.assembly_buffer) == 0


def test_idle_frame_leaves_the_pending_packet_untouched():
    a, p = pkt(0x10, body(4, 1)), pkt(0x155, body(16, 7))
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:6])
    assert vc.process_frame_data(1, ONLY_IDLE, bytes([0xE0]) * 16) == [] and bytes(vc.assembly_buffer) == p[:6]
    got = vc.process_frame_data(2, NO_START, p[6:])
    assert [g.raw_packet for g in got] == [p]
    assert vc.frames_received == 3


def test_octets_before_the_first_header_pointer_are_skipped_when_nothing_is_pending():
    y, d = pkt(0x77, b"q"), pkt(0x30, body(3, 60))
    assert len(y) == 7 and len(d) == 9
    vc = VirtualChannelReceiver(1)
    got = vc.process_frame_data(0, 7, y + d)                        # the first seven octets are the end of a packet never begun
    assert [g.raw_packet for g in got] == [d]


def test_two_packets_filling_the_field_exactly_are_both_delivered_at_once():
    a, d = pkt(0x10, body(3, 1)), pkt(0x30, b"k")
    assert len(a) + len(d) == 16
    vc = VirtualChannelReceiver(1)
    got = vc.process_frame_data(0, 0, a + d)
    assert [g.raw_packet for g in got] == [a, d] and len(vc.assembly_buffer) == 0


def test_extraction_stops_at_idle_packets_and_at_other_versions():
    a, d = pkt(0x10, b"k"), pkt(0x30, b"m")
    idle = pkt(0x7FF, b"i")
    vc = VirtualChannelReceiver(1)
    assert [g.raw_packet for g in vc.process_frame_data(0, 0, a + idle + d)] == [a]
    almost_idle = pkt(0x7FE, b"i")
    assert [g.raw_packet for g in vc.process_frame_data(1, 0, a + almost_idle + d)] == [a, almost_idle, d]
    for version in (1, 2, 4, 7):
        other = pkt(0x31, b"v", version=version)
        vc = VirtualChannelReceiver(1)
        assert [g.raw_packet for g in vc.process_frame_data(0, 0, a + other + d)] == [a]
    assert [g.apid for g in parse_space_packets(a + pkt(0x31, b"v", version=1) + d)] == [0x10, 0x30]


def test_fragment_too_short_to_hold_a_header_is_dropped_without_error():
    a, p, d = pkt(0x10, body(8, 1)), pkt(0x155, body(16, 7)), pkt(0x30, body(9, 60))
    assert len(a) == 14 and len(d) == 15
    vc = VirtualChannelReceiver(1)
    vc.process_frame_data(0, 0, a + p[:2])
    got = vc.process_frame_data(1, 1, p[2:3] + d)
    assert [g.raw_packet for g in got] == [d]


@pytest.mark.parametrize("ptype,sec,flags,seq,apid", [(1, 0, 0, 0x3FFF, 0x555), (0, 1, 1, 0x2AAA, 0x2AA), (1, 1, 2, 0x1555, 0x7FE),
                                                      (0, 0, 3, 1, 1), (1, 0, 3, 0, 0x400), (0, 1, 0, 0x2000, 0x3FF)])
def test_every_field_of_the_primary_header(ptype, sec, flags, seq, apid):
    raw = pkt(apid, body(5, 9), seq=seq, flags=flags, ptype=ptype, sec=sec)
    got = parse_space_packets(raw)
    assert len(got) == 1
    g = got[0]
    assert (g.packet_type, g.sec_hdr_flag, g.seq_flags, g.seq_count, g.apid) == (ptype, sec, flags, seq, apid)
    assert g.length == 11 and g.payload == body(5, 9) and g.raw_packet == raw and g.timestamp_utc is None


def test_time_code_needs_six_octets_and_the_secondary_header_flag():
    t = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    code = encode_cuc(t, coarse_octets=4, fine_octets=2, p_field=False)
    assert len(code) == 6
    assert parse_space_packets(pkt(0x21, code, sec=1))[0].timestamp_utc == t           # exactly six octets of data
    assert parse_space_packets(pkt(0x21, code + b"x", sec=1))[0].timestamp_utc == t
    assert parse_space_packets(pkt(0x21, code[:5], sec=1))[0].timestamp_utc is None
    assert parse_space_packets(pkt(0x21, code, sec=0))[0].timestamp_utc is None


def test_stream_of_packets_ends_at_the_first_incomplete_one():
    a, d = pkt(0x10, body(3, 1)), pkt(0x30, body(4, 60))
    assert [g.raw_packet for g in parse_space_packets(a + d)] == [a, d]
    for cut in range(1, len(d)):
        assert [g.raw_packet for g in parse_space_packets(a + d[:-cut])] == [a]
    assert parse_space_packets(b"") == [] and parse_space_packets(a[:6]) == []


def test_frames_without_error_control_field():
    a, d = pkt(0x10, body(5, 1)), pkt(0x30, body(7, 60) + CCSDS_ASM)             # the first frame ENDS with the sync pattern
    assert len(a) + len(d) == 11 + 17
    engine = CcsdsTransferFrameEngine(frame_length=8 + 28, has_fecf=False)
    first = aos(0, 0, a + d, 36, fecf=False)
    assert first.endswith(CCSDS_ASM)
    header, data = engine.parse_frame(first)
    assert header.fecf_valid is True and header.fecf_received == 0 and data == a + d and len(data) == 28
    assert (header.tfvn, header.scid, header.vcid, header.vcfc, header.fhp, header.replay_flag) == (1, 0x5A, 3, 0, 0, False)
    c = pkt(0x20, body(22, 30))
    second = aos(1, 0, c, 36, fecf=False)
    engine = CcsdsTransferFrameEngine(frame_length=36, has_fecf=False)
    got = engine.process_raw_stream(CCSDS_ASM + first + CCSDS_ASM + second)
    assert [g.raw_packet for g in got] == [a, d, c] and engine.total_synced_frames == 2 and engine.crc_errors == 0
    assert engine.virtual_channels[3].frames_dropped == 0


def test_tm_frame_with_an_odd_first_header_pointer_and_no_secondary_header():
    d = pkt(0x30, body(9, 60))
    data = body(3, 200) + d
    length = 6 + len(data) + 2
    w1 = (0x155 << 4) | (5 << 1)
    frame = struct.pack(">HBBH", w1, 9, 17, 0x1800 | 3) + data
    frame += struct.pack(">H", compute_crc16_ccitt(frame))
    engine = CcsdsTransferFrameEngine(frame_length=length)
    header, field = engine.parse_frame(frame)
    assert (header.tfvn, header.scid, header.vcid, header.vcfc, header.fhp) == (0, 0x155, 5, 17, 3) and field == data
    assert [g.raw_packet for g in engine.process_raw_stream(CCSDS_ASM + frame)] == [d]


@pytest.mark.parametrize("missing", [1, 2, 3, 4, 5, 8, 20])
def test_stream_cut_inside_the_last_frame_gives_the_frames_before_it_and_no_error(missing):
    a, c = pkt(0x10, body(18, 1)), pkt(0x20, body(18, 30))
    first, second = aos(0, 0, a, 34), aos(1, 0, c, 34)
    engine = CcsdsTransferFrameEngine(frame_length=34)
    stream = CCSDS_ASM + first + CCSDS_ASM + second
    assert [g.raw_packet for g in engine.process_raw_stream(stream[:-missing])] == [a] and engine.total_synced_frames == 1
    engine = CcsdsTransferFrameEngine(frame_length=34)
    assert engine.process_raw_stream((CCSDS_ASM + first)[:-missing]) == [] and engine.total_synced_frames == 0


@pytest.mark.parametrize("junk", [1, 2, 3, 4, 5, 7])
def test_octets_before_the_sync_marker_are_skipped_one_at_a_time(junk):
    a, c = pkt(0x10, body(18, 1)), pkt(0x20, body(18, 30))
    first, second = aos(0, 0, a, 34), aos(1, 0, c, 34)
    engine = CcsdsTransferFrameEngine(frame_length=34)
    stream = bytes([0x55]) * junk + CCSDS_ASM + first + bytes([0xAA]) * junk + CCSDS_ASM + second
    assert [g.raw_packet for g in engine.process_raw_stream(stream)] == [a, c] and engine.total_synced_frames == 2
