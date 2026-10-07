"""star_timecode - CCSDS ASCII time codes A and B, strict (S.T.A.R., 2026-10-07).
Standard library only.

  parse(text)                    code A "YYYY-MM-DDThh:mm:ss[.d...][Z]" or code B "YYYY-DDDThh:mm:ss[.d...][Z]"
                                 -> (year, month, day, hour, minute, second, fraction)
  format_a(year, month, day, hour, minute, second, fraction="")   -> "YYYY-MM-DDThh:mm:ss[.d...]Z"
  format_b(year, month, day, hour, minute, second, fraction="")   -> "YYYY-DDDThh:mm:ss[.d...]Z"
  day_of_year(year, month, day)  -> 1..366          month_day(year, day_of_year) -> (month, day)
The two codes are those of CCSDS 301.0-B-4 (Time Code Formats), section 3.5: calendar date or day of year, the letter
T, the time of day in UTC, an optional decimal fraction of the second and an optional terminator Z. The fraction is
kept as its string of digits ("" when absent, up to 12 digits): nothing is converted to a float, so a time code read
and written again is the same text. Second 60 is accepted only at 23:59, the place of a positive leap second.
Refusals (ValueError): anything that is not a str of that exact shape (wrong widths, separators, lower-case t or z,
spaces, signs, non-ASCII digits, a fraction with no digits or more than 12); a year outside 0001-9999; a month, day,
day of year, hour, minute or second out of range for that year (Gregorian leap years); second 60 outside 23:59;
for the formatters, arguments that are not integers (booleans refused) or a fraction that is not a string of digits.
"""
from __future__ import annotations

import numbers
import re
from typing import Tuple

__all__ = ["parse", "format_a", "format_b", "day_of_year", "month_day"]
__version__ = "0.1.0"

MAX_FRACTION_DIGITS = 12
_DIGITS = "0123456789"
_CODE = re.compile(r"([0-9]{4})-(?:([0-9]{2})-([0-9]{2})|([0-9]{3}))T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,12}))?Z?", re.ASCII)
_BEFORE = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)      # days before each month in a common year


def _leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in(year: int, month: int) -> int:
    if month == 2:
        return 29 if _leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def _int(v, what: str, lowest: int, highest: int) -> int:
    if isinstance(v, bool) or not isinstance(v, numbers.Integral) or not lowest <= v <= highest:
        raise ValueError(f"{what} must be an integer from {lowest} to {highest}")
    return int(v)


def _date(year, month, day) -> Tuple[int, int, int]:
    y = _int(year, "year", 1, 9999)
    m = _int(month, "month", 1, 12)
    return y, m, _int(day, "day", 1, _days_in(y, m))


def _time(hour, minute, second, fraction) -> Tuple[int, int, int, str]:
    h, mi = _int(hour, "hour", 0, 23), _int(minute, "minute", 0, 59)
    s = _int(second, "second", 0, 60 if (h, mi) == (23, 59) else 59)
    if not isinstance(fraction, str) or len(fraction) > MAX_FRACTION_DIGITS or any(c not in _DIGITS for c in fraction):
        raise ValueError("fraction must be a string of 0 to 12 ASCII digits")
    return h, mi, s, fraction


def day_of_year(year: int, month: int, day: int) -> int:
    y, m, d = _date(year, month, day)
    return _BEFORE[m - 1] + d + (1 if m > 2 and _leap(y) else 0)


def month_day(year: int, day_of_year: int) -> Tuple[int, int]:  # noqa: A002 - the parameter is named as in the standard
    y = _int(year, "year", 1, 9999)
    left = _int(day_of_year, "day of year", 1, 366 if _leap(y) else 365)
    month = 1
    while left > _days_in(y, month):
        left -= _days_in(y, month)
        month += 1
    return month, left


def parse(text: str) -> Tuple[int, int, int, int, int, int, str]:
    if not isinstance(text, str):
        raise ValueError("a time code must be a str")
    found = _CODE.fullmatch(text)
    if found is None:
        raise ValueError("not a CCSDS ASCII time code A (YYYY-MM-DDThh:mm:ss[.d]Z) or B (YYYY-DDDThh:mm:ss[.d]Z)")
    year, month, day, doy, hour, minute, second, fraction = found.groups()
    if doy is None:
        y, m, d = _date(int(year), int(month), int(day))
    else:
        y = int(year)
        m, d = month_day(y, int(doy))                       # month_day checks the year too
    return (y, m, d) + _time(int(hour), int(minute), int(second), fraction or "")


def _tail(hour, minute, second, fraction) -> str:
    h, mi, s, f = _time(hour, minute, second, fraction)
    return f"T{h:02d}:{mi:02d}:{s:02d}" + ("." + f if f else "") + "Z"


def format_a(year: int, month: int, day: int, hour: int, minute: int, second: int, fraction: str = "") -> str:
    y, m, d = _date(year, month, day)
    return f"{y:04d}-{m:02d}-{d:02d}" + _tail(hour, minute, second, fraction)


def format_b(year: int, month: int, day: int, hour: int, minute: int, second: int, fraction: str = "") -> str:
    y, m, d = _date(year, month, day)
    return f"{y:04d}-{day_of_year(y, m, d):03d}" + _tail(hour, minute, second, fraction)
