"""star_epoch - Julian and Besselian epochs <-> Julian Date (S.T.A.R., 2026-10-06). Standard library only.

  julian_epoch(jd_day, jd_frac=0.0)        e.g. 2000.0 for JD 2451545.0 (J2000.0); one Julian year = 365.25 days
  besselian_epoch(jd_day, jd_frac=0.0)     e.g. 1950.0 for JD 2433282.42345905 (B1950.0)
  jd_from_julian_epoch(epoch)    -> (jd_day, jd_frac)
  jd_from_besselian_epoch(epoch) -> (jd_day, jd_frac)
The Besselian epoch follows Lieske (1979), as adopted by the IAU: B1900.0 = JD 2415020.31352 and a tropical year of
365.242198781 days. Dates are Julian Dates in two parts (their sum is the date) so that no digit is lost; the
results of the inverse functions have jd_day ending in .5 and jd_frac in [0, 1). The time scale is the caller's
(TT for catalogue epochs).
Refusals (ValueError): non-numeric, boolean or non-finite input, a date outside JD 2086302.5 ... 2816787.5 or an
epoch outside [1000, 3000], a fraction outside [-1, 1].
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["julian_epoch", "besselian_epoch", "jd_from_julian_epoch", "jd_from_besselian_epoch"]
__version__ = "0.1.0"

JD_MIN, JD_MAX = 2086302.5, 2816787.5
EPOCH_MIN, EPOCH_MAX = 1000.0, 3000.0
J2000 = 2451545.0
JULIAN_YEAR = 365.25
TROPICAL_YEAR = 365.242198781           # days, Lieske 1979
B1900_MJD = 15019.81352                 # B1900.0 = JD 2415020.31352
MJD0 = 2400000.5


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _date(jd_day, jd_frac) -> Tuple[float, float]:
    return _real(jd_day, JD_MIN, JD_MAX, "jd_day"), _real(jd_frac, -1.0, 1.0, "jd_frac")


def _split(mjd: float) -> Tuple[float, float]:
    whole = math.floor(mjd)
    return MJD0 + whole, mjd - whole


def julian_epoch(jd_day: float, jd_frac: float = 0.0) -> float:
    day, frac = _date(jd_day, jd_frac)
    return 2000.0 + ((day - J2000) + frac) / JULIAN_YEAR


def besselian_epoch(jd_day: float, jd_frac: float = 0.0) -> float:
    day, frac = _date(jd_day, jd_frac)
    return 1900.0 + ((day - J2000) + (frac + (J2000 - MJD0 - B1900_MJD))) / TROPICAL_YEAR


def jd_from_julian_epoch(epoch: float) -> Tuple[float, float]:
    return _split(51544.5 + (_real(epoch, EPOCH_MIN, EPOCH_MAX, "epoch") - 2000.0) * JULIAN_YEAR)


def jd_from_besselian_epoch(epoch: float) -> Tuple[float, float]:
    return _split(B1900_MJD + (_real(epoch, EPOCH_MIN, EPOCH_MAX, "epoch") - 1900.0) * TROPICAL_YEAR)
