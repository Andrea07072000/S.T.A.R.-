"""star_sexagesimal - degrees <-> degrees/minutes/seconds and hours/minutes/seconds (S.T.A.R., 2026-10-06).
Standard library only.

  deg_to_dms(deg, decimals=3) -> (sign, degrees, arcminutes, arcseconds, fraction)   e.g. ('-', 23, 26, 21, 448)
  deg_to_hms(deg, decimals=4) -> (sign, hours, minutes, seconds, fraction)           the same angle as time, 15 deg = 1 h
  dms_to_deg(sign, degrees, arcminutes, arcseconds) -> degrees
  hms_to_deg(sign, hours, minutes, seconds)         -> degrees
The fields are integers: `fraction` counts units of 10**-decimals of a second. Rounding is to the nearest unit, ties
away from zero, done ONCE on the whole angle, so a value never shows 60 in a field: 59.9996 arcsec at three decimals
becomes the next arcminute. The sign is a separate '+' or '-' so that -0 deg 30' is not lost; an angle that rounds
to zero has sign '+'. No wrapping: 360 deg is ('+', 360, 0, 0, 0) and 24 h.
Refusals (ValueError): non-numeric, boolean or non-finite input, an angle outside [-360, 360] deg, decimals not an
integer in 0 ... 6, a sign other than '+' or '-', degrees not an integer in 0 ... 360 (hours 0 ... 24), minutes not
an integer in 0 ... 59, seconds outside [0, 60), a total above 360 deg (24 h).
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["deg_to_dms", "deg_to_hms", "dms_to_deg", "hms_to_deg"]
__version__ = "0.1.0"

Fields = Tuple[str, int, int, int, int]


def _real(v, lo: float, hi: float, what: str, closed_hi: bool = True) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) and (float(v) <= hi if closed_hi else float(v) < hi)
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}{']' if closed_hi else ')'}")
    return float(v)


def _int(v, lo: int, hi: int, what: str) -> int:
    if isinstance(v, bool) or not isinstance(v, numbers.Integral) or not lo <= int(v) <= hi:
        raise ValueError(f"{what} must be an integer within [{lo}, {hi}]")
    return int(v)


def _split(deg, decimals, seconds_per_degree: int) -> Fields:
    value = _real(deg, -360.0, 360.0, "angle (deg)")
    scale = 10 ** _int(decimals, 0, 6, "decimals")
    total = math.floor(abs(value) * seconds_per_degree * scale + 0.5)          # units of 10**-decimals second, ties away from zero
    seconds, fraction = divmod(total, scale)
    minutes, s = divmod(seconds, 60)
    whole, m = divmod(minutes, 60)
    return ("-" if value < 0.0 and total else "+"), whole, m, s, fraction


def deg_to_dms(deg: float, decimals: int = 3) -> Fields:
    return _split(deg, decimals, 3600)


def deg_to_hms(deg: float, decimals: int = 4) -> Fields:
    return _split(deg, decimals, 240)


def _join(sign, whole, minutes, seconds, top: int, unit: str, seconds_per_degree: float) -> float:
    if not isinstance(sign, str) or sign not in ("+", "-"):
        raise ValueError("sign must be '+' or '-'")
    total = (_int(whole, 0, top, unit) * 60 + _int(minutes, 0, 59, "minutes")) * 60 + _real(seconds, 0.0, 60.0, "seconds", closed_hi=False)
    if total > top * 3600:
        raise ValueError(f"the angle exceeds {top} {unit}")
    return (-total if sign == "-" else total) / seconds_per_degree


def dms_to_deg(sign: str, degrees: int, arcminutes: int, arcseconds: float) -> float:
    return _join(sign, degrees, arcminutes, arcseconds, 360, "degrees", 3600.0)


def hms_to_deg(sign: str, hours: int, minutes: int, seconds: float) -> float:
    return _join(sign, hours, minutes, seconds, 24, "hours", 240.0)
