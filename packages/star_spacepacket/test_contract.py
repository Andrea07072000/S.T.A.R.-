"""Refusals and boundary contracts of star_spacepacket with pinned hostile values.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_spacepacket as sp

HOSTILE = [1.0, "1", None, True]


def test_pinned_constants_and_hostile_set():
    assert sp.__version__ == "0.1.1"
    assert len(HOSTILE) == 4
    assert sp.IDLE_APID == 2047 and sp.HEADER_OCTETS == 6 and sp.MAX_DATA_OCTETS == 65536


@pytest.mark.parametrize("bad", HOSTILE + [-1, 2048])
def test_encode_header_apid_refusals(bad):
    with pytest.raises(ValueError, match="apid must be an integer from 0 to 2047"):
        sp.encode_header(bad, 0, 0)


@pytest.mark.parametrize("bad", HOSTILE + [-1, 16384])
def test_encode_header_sequence_count_refusals(bad):
    with pytest.raises(ValueError, match="sequence_count must be an integer from 0 to 16383"):
        sp.encode_header(0, bad, 0)


@pytest.mark.parametrize("bad", HOSTILE + [-1, 65536])
def test_encode_header_data_length_refusals(bad):
    with pytest.raises(ValueError, match="data_length must be an integer from 0 to 65535"):
        sp.encode_header(0, 0, bad)


@pytest.mark.parametrize("bad", HOSTILE + [-1, 2])
def test_encode_header_packet_type_refusals(bad):
    with pytest.raises(ValueError, match="packet_type must be an integer from 0 to 1"):
        sp.encode_header(0, 0, 0, packet_type=bad)


@pytest.mark.parametrize("bad", HOSTILE + [-1, 4])
def test_encode_header_sequence_flags_refusals(bad):
    with pytest.raises(ValueError, match="sequence_flags must be an integer from 0 to 3"):
        sp.encode_header(0, 0, 0, sequence_flags=bad)


@pytest.mark.parametrize("bad", [0, 1, None, "yes"])
def test_encode_header_secondary_header_type_refusals(bad):
    with pytest.raises(ValueError, match="secondary_header must be True or False"):
        sp.encode_header(0, 0, 0, secondary_header=bad)


def test_range_limits_just_inside_for_encode_header():
    assert len(sp.encode_header(0, 0, 0, 0, False, 0)) == 6
    assert len(sp.encode_header(2047, 16383, 65535, 1, True, 3)) == 6


@pytest.mark.parametrize("bad_data", ["abc", [65, 66], None])
def test_encode_packet_data_must_be_bytes_like(bad_data):
    with pytest.raises(ValueError, match="data must be bytes-like"):
        sp.encode_packet(0, 0, bad_data)


@pytest.mark.parametrize("n", [0, 65537])
def test_encode_packet_data_length_refusals(n):
    with pytest.raises(ValueError, match="from 1 to 65536 octets"):
        sp.encode_packet(0, 0, b"\x00" * n)


def test_encode_packet_data_length_limits_inside():
    assert len(sp.encode_packet(0, 0, b"\x00")) == 7
    assert len(sp.encode_packet(0, 0, b"\x00" * 65536)) == 65542


@pytest.mark.parametrize("bad", ["x", 123, None])
def test_decode_header_not_bytes_like_refused(bad):
    with pytest.raises(ValueError, match="octets must be bytes-like"):
        sp.decode_header(bad)


@pytest.mark.parametrize("n", [0, 5, 7])
def test_decode_header_size_refused(n):
    with pytest.raises(ValueError, match="a primary header has 6 octets"):
        sp.decode_header(b"\x00" * n)


@pytest.mark.parametrize("b0", [0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0, 0xE0])
def test_decode_header_version_nonzero_refused(b0):
    with pytest.raises(ValueError, match="packet version number must be 0"):
        sp.decode_header(bytes([b0, 0, 0, 0, 0, 0]))


NOT_NUMBERS = [float("nan"), float("inf"), float("-inf"), 1e300, 2.5, 1 + 0j]


@pytest.mark.parametrize("bad", NOT_NUMBERS)
def test_nan_and_inf_are_refused_in_every_integer_field(bad):
    """Added by the reviewer (0.1.1): the drafted contract had no NaN or infinity among its hostile values."""
    good = dict(apid=1, sequence_count=2, data_length=3, packet_type=0, sequence_flags=3)
    for field in good:
        with pytest.raises(ValueError, match=f"{field} must be an integer"):
            sp.encode_header(**dict(good, **{field: bad}))
    with pytest.raises(ValueError, match="apid must be an integer"):
        sp.encode_packet(bad, 0, b"x")
    with pytest.raises(ValueError, match="sequence_count must be an integer"):
        sp.next_count(bad)
    with pytest.raises(ValueError, match="secondary_header must be True or False"):
        sp.encode_header(1, 2, 3, secondary_header=bad)
    for call in (sp.decode_header, sp.decode_packet, sp.split_packets):
        with pytest.raises(ValueError, match="bytes-like"):
            call(bad)


def test_every_truncation_of_a_packet_is_refused():
    packet = sp.encode_packet(0x155, 77, bytes(range(40)), sp.TELECOMMAND, True, sp.LAST)
    for cut in range(len(packet)):                           # every proper prefix, the empty one included
        with pytest.raises(ValueError):
            sp.decode_packet(packet[:cut])
        if cut:
            with pytest.raises(ValueError, match="the stream ends inside"):
                sp.split_packets(packet + packet[:cut])
    assert sp.split_packets(packet + packet) == [packet, packet]
