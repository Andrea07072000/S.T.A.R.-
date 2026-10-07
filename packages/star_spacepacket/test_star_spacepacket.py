"""star_spacepacket against published CCSDS header values, hand derivations, inverses and edge invariants.
Verifies behaviour only (not refusals).
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""


import star_spacepacket as sp


def test_published_headers_and_decoding():
    assert sp.encode_header(0x123, 42, 1, secondary_header=True) == bytes.fromhex("0923c02a0001")
    assert sp.encode_header(2047, 0, 0) == bytes.fromhex("07ffc0000000")
    assert sp.encode_header(0, 0, 0, packet_type=1, sequence_flags=0) == bytes.fromhex("100000000000")
    assert sp.encode_header(2047, 16383, 65535, 1, True, 3) == bytes.fromhex("1fffffffffff")

    h = sp.decode_header(bytes.fromhex("0923c02a0001"))
    assert h == sp.Header(0x123, 0, True, 3, 42, 1)
    assert sp.decode_header(bytes.fromhex("1fffffffffff")) == sp.Header(2047, 1, True, 3, 16383, 65535)


def test_constants_and_default_layout_bits():
    assert sp.TELEMETRY == 0 and sp.TELECOMMAND == 1
    assert (sp.CONTINUATION, sp.FIRST, sp.LAST, sp.UNSEGMENTED) == (0, 1, 2, 3)
    assert sp.IDLE_APID == 2047
    assert sp.HEADER_OCTETS == 6 and sp.MAX_DATA_OCTETS == 65536

    # Hand derivation from bit layout with defaults (telemetry, no secondary header, unsegmented):
    # first word: 000 0 0 + APID 1 => 0000000000000001 = 0x0001
    # second: flags 11 + count 0 => 1100000000000000 = 0xC000
    # length 0 => 0x0000
    assert sp.encode_header(1, 0, 0) == bytes.fromhex("0001c0000000")

    base = bytearray(sp.encode_header(0, 0, 0))
    assert base == bytearray.fromhex("0000c0000000")
    assert sp.encode_header(0x7FF, 0, 0)[:2] == bytes.fromhex("07ff")  # APID occupies low 3 bits of octet0 + octet1
    assert sp.encode_header(0, 0, 0, packet_type=1)[0] == (base[0] | 0x10)
    assert sp.encode_header(0, 0, 0, secondary_header=True)[0] == (base[0] | 0x08)
    assert sp.encode_header(0, 0, 0, sequence_flags=1)[2] == 0x40
    assert sp.encode_header(0, 0, 0, sequence_flags=2)[2] == 0x80
    assert sp.encode_header(0, 0, 0, sequence_flags=3)[2] == 0xC0
    assert sp.encode_header(0, 0x3FFF, 0)[2:4] == bytes.fromhex("ffff")  # 0xC000 | 0x3FFF = 0xFFFF
    assert sp.encode_header(0, 0, 0x1234)[4:6] == bytes.fromhex("1234")


def test_roundtrip_and_packet_shapes():
    # Non-symmetric values so each decoded field is decided independently.
    hdr = sp.encode_header(0x456, 0x1234, 0x2345, packet_type=1, secondary_header=True, sequence_flags=2)
    assert len(hdr) == 6
    assert sp.decode_header(hdr) == sp.Header(0x456, 1, True, 2, 0x1234, 0x2345)

    pkt = sp.encode_packet(0x123, 42, b"AB", secondary_header=True)
    assert pkt == bytes.fromhex("0923c02a00014142")
    h, data = sp.decode_packet(pkt)
    assert h == sp.Header(0x123, 0, True, 3, 42, 1) and data == b"AB"

    idle = sp.encode_packet(2047, 0, b"\x00")
    assert len(idle) == 7  # 6-byte header + 1-byte data field

    big = sp.encode_packet(1, 2, b"\xAA" * 65536)
    assert len(big) == 65542
    assert big[4:6] == b"\xff\xff"


def test_decode_header_accepts_all_bytes_like_and_split_packets_invariant():
    h = bytes.fromhex("0923c02a0001")
    assert sp.decode_header(h) == sp.decode_header(bytearray(h)) == sp.decode_header(memoryview(h))

    p1 = sp.encode_packet(1, 10, b"XYZ")
    p2 = sp.encode_packet(sp.IDLE_APID, 0, b"\x00")
    p3 = sp.encode_packet(3, 7, b"ABCD", packet_type=1, sequence_flags=sp.FIRST)
    stream = p1 + p2 + p3
    parts = sp.split_packets(stream)
    assert parts == [p1, p2, p3]
    assert b"".join(parts) == stream
    assert sp.split_packets(b"") == []


def test_next_count_edges_and_linear_region():
    assert sp.next_count(0) == 1
    assert sp.next_count(1) == 2
    assert sp.next_count(16382) == 16383
    assert sp.next_count(16383) == 0
