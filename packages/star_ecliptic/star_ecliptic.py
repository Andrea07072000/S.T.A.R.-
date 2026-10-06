"""star_ecliptic - mean obliquity of the ecliptic and equatorial <-> ecliptic directions (S.T.A.R., 2026-10-06).
Standard library only.

  mean_obliquity_arcsec(jd_day, jd_frac=0.0, model="iau2006")   arcseconds; model "iau2006" or "iau1980"
  equatorial_to_ecliptic(ra_deg, dec_deg, obliquity_arcsec) -> (longitude in [0, 360), latitude) in degrees
  ecliptic_to_equatorial(lon_deg, lat_deg, obliquity_arcsec) -> (right ascension in [0, 360), declination) in degrees
The date is a TT Julian Date split in two parts (day + fraction) so that no digit is lost; T is counted in Julian
centuries of 36525 days from JD 2451545.0.
  IAU 1980 (Lieske 1979):  84381.448 - 46.8150 T - 0.00059 T^2 + 0.001813 T^3
  IAU 2006 (Capitaine 2003): 84381.406 - 46.836769 T - 0.0001831 T^2 + 0.00200340 T^3 - 0.000000576 T^4 - 0.0000000434 T^5
The two conversions are one rotation about the x axis (the equinox) by the obliquity that the caller passes: the
mean obliquity of date, the J2000 value, or a true obliquity that already includes nutation.
Refusals (ValueError): non-numeric, boolean or non-finite input, a date outside JD 2086302.5 ... 2816787.5 (years
1000 to 3000), a fraction outside [-1, 1], an unknown model, declination or latitude outside [-90, 90], right
ascension or longitude outside [-360, 360], obliquity outside [0, 324000] arcsec.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["mean_obliquity_arcsec", "equatorial_to_ecliptic", "ecliptic_to_equatorial"]
__version__ = "0.1.0"

JD_MIN, JD_MAX = 2086302.5, 2816787.5
# coefficients of T^0 ... T^n, arcseconds
MODELS = {"iau1980": (84381.448, -46.8150, -0.00059, 0.001813),
          "iau2006": (84381.406, -46.836769, -0.0001831, 0.00200340, -0.000000576, -0.0000000434)}


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _wrap360(deg: float) -> float:
    d = deg % 360.0
    return 0.0 if d >= 360.0 else d


def mean_obliquity_arcsec(jd_day: float, jd_frac: float = 0.0, model: str = "iau2006") -> float:
    day, frac = _real(jd_day, JD_MIN, JD_MAX, "jd_day"), _real(jd_frac, -1.0, 1.0, "jd_frac")
    if not isinstance(model, str) or model not in MODELS:
        raise ValueError("model must be 'iau2006' or 'iau1980'")
    t = ((day - 2451545.0) + frac) / 36525.0
    eps = 0.0
    for c in reversed(MODELS[model]):
        eps = eps * t + c
    return eps


def _rotate(lon_deg, lat_deg, obliquity_arcsec, sign: float, names) -> Tuple[float, float]:
    a = math.radians(_real(lon_deg, -360.0, 360.0, names[0] + " (deg)"))
    d = math.radians(_real(lat_deg, -90.0, 90.0, names[1] + " (deg)"))
    e = sign * math.radians(_real(obliquity_arcsec, 0.0, 324000.0, "obliquity (arcsec)") / 3600.0)
    x, y, z = math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)
    y2 = y * math.cos(e) + z * math.sin(e)
    z2 = z * math.cos(e) - y * math.sin(e)
    return _wrap360(math.degrees(math.atan2(y2, x))), math.degrees(math.atan2(z2, math.hypot(x, y2)))


def equatorial_to_ecliptic(ra_deg: float, dec_deg: float, obliquity_arcsec: float) -> Tuple[float, float]:
    return _rotate(ra_deg, dec_deg, obliquity_arcsec, 1.0, ("right ascension", "declination"))


def ecliptic_to_equatorial(lon_deg: float, lat_deg: float, obliquity_arcsec: float) -> Tuple[float, float]:
    return _rotate(lon_deg, lat_deg, obliquity_arcsec, -1.0, ("longitude", "latitude"))
