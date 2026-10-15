"""star_calendar - calendar dates and Julian day numbers, exact integer arithmetic (S.T.A.R., 2026-10-06).
Standard library only.

  jdn(year, month, day, calendar="auto") -> int: Julian Day Number of the date (the day that starts at noon UT)
  calendar_date(jdn, calendar="auto") -> (year, month, day)
  julian_date(year, month, day, hour=0, minute=0, second=0.0, calendar="auto") -> (jd_midnight, fraction): the Julian
      Date as a pair whose sum is the JD; jd_midnight ends in .5 and fraction is in [0, 1) - two floats keep the time
      of day to full precision, one float would keep only about 40 microseconds
  weekday(jdn) -> 0 = Monday ... 6 = Sunday;  day_of_year(year, month, day, calendar="auto") -> 1..366
Calendars: "gregorian" (proleptic), "julian" (proleptic), "auto" = Julian up to 1582-10-04, Gregorian from 1582-10-15
(the ten days in between never existed and are refused). Years are astronomical: year 0 is 1 BC, -4712 is 4713 BC.
Valid for JDN 0 (-4712-01-01 Julian) to year 9999. Not a time scale: no leap seconds, no UTC/TT conversion.
Refusals (ValueError): non-integer year, month, day or JDN (booleans included), a date that does not exist in the
calendar, an unknown calendar, a time of day outside 00:00:00 - 24:00:00 (exclusive), anything outside the valid range.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["jdn", "calendar_date", "julian_date", "weekday", "day_of_year", "CALENDARS"]
__version__ = "0.1.0"
CALENDARS = ("auto", "gregorian", "julian")
GREGORIAN_START_JDN = 2299161            # 1582-10-15 Gregorian
MAX_JDN = 5373484                        # 9999-12-31 Gregorian
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _int(v, what: str) -> int:
    if isinstance(v, bool) or not isinstance(v, numbers.Integral):
        raise ValueError(f"{what} must be an integer")
    return int(v)


def _cal(calendar) -> str:
    if not isinstance(calendar, str) or calendar not in CALENDARS:
        raise ValueError(f"calendar must be one of {', '.join(CALENDARS)}")
    return calendar


def _leap(year: int, gregorian: bool) -> bool:
    return year % 4 == 0 and (not gregorian or year % 100 != 0 or year % 400 == 0)


def _raw_jdn(year: int, month: int, day: int, gregorian: bool) -> int:
    a = (14 - month) // 12
    y, m = year + 4800 - a, month + 12 * a - 3
    base = day + (153 * m + 2) // 5 + 365 * y + y // 4
    return base - y // 100 + y // 400 - 32045 if gregorian else base - 32083


def jdn(year: int, month: int, day: int, calendar: str = "auto") -> int:
    year, month, day, calendar = _int(year, "year"), _int(month, "month"), _int(day, "day"), _cal(calendar)
    if not -4712 <= year <= 9999:
        raise ValueError("year must be within [-4712, 9999]")
    if not 1 <= month <= 12:
        raise ValueError("month must be within [1, 12]")
    gregorian = calendar == "gregorian" or (calendar == "auto" and (year, month, day) >= (1582, 10, 15))
    if calendar == "auto" and (1582, 10, 4) < (year, month, day) < (1582, 10, 15):
        raise ValueError("1582-10-05 to 1582-10-14 do not exist in the civil calendar")
    last = 29 if month == 2 and _leap(year, gregorian) else _DAYS[month - 1]
    if not 1 <= day <= last:
        raise ValueError(f"day must be within [1, {last}] for {year}-{month:02d} in the {'Gregorian' if gregorian else 'Julian'} calendar")
    n = _raw_jdn(year, month, day, gregorian)
    if not 0 <= n <= MAX_JDN:
        raise ValueError("date outside the valid range (JDN 0 to 9999-12-31)")
    return n


def calendar_date(jdn_value: int, calendar: str = "auto") -> Tuple[int, int, int]:
    j, calendar = _int(jdn_value, "jdn"), _cal(calendar)
    if not 0 <= j <= MAX_JDN:
        raise ValueError("jdn outside the valid range (0 to 9999-12-31)")
    gregorian = calendar == "gregorian" or (calendar == "auto" and j >= GREGORIAN_START_JDN)
    f = j + 1401
    if gregorian:
        f += (((4 * j + 274277) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    h = 5 * ((e % 1461) // 4) + 2
    day = (h % 153) // 5 + 1
    month = (h // 153 + 2) % 12 + 1
    return e // 1461 - 4716 + (14 - month) // 12, month, day


def julian_date(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: float = 0.0,
                calendar: str = "auto") -> Tuple[float, float]:
    n = jdn(year, month, day, calendar)
    hour, minute = _int(hour, "hour"), _int(minute, "minute")
    if isinstance(second, bool) or not isinstance(second, numbers.Real) or not math.isfinite(second):
        raise ValueError("second must be a finite real number")
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0.0 <= second < 60.0):
        raise ValueError("time of day must be within 00:00:00 and 23:59:59.999...")
    fraction = (hour * 3600 + minute * 60 + float(second)) / 86400.0
    return n - 0.5, min(fraction, math.nextafter(1.0, 0.0))


def weekday(jdn_value: int) -> int:
    j = _int(jdn_value, "jdn")
    if not 0 <= j <= MAX_JDN:
        raise ValueError("jdn outside the valid range (0 to 9999-12-31)")
    return j % 7                                           # JDN 0 was a Monday


def day_of_year(year: int, month: int, day: int, calendar: str = "auto") -> int:
    n = jdn(year, month, day, calendar)
    if calendar == "auto" and year == 1582 and n >= GREGORIAN_START_JDN:
        return n - jdn(1582, 1, 1, "julian") + 1          # days actually elapsed: 1582 had 355 days in the civil calendar
    gregorian = calendar == "gregorian" or (calendar == "auto" and n >= GREGORIAN_START_JDN)
    return n - jdn(year, 1, 1, "gregorian" if gregorian else "julian") + 1
