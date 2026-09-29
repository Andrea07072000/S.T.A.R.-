# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""CCSDS CUC Level 1: P-field values from the standard, an independent cross-check with ERFA, round trips,
leap seconds and refusals."""

import random
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

from star_timescales import (
    LEAP_SECONDS,
    CucFormatError,
    NaiveDatetimeError,
    cuc_p_field,
    cuc_to_utc,
    decode_cuc,
    encode_cuc,
)

UTC = timezone.utc


@pytest.mark.req("TS-REQ-008")
@pytest.mark.parametrize("coarse, fine, expected", [(4, 2, 0x1E), (4, 3, 0x1F), (4, 0, 0x1C), (1, 0, 0x10),
                                                    (2, 1, 0x15)])
def test_p_field_follows_the_standard_layout(coarse, fine, expected):
    assert cuc_p_field(coarse, fine) == expected


@pytest.mark.req("TS-REQ-008")
def test_a_known_instant_by_hand():
    # 1958-01-01 -> 1972-01-01 is 14 years with 3 leap days (1960, 1964, 1968): 5113 days;
    # at 1972-01-01 UTC, TAI - UTC = 10 s. Half a second is 0x8000 in two fine octets.
    code = encode_cuc(datetime(1972, 1, 1, 0, 0, 0, 500000, tzinfo=UTC))
    assert code == bytes([0x1E]) + (5113 * 86400 + 10).to_bytes(4, "big") + bytes([0x80, 0x00])
    assert decode_cuc(code) == Fraction(5113 * 86400 + 10) + Fraction(1, 2)


def _instants():
    rng = random.Random(1958)
    out = []
    for effective, _mjd, _offset in LEAP_SECONDS:
        for delta in (-1, 0, 1, 86400 * 100):
            out.append(effective + timedelta(seconds=delta))
    start = datetime(1972, 1, 1, tzinfo=UTC)
    span = int((datetime(2027, 6, 1, tzinfo=UTC) - start).total_seconds())
    out += [start + timedelta(seconds=rng.randrange(span), microseconds=rng.randrange(10**6)) for _ in range(300)]
    return [t for t in out if datetime(1972, 1, 1, tzinfo=UTC) <= t < datetime(2027, 6, 28, tzinfo=UTC)]


@pytest.mark.req("TS-REQ-009")
def test_agrees_with_erfa_utc_to_tai():
    erfa = pytest.importorskip("erfa")
    e1, e2 = erfa.dtf2d("TAI", 1958, 1, 1, 0, 0, 0.0)
    for t in _instants():
        u1, u2 = erfa.dtf2d("UTC", t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
        a1, a2 = erfa.utctai(u1, u2)
        reference = ((a1 - e1) + (a2 - e2)) * 86400.0
        ours = decode_cuc(encode_cuc(t, fine_octets=3))
        # ERFA works on two-part Julian dates in floating point: agreement is bounded by its noise (~1e-6 s)
        assert abs(float(ours) - reference) < 2e-6, t


@pytest.mark.req("TS-REQ-008")
def test_round_trip_is_exact_to_the_microsecond_with_three_fine_octets():
    for t in _instants():
        assert cuc_to_utc(encode_cuc(t, fine_octets=3)) == t


@pytest.mark.req("TS-REQ-008")
def test_resolution_bound_with_fewer_fine_octets():
    for t in _instants()[:80]:
        for fine in (0, 1, 2):
            back = cuc_to_utc(encode_cuc(t, fine_octets=fine))
            assert timedelta(0) <= t - back <= timedelta(seconds=1 / 256 ** fine) + timedelta(microseconds=1)


@pytest.mark.req("TS-REQ-008")
def test_the_code_is_continuous_across_a_leap_second():
    before = decode_cuc(encode_cuc(datetime(2016, 12, 31, 23, 59, 59, tzinfo=UTC)))
    after = decode_cuc(encode_cuc(datetime(2017, 1, 1, tzinfo=UTC)))
    assert after - before == 2                           # 23:59:60 was inserted between them


@pytest.mark.req("TS-REQ-008")
def test_an_instant_inside_a_leap_second_is_refused_when_decoding():
    before = encode_cuc(datetime(2016, 12, 31, 23, 59, 59, tzinfo=UTC), p_field=False)
    inside = (int.from_bytes(before[:4], "big") + 1).to_bytes(4, "big") + before[4:]   # 23:59:60
    with pytest.raises(ValueError, match="leap second"):
        cuc_to_utc(inside, 4, 2)


@pytest.mark.req("TS-REQ-008")
def test_implicit_p_field_and_refusals():
    t = datetime(2026, 9, 28, tzinfo=UTC)
    assert decode_cuc(encode_cuc(t, p_field=False), 4, 2) == decode_cuc(encode_cuc(t))
    with pytest.raises(CucFormatError):
        encode_cuc(t, coarse_octets=1)                    # does not fit in one octet
    with pytest.raises(CucFormatError):
        encode_cuc(t, coarse_octets=5)
    with pytest.raises(CucFormatError):
        decode_cuc(encode_cuc(t)[:-1])                    # truncated
    with pytest.raises(CucFormatError):
        decode_cuc(bytes([0x2E]) + bytes(6))              # time code id 010: not Level 1
    with pytest.raises(CucFormatError):
        decode_cuc(bytes([0x9E]) + bytes(6))              # extended P-field
    with pytest.raises(CucFormatError):
        decode_cuc(bytes(6), 4, None)
    with pytest.raises(NaiveDatetimeError):
        encode_cuc(datetime(2026, 9, 28))
