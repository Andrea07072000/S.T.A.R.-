"""Guard tests of star_spacepacket written by the reviewer: an independent oracle (the header written as a string of 48
binary digits, field after field, as the standard draws it), every field alone and at its ends, exact boundaries of
the lengths, and every refusal by name."""
import random

import pytest

import star_spacepacket as ssp
from star_spacepacket import Header


def by_bits(apid, count, length, ptype, sec, flags):
    """The 48 bits in the order of CCSDS 133.0-B-2, figure 4-2: 3 + 1 + 1 + 11 + 2 + 14 + 16."""
    bits = "000" + format(ptype, "01b") + ("1" if sec else "0") + format(apid, "011b") + format(flags, "02b") + format(count, "014b") + format(length, "016b")
    assert len(bits) == 48
    return bytes(int(bits[k:k + 8], 2) for k in range(0, 48, 8))


def test_headers_written_out_by_hand():
    assert ssp.encode_header(0x123, 42, 1, secondary_header=True) == bytes.fromhex("0923c02a0001")
    assert ssp.encode_header(2047, 0, 0) == bytes.fromhex("07ffc0000000")                 # the idle packet of one octet
    assert ssp.encode_header(0, 0, 0, packet_type=1, sequence_flags=0) == bytes.fromhex("100000000000")
    assert ssp.encode_header(2047, 16383, 65535, 1, True, 3) == bytes.fromhex("1fffffffffff")
    assert ssp.encode_header(1, 0, 0) == bytes.fromhex("0001c0000000")                    # defaults: telemetry, no secondary header, unsegmented
    assert ssp.encode_header(0, 0, 0, ssp.TELEMETRY, False, ssp.CONTINUATION) == bytes(6)


def test_each_field_alone_lands_on_its_own_bits():
    zero = dict(apid=0, sequence_count=0, data_length=0, packet_type=0, secondary_header=False, sequence_flags=0)
    for field, value, expected in (("apid", 0x7FF, "07ff00000000"), ("apid", 0x400, "040000000000"), ("apid", 0x0FF, "00ff00000000"), ("apid", 0x100, "010000000000"),
                                   ("packet_type", 1, "100000000000"), ("secondary_header", True, "080000000000"),
                                   ("sequence_flags", 1, "000040000000"), ("sequence_flags", 2, "000080000000"), ("sequence_flags", 3, "0000c0000000"),
                                   ("sequence_count", 0x3FFF, "00003fff0000"), ("sequence_count", 0x2000, "000020000000"), ("sequence_count", 0x00FF, "000000ff0000"),
                                   ("sequence_count", 0x0100, "000001000000"), ("data_length", 0x1234, "000000001234"), ("data_length", 0xFF00, "00000000ff00"),
                                   ("data_length", 0x00FF, "0000000000ff"), ("data_length", 0xFFFF, "00000000ffff")):
        fields = dict(zero, **{field: value})
        octets = ssp.encode_header(**fields)
        assert octets == bytes.fromhex(expected), field
        decoded = ssp.decode_header(octets)
        assert decoded == Header(**fields) and getattr(decoded, field) == value


def test_against_the_header_written_bit_by_bit():
    rnd = random.Random(133)
    for _ in range(3000):
        fields = (rnd.choice([0, 1, 2046, 2047, rnd.randint(0, 2047)]), rnd.choice([0, 16383, rnd.randint(0, 16383)]), rnd.choice([0, 65535, rnd.randint(0, 65535)]),
                  rnd.randint(0, 1), rnd.random() < 0.5, rnd.randint(0, 3))
        octets = ssp.encode_header(*fields)
        assert octets == by_bits(*fields) and len(octets) == 6
        back = ssp.decode_header(octets)
        assert (back.apid, back.sequence_count, back.data_length, back.packet_type, back.secondary_header, back.sequence_flags) == fields
        assert isinstance(back.secondary_header, bool) and all(type(v) is int for v in (back.apid, back.sequence_count, back.data_length, back.packet_type, back.sequence_flags))


def test_constants_and_header_type():
    assert (ssp.TELEMETRY, ssp.TELECOMMAND, ssp.CONTINUATION, ssp.FIRST, ssp.LAST, ssp.UNSEGMENTED, ssp.IDLE_APID) == (0, 1, 0, 1, 2, 3, 2047)
    assert (ssp.HEADER_OCTETS, ssp.MAX_DATA_OCTETS, ssp.__version__) == (6, 65536, "0.1.1")
    assert Header._fields == ("apid", "packet_type", "secondary_header", "sequence_flags", "sequence_count", "data_length")
    assert ssp.decode_header(bytes.fromhex("0923c02a0001")) == (0x123, 0, True, 3, 42, 1)
    assert ssp.decode_header(bytearray.fromhex("1fffffffffff")) == (2047, 1, True, 3, 16383, 65535)
    assert ssp.decode_header(memoryview(bytes.fromhex("100000000000"))) == (0, 1, False, 0, 0, 0)


def test_packets_and_their_lengths():
    assert ssp.encode_packet(0x123, 42, b"AB", secondary_header=True) == bytes.fromhex("0923c02a00014142")
    assert ssp.encode_packet(2047, 0, bytes(1)) == bytes.fromhex("07ffc000000000")
    assert ssp.encode_packet(7, 9, bytearray(b"xyz"), ssp.TELECOMMAND, False, ssp.FIRST) == bytes.fromhex("100740090002") + b"xyz"
    assert ssp.decode_packet(bytes.fromhex("0923c02a00014142")) == (Header(0x123, 0, True, 3, 42, 1), b"AB")
    for size in (1, 2, 255, 256, 257, 65535, 65536):
        packet = ssp.encode_packet(5, 7, bytes(size))
        assert len(packet) == 6 + size and int.from_bytes(packet[4:6], "big") == size - 1
        header, data = ssp.decode_packet(packet)
        assert header.data_length == size - 1 and data == bytes(size) and isinstance(data, bytes)
    for size in (0, 65537):
        with pytest.raises(ValueError, match="the data field must have from 1 to 65536 octets"):
            ssp.encode_packet(5, 7, bytes(size))
    whole = ssp.encode_packet(5, 7, b"abcd")
    for wrong in (whole[:-1], whole + b"e", whole[:6], whole + whole):
        with pytest.raises(ValueError, match="the header declares a packet of 10 octets"):
            ssp.decode_packet(wrong)
    for short in (b"", whole[:1], whole[:5]):
        with pytest.raises(ValueError, match="a packet has at least 7 octets"):
            ssp.decode_packet(short)


def test_streams_are_split_whole_or_refused_with_the_place():
    a, idle, b, c = ssp.encode_packet(1, 0, b"a"), ssp.encode_packet(ssp.IDLE_APID, 0, bytes(3)), ssp.encode_packet(2, 16383, b"bcd", 1, True, 2), ssp.encode_packet(3, 5, bytes(300))
    assert ssp.split_packets(b"") == [] and ssp.split_packets(a) == [a]
    assert ssp.split_packets(a + idle + b + c) == [a, idle, b, c]                          # the idle packet is returned like the others
    assert ssp.split_packets(bytearray(a + b)) == [a, b] and all(isinstance(p, bytes) for p in ssp.split_packets(memoryview(a + b)))
    start = len(a) + len(idle)
    for cut in (1, 2, 5):
        with pytest.raises(ValueError, match=f"the stream ends inside a header at octet {start}$"):
            ssp.split_packets(a + idle + b[:cut])
    with pytest.raises(ValueError, match=f"the stream ends inside the packet that starts at octet {start}: 3 octets missing"):
        ssp.split_packets(a + idle + b[:6])
    with pytest.raises(ValueError, match=f"the stream ends inside the packet that starts at octet {start}: 1 octets missing"):
        ssp.split_packets(a + idle + b[:-1])
    with pytest.raises(ValueError, match="the stream ends inside a header at octet 7$"):
        ssp.split_packets(a + bytes(1))
    for version in range(1, 8):
        damaged = bytes([b[0] | (version << 5)]) + b[1:]
        with pytest.raises(ValueError, match=f"packet version number must be 0, got {version} at octet {start}$"):
            ssp.split_packets(a + idle + damaged + c)
        with pytest.raises(ValueError, match=f"packet version number must be 0, got {version}$"):
            ssp.decode_header(damaged[:6])
        with pytest.raises(ValueError, match=f"packet version number must be 0, got {version}$"):
            ssp.decode_packet(damaged)


def test_sequence_count_wraps_at_14_bits():
    assert [ssp.next_count(c) for c in (0, 1, 16382, 16383)] == [1, 2, 16383, 0]
    count = 16380
    seen = []
    for _ in range(6):
        seen.append(count)
        count = ssp.next_count(count)
    assert seen == [16380, 16381, 16382, 16383, 0, 1]
    for bad in (-1, 16384, 1.0, True, None, "3"):
        with pytest.raises(ValueError, match="sequence_count must be an integer from 0 to 16383"):
            ssp.next_count(bad)


def test_refusals_name_the_field():
    good = dict(apid=1, sequence_count=2, data_length=3, packet_type=0, secondary_header=False, sequence_flags=3)
    for field, highest in (("apid", 2047), ("sequence_count", 16383), ("data_length", 65535), ("packet_type", 1), ("sequence_flags", 3)):
        assert ssp.encode_header(**dict(good, **{field: highest})) and ssp.encode_header(**dict(good, **{field: 0}))
        for bad in (-1, highest + 1, 1.0, "1", None, True, False, 1 + 0j):
            with pytest.raises(ValueError, match=f"{field} must be an integer from 0 to {highest},"):
                ssp.encode_header(**dict(good, **{field: bad}))
    for bad in (0, 1, None, "yes", 1.0):
        with pytest.raises(ValueError, match="secondary_header must be True or False"):
            ssp.encode_header(**dict(good, secondary_header=bad))
        with pytest.raises(ValueError, match="secondary_header must be True or False"):
            ssp.encode_packet(1, 2, b"x", secondary_header=bad)
    for bad in (2048, -1, True):
        with pytest.raises(ValueError, match="apid must be an integer from 0 to 2047"):
            ssp.encode_packet(bad, 0, b"x")
    for bad in ("AB", [65, 66], None, 65, ("A",)):
        with pytest.raises(ValueError, match="data must be bytes-like"):
            ssp.encode_packet(1, 2, bad)
        with pytest.raises(ValueError, match="octets must be bytes-like"):
            ssp.decode_header(bad)
        with pytest.raises(ValueError, match="octets must be bytes-like"):
            ssp.decode_packet(bad)
        with pytest.raises(ValueError, match="stream must be bytes-like"):
            ssp.split_packets(bad)
    for size in (0, 1, 5, 7, 12):
        with pytest.raises(ValueError, match=f"a primary header has 6 octets, got {size}"):
            ssp.decode_header(bytes(size))
