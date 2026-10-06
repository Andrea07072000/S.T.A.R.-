"""star_moon - low-precision geocentric Moon position (S.T.A.R., 2026-10-06). Standard library only.

  moon_vector_km(jd_day, jd_frac=0.0) -> (x, y, z): geocentric Moon position in km, mean equator and equinox of date.
  moon_ra_dec_deg(jd_day, jd_frac=0.0) -> (right ascension in [0, 360), declination), same frame.
  moon_distance_km(jd_day, jd_frac=0.0) -> geocentric distance.
Series of the Astronomical Almanac as given by Vallado, Algorithm 31 (six terms in longitude, four in latitude, four
in parallax). Stated accuracy of the series: 0.3 deg in longitude, 0.2 deg in latitude, 0.003 deg in parallax
(about 1200 km in distance). The measured envelope against JPL DE440 is in crosscheck_moon.py and in the README.
The Julian date is TDB (TT or UTC change the result far below this accuracy), given as day + fraction.
Valid for 1950-2050; outside, ValueError (the series is not stated to hold there).
Refusals (ValueError): non-numeric, boolean or non-finite input, a date outside 1950-2050.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["moon_vector_km", "moon_ra_dec_deg", "moon_distance_km"]
__version__ = "0.1.0"
JD_1950, JD_2050 = 2433282.5, 2469807.5
J2000 = 2451545.0
EARTH_RADIUS_KM = 6378.137
# (amplitude deg, phase deg, rate deg per Julian century)
LONGITUDE = ((6.29, 134.9, 477198.85), (-1.27, 259.2, -413335.38), (0.66, 235.7, 890534.23), (0.21, 269.9, 954397.70),
             (-0.19, 357.5, 35999.05), (-0.11, 186.6, 966404.05))
LATITUDE = ((5.13, 93.3, 483202.03), (0.28, 228.2, 960400.87), (-0.28, 318.3, 6003.18), (-0.17, 217.6, -407332.20))
PARALLAX = ((0.0518, 134.9, 477198.85), (0.0095, 259.2, -413335.38), (0.0078, 235.7, 890534.23), (0.0028, 269.9, 954397.70))
Vec = Tuple[float, float, float]


def _centuries(jd_day, jd_frac) -> float:
    for v in (jd_day, jd_frac):
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e300 < float(v) < 1e300      # NaN fails both
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError("the date must be given as finite real numbers")
    if not JD_1950 <= float(jd_day) + float(jd_frac) <= JD_2050:
        raise ValueError("date outside 1950-2050: the series is not stated to hold there")
    return ((float(jd_day) - J2000) + float(jd_frac)) / 36525.0


def _series(terms, t: float, f) -> float:
    return sum(a * f(math.radians((phase + rate * t) % 360.0)) for a, phase, rate in terms)


def _spherical(jd_day, jd_frac) -> Tuple[float, float, float, float]:
    """Ecliptic longitude and latitude (rad), distance (km), obliquity (rad)."""
    t = _centuries(jd_day, jd_frac)
    lon = math.radians((218.32 + 481267.8813 * t + _series(LONGITUDE, t, math.sin)) % 360.0)
    lat = math.radians(_series(LATITUDE, t, math.sin))
    parallax = math.radians(0.9508 + _series(PARALLAX, t, math.cos))
    return lon, lat, EARTH_RADIUS_KM / math.sin(parallax), math.radians(23.439291 - 0.0130042 * t)


def moon_vector_km(jd_day: float, jd_frac: float = 0.0) -> Vec:
    lon, lat, r, eps = _spherical(jd_day, jd_frac)
    cb, sb, cl, sl, ce, se = math.cos(lat), math.sin(lat), math.cos(lon), math.sin(lon), math.cos(eps), math.sin(eps)
    return r * cb * cl, r * (ce * cb * sl - se * sb), r * (se * cb * sl + ce * sb)


def moon_distance_km(jd_day: float, jd_frac: float = 0.0) -> float:
    return _spherical(jd_day, jd_frac)[2]


def moon_ra_dec_deg(jd_day: float, jd_frac: float = 0.0) -> Tuple[float, float]:
    x, y, z = moon_vector_km(jd_day, jd_frac)
    ra = math.degrees(math.atan2(y, x)) % 360.0
    return (0.0 if ra >= 360.0 else ra), math.degrees(math.atan2(z, math.hypot(x, y)))
