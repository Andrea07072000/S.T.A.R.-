# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""TAI - UTC from the IERS leap-second table, TT - UTC, and Julian dates.

Design rule: outside its validity domain this module raises an error; it never returns a
plausible-looking number. Three domains are enforced:

* before 1972-01-01 UTC with integer leap seconds does not exist -> LeapSecondTableError
* after the table's published expiry date a new leap second may have been announced
  -> LeapSecondTableError (update the table from IERS Bulletin C)
* a datetime without a timezone is ambiguous -> NaiveDatetimeError

Primary source: IERS Earth Orientation Centre, Bulletin C, file ``Leap_Second.dat``
(https://hpiers.obspm.fr/iers/bul/bulc/Leap_Second.dat), "Updated through IERS Bulletin 72
issued in July 2026", "File expires on 28 June 2027". Values checked against that file on
2026-09-28 (see tests/test_leap_seconds.py for the MJD cross-check of every entry).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

#: TT - TAI in seconds, fixed by definition (IAU 1991 Resolution A4).
TT_MINUS_TAI_S: float = 32.184

#: MJD = JD - 2400000.5
_MJD_OFFSET: float = 2400000.5

LEAP_SECONDS_SOURCE = (
    "IERS Bulletin C, Leap_Second.dat (updated through Bulletin 72, July 2026; expires 2027-06-28)"
)

#: (UTC instant the value takes effect, MJD of that instant as published by IERS, TAI - UTC in seconds)
LEAP_SECONDS: tuple[tuple[datetime, float, int], ...] = tuple(
    (datetime(year, month, 1, tzinfo=timezone.utc), mjd, value)
    for mjd, year, month, value in (
        (41317.0, 1972, 1, 10), (41499.0, 1972, 7, 11), (41683.0, 1973, 1, 12),
        (42048.0, 1974, 1, 13), (42413.0, 1975, 1, 14), (42778.0, 1976, 1, 15),
        (43144.0, 1977, 1, 16), (43509.0, 1978, 1, 17), (43874.0, 1979, 1, 18),
        (44239.0, 1980, 1, 19), (44786.0, 1981, 7, 20), (45151.0, 1982, 7, 21),
        (45516.0, 1983, 7, 22), (46247.0, 1985, 7, 23), (47161.0, 1988, 1, 24),
        (47892.0, 1990, 1, 25), (48257.0, 1991, 1, 26), (48804.0, 1992, 7, 27),
        (49169.0, 1993, 7, 28), (49534.0, 1994, 7, 29), (50083.0, 1996, 1, 30),
        (50630.0, 1997, 7, 31), (51179.0, 1999, 1, 32), (53736.0, 2006, 1, 33),
        (54832.0, 2009, 1, 34), (56109.0, 2012, 7, 35), (57204.0, 2015, 7, 36),
        (57754.0, 2017, 1, 37),
    )
)

#: The table is not trusted after this instant (the expiry date published by IERS).
LEAP_SECONDS_VALID_UNTIL: datetime = datetime(2027, 6, 28, tzinfo=timezone.utc)


class LeapSecondTableError(ValueError):
    """The requested epoch is outside the validity domain of the leap-second table."""


class NaiveDatetimeError(ValueError):
    """A datetime without timezone was given: the instant is ambiguous."""


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise NaiveDatetimeError(
            f"{dt.isoformat()} has no timezone; pass an aware datetime (e.g. tzinfo=timezone.utc)")
    return dt.astimezone(timezone.utc)


def tai_minus_utc(utc: datetime) -> int:
    """TAI - UTC in seconds valid at the given instant."""
    t = _as_utc(utc)
    if t < LEAP_SECONDS[0][0]:
        raise LeapSecondTableError("UTC with integer leap seconds is not defined before 1972-01-01")
    if t > LEAP_SECONDS_VALID_UNTIL:
        raise LeapSecondTableError(
            f"leap-second table valid until {LEAP_SECONDS_VALID_UNTIL:%Y-%m-%d}; "
            "update it from IERS Bulletin C before using later epochs")
    value = LEAP_SECONDS[0][2]
    for effective, _mjd, offset in LEAP_SECONDS:
        if t < effective:
            break
        value = offset
    return value


def tt_minus_utc(utc: datetime) -> float:
    """TT - UTC in seconds valid at the given instant (TAI - UTC + 32.184 s)."""
    return tai_minus_utc(utc) + TT_MINUS_TAI_S


def julian_date(utc: datetime) -> float:
    """Julian Date of a UTC instant (proleptic Gregorian calendar, Meeus algorithm).

    The day fraction is civil time over an 86400 s day. Consequences, stated rather than hidden:

    * a leap second (23:59:60) is not representable by ``datetime`` and is out of scope;
    * on a UTC day that ends with a leap second, SOFA/ERFA ("quasi-JD" UTC) spread the day
      over 86401 s, so their value and this one differ by up to 1 s (about 1.16e-5 day).
      On every other day the two agree (see tests/test_leap_seconds.py).
    """
    t = _as_utc(utc)
    year, month = t.year, t.month
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    day_fraction = (t.hour + (t.minute + (t.second + t.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    return (math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1))
            + t.day + b - 1524.5 + day_fraction)


def modified_julian_date(utc: datetime) -> float:
    """Modified Julian Date of a UTC instant."""
    return jd_to_mjd(julian_date(utc))


def jd_to_mjd(jd: float) -> float:
    return jd - _MJD_OFFSET


def mjd_to_jd(mjd: float) -> float:
    return mjd + _MJD_OFFSET
