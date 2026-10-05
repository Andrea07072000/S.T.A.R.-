# SPDX-License-Identifier: Apache-2.0
"""Regression for the CCSDS pseudo-randomizer (found 2026-10-04 by mutation review: exported and imported by two test
files, never checked against a value; output was ff1aaf66.. instead of the published sequence) plus the constants
whose mutants survived. Reference: CCSDS 131.0-B pseudo-randomizer, h(x) = x^8 + x^7 + x^5 + x^3 + 1, all-ones seed."""
import pytest

from star_telemetry import CCSDS_ASM, compute_crc16_ccitt, generate_ccsds_randomizer_sequence
from star_telemetry.engine import DEFAULT_FRAME_SIZE, parse_space_packets

PUBLISHED_HEAD = bytes.fromhex("ff480ec09a0d70bc8e2c93ada7b746ce5a977dcc32a2bf3e0a10f18894cdeab1")


def bits(seq):
    return [(b >> (7 - i)) & 1 for b in seq for i in range(8)]


def test_randomizer_matches_published_head():
    assert generate_ccsds_randomizer_sequence(len(PUBLISHED_HEAD)) == PUBLISHED_HEAD


def test_randomizer_obeys_the_recurrence_and_has_period_255_bits():
    s = bits(generate_ccsds_randomizer_sequence(300))
    assert all(s[n + 8] == s[n + 7] ^ s[n + 5] ^ s[n + 3] ^ s[n] for n in range(len(s) - 8))
    assert s[255:510] == s[:255] and s[1:256] != s[:255]


def test_randomizer_default_length_and_self_inverse():
    pn = generate_ccsds_randomizer_sequence()
    assert len(pn) == 4096
    data = bytes(range(256)) * 2
    once = bytes(a ^ b for a, b in zip(data, pn))
    assert once != data and bytes(a ^ b for a, b in zip(once, pn)) == data


def test_constants():
    assert CCSDS_ASM == bytes.fromhex("1acffc1d") and DEFAULT_FRAME_SIZE == 1115
    assert compute_crc16_ccitt(b"123456789") == 0x29B1          # CRC-16/CCITT-FALSE check value
    assert compute_crc16_ccitt(b"") == 0xFFFF


def pkt(apid, payload, seq=0):
    n = len(payload) - 1
    return bytes([(apid >> 8) & 0x07, apid & 0xFF, 0xC0 | (seq >> 8), seq & 0xFF, n >> 8, n & 0xFF]) + payload


@pytest.mark.parametrize("tail", [b"", b"\x00", b"\x00" * 5])
def test_stream_parser_stops_cleanly_on_short_tail(tail):
    data = pkt(5, b"A") + pkt(6, b"BC") + tail
    out = parse_space_packets(data)
    assert [(p.apid, p.payload) for p in out] == [(5, b"A"), (6, b"BC")]


def test_stream_parser_exact_boundary_and_truncated_packet():
    one = pkt(7, b"XYZ")
    assert [p.length for p in parse_space_packets(one)] == [9]          # idx + len == len(data) must be accepted
    assert parse_space_packets(one[:-1]) == []                          # one byte short: nothing
    assert parse_space_packets(one[:6]) == []                           # header only


def test_space_packet_and_virtual_channel_receiver_direct():
    # rewritten 2026-10-05: the first version called an API that does not exist (version=, cuc_coarse=,
    # vc_id=, push_data) and failed; this one exercises the real exported classes
    from star_telemetry import SpacePacket, VirtualChannelReceiver
    p = SpacePacket(apid=42, packet_type=0, sec_hdr_flag=0, seq_flags=3, seq_count=101, length=13,
                    payload=b"PAYLOAD", raw_packet=b"")
    assert (p.apid, p.seq_count, p.payload, p.timestamp_utc) == (42, 101, b"PAYLOAD", None)
    rx = VirtualChannelReceiver(vcid=1)
    assert (rx.vcid, rx.last_vcfc, rx.frames_received, rx.frames_dropped) == (1, None, 0, 0)
    data = pkt(9, b"HELLO").ljust(40, bytes([0xE0]))
    out = rx.process_frame_data(0, 0, data)
    assert [(q.apid, q.payload) for q in out] == [(9, b"HELLO")] and rx.reassembled_packets == out
    rx.process_frame_data(3, 2047, b"")                     # counts 1 and 2 missing: 2 frames dropped
    assert rx.frames_dropped == 2 and rx.frames_received == 2


@pytest.mark.parametrize("version", range(1, 8))
def test_packet_version_other_than_zero_is_not_a_valid_packet(version):
    p = bytearray(pkt(5, b"A"))
    p[0] |= version << 5
    assert parse_space_packets(bytes(p)) == []
    assert [q.apid for q in parse_space_packets(pkt(5, b"A"))] == [5]
