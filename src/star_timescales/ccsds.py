# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""CCSDS Unsegmented Time Code (CUC), Level 1: TAI seconds since 1958-01-01, as flown in telemetry.

Reference: CCSDS 301.0-B-4, *Time Code Formats* (Blue Book), section 3.2. Level 1 means the time scale is TAI
and the epoch is 1958 January 1, 00:00:00 TAI, so the code needs no agency-specific definition.

The code is ``[P-field] T-field``:

* **P-field** (one octet, basic form): extension flag 0, time code identification ``001`` (Level 1),
  number of coarse octets minus one (2 bits), number of fine octets (2 bits).
  4 coarse + 2 fine octets gives the familiar ``0x1E``.
* **T-field**: whole TAI seconds as a big-endian unsigned integer (1-4 octets), then the fraction of a second
  as a binary fraction (0-3 octets), truncated, as the standard specifies.

Scope, stated rather than hidden: only the basic one-octet P-field (up to 4 coarse and 3 fine octets);
UTC instants from 1972-01-01 to the end of the leap-second table; instants inside an inserted leap second
(23:59:60) are not representable by ``datetime`` and are refused when decoding.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fractions import Fraction

from .leap_seconds import LEAP_SECONDS, _as_utc, tai_minus_utc

#: The Level 1 epoch, as a TAI calendar label.
CUC_EPOCH_TAI: datetime = datetime(1958, 1, 1, tzinfo=timezone.utc)
_LEVEL1_ID = 0b001
_SECOND = timedelta(seconds=1)


class CucFormatError(ValueError):
    """The octet counts, the P-field or the length of a CUC code are not valid, or the value does not fit."""


def cuc_p_field(coarse_octets: int = 4, fine_octets: int = 2) -> int:
    """The basic (one-octet) P-field of a Level 1 CUC code."""
    _check_octets(coarse_octets, fine_octets)
    return (_LEVEL1_ID << 4) | ((coarse_octets - 1) << 2) | fine_octets


def encode_cuc(utc: datetime, coarse_octets: int = 4, fine_octets: int = 2, p_field: bool = True) -> bytes:
    """Encode a UTC instant as a Level 1 CUC code (TAI seconds since 1958-01-01)."""
    _check_octets(coarse_octets, fine_octets)
    t = _as_utc(utc)
    elapsed = (t + timedelta(seconds=tai_minus_utc(t))) - CUC_EPOCH_TAI  # exact: integer microseconds
    coarse, rest = divmod(elapsed, _SECOND)
    if coarse >= 256 ** coarse_octets:
        raise CucFormatError(f"{coarse} s does not fit in {coarse_octets} coarse octet(s)")
    fine = (rest.microseconds << (8 * fine_octets)) // 1_000_000  # truncated binary fraction
    head = bytes([cuc_p_field(coarse_octets, fine_octets)]) if p_field else b""
    return head + coarse.to_bytes(coarse_octets, "big") + fine.to_bytes(fine_octets, "big")


def decode_cuc(code: bytes, coarse_octets: int | None = None, fine_octets: int | None = None) -> Fraction:
    """TAI seconds since 1958-01-01 carried by a CUC code, as an exact fraction.

    With a P-field, pass the code alone. Without one (octet counts agreed in advance, the "implicit"
    P-field of the standard), pass ``coarse_octets`` and ``fine_octets``.
    """
    if coarse_octets is None and fine_octets is None:
        if not code:
            raise CucFormatError("empty code")
        p = code[0]
        if p >> 7:
            raise CucFormatError("extended P-field (second octet) is not supported")
        if (p >> 4) & 0b111 != _LEVEL1_ID:
            raise CucFormatError(f"time code identification {(p >> 4) & 0b111:03b} is not Level 1 (001)")
        coarse_octets, fine_octets, t_field = ((p >> 2) & 0b11) + 1, p & 0b11, code[1:]
    elif coarse_octets is None or fine_octets is None:
        raise CucFormatError("pass both octet counts, or neither")
    else:
        _check_octets(coarse_octets, fine_octets)
        t_field = code
    if len(t_field) != coarse_octets + fine_octets:
        raise CucFormatError(f"expected {coarse_octets + fine_octets} T-field octets, got {len(t_field)}")
    coarse = int.from_bytes(t_field[:coarse_octets], "big")
    fine = int.from_bytes(t_field[coarse_octets:], "big")
    return coarse + Fraction(fine, 256 ** fine_octets)


def cuc_to_utc(code: bytes, coarse_octets: int | None = None, fine_octets: int | None = None) -> datetime:
    """The UTC instant of a CUC code, to the nearest microsecond.

    Raises ``ValueError`` if the instant falls inside an inserted leap second (UTC 23:59:60), which
    ``datetime`` cannot represent.
    """
    seconds = decode_cuc(code, coarse_octets, fine_octets)
    tai_label = CUC_EPOCH_TAI + timedelta(microseconds=round(seconds * 1_000_000))
    for offset in sorted({entry[2] for entry in LEAP_SECONDS}):
        candidate = tai_label - timedelta(seconds=offset)
        try:
            if tai_minus_utc(candidate) == offset:
                return candidate
        except ValueError:
            continue
    raise ValueError(f"TAI {tai_label:%Y-%m-%dT%H:%M:%S.%f} is inside a leap second (UTC 23:59:60) "
                     "or outside the leap-second table")


def _check_octets(coarse_octets: int, fine_octets: int) -> None:
    if not 1 <= coarse_octets <= 4 or not 0 <= fine_octets <= 3:
        raise CucFormatError("the basic P-field allows 1-4 coarse and 0-3 fine octets")
