"""star_era - Earth Rotation Angle (IAU 2000) and Greenwich Mean Sidereal Time (IAU 2006)
(S.T.A.R., 2026-10-06). Standard library only.

  era_deg(ut1_day, ut1_frac=0.0) -> Earth Rotation Angle in degrees, [0, 360): the angle between the Celestial and the
      Terrestrial Intermediate Origins, linear in UT1 (IERS Conventions 2010, eq. 5.15).
  gmst06_deg(ut1_day, ut1_frac, tt_day, tt_frac) -> Greenwich Mean Sidereal Time in degrees, [0, 360), consistent with
      the IAU 2006 precession: ERA(UT1) plus a polynomial in TT (IERS Conventions 2010, eq. 5.32).
Dates are Julian Dates given as two numbers whose sum is the date (any split): the fraction of the day is handled
apart, so a split like (2460000.5, 0.123456789) keeps nanosecond-level precision in the angle.
Valid for 1800-01-01 to 2200-01-01 (the span over which the polynomial is used in practice); outside, ValueError.
Refusals (ValueError): non-numeric, boolean or non-finite input, a date outside the valid range.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["era_deg", "gmst06_deg"]
__version__ = "0.1.1"
J2000 = 2451545.0
JD_MIN, JD_MAX = 2378496.5, 2524593.5              # 1800-01-01 and 2200-01-01
ERA0 = 0.7790572732640                             # turns at J2000.0 UT1
ERA_RATE = 0.00273781191135448                     # turns per UT1 day beyond one full turn
# IAU 2006 GMST - ERA, arcseconds, polynomial in Julian centuries of TT since J2000.0
GMST_POLY = (0.014506, 4612.156534, 1.3915817, -0.00000044, -0.000029956, -0.0000000368)


def _pair(day, frac, what: str) -> Tuple[float, float]:
    for v in (day, frac):
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e300 < float(v) < 1e300      # NaN fails both
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"{what} must be given as finite real numbers")
    day, frac = float(day), float(frac)
    if not JD_MIN <= day + frac <= JD_MAX:
        raise ValueError(f"{what} outside 1800-2200")
    return day, frac


def _era_turns(day: float, frac: float) -> float:
    # days since J2000 kept as two parts: the whole turns of the large part are dropped exactly before adding
    d1, d2 = (day, frac) if abs(day) >= abs(frac) else (frac, day)
    t = d2 + (d1 - J2000)
    f = math.fmod(d1, 1.0) + math.fmod(d2, 1.0)
    return (f + ERA0 + ERA_RATE * t) % 1.0


def _wrap360(angle: float) -> float:
    """Reduction to [0, 360). Python's % returns 360.0 itself for a tiny negative number (-1e-20 % 360.0 == 360.0): that
    value is the same direction as 0 and is returned as 0.0, so the result is never 360."""
    reduced = angle % 360.0
    return 0.0 if reduced >= 360.0 else reduced


def era_deg(ut1_day: float, ut1_frac: float = 0.0) -> float:
    day, frac = _pair(ut1_day, ut1_frac, "UT1 date")
    return _wrap360(360.0 * _era_turns(day, frac))


def gmst06_deg(ut1_day: float, ut1_frac: float, tt_day: float, tt_frac: float) -> float:
    day, frac = _pair(ut1_day, ut1_frac, "UT1 date")
    td, tf = _pair(tt_day, tt_frac, "TT date")
    t = ((td - J2000) + tf) / 36525.0
    poly = 0.0
    for c in reversed(GMST_POLY):
        poly = poly * t + c
    return _wrap360(360.0 * _era_turns(day, frac) + poly / 3600.0)
