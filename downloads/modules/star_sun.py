"""star_sun - low-precision Sun vector, orbit beta angle and cylindrical eclipse test (S.T.A.R., 2026-10-06).
Standard library only.

  sun_vector_au(jd_day, jd_frac=0.0) -> (x, y, z): geocentric Sun position in astronomical units, referred to the
      mean equator and equinox of date (MOD). Series of the Astronomical Almanac as given by Vallado, Algorithm 29.
      Stated accuracy of the series: 0.01 deg between 1950 and 2050; outside those years the function refuses.
      Measured (crosscheck_sun.py, 402 dates): the direction is the APPARENT one (aberration included), within
      0.0097 deg of JPL DE440 apparent and of astropy; against geometric positions the difference reaches 0.014 deg.
      Distance within 7e-5 AU.
  sun_ra_dec_deg(jd_day, jd_frac=0.0) -> (right ascension in [0, 360), declination), same frame.
  beta_angle_deg(sun, inc_deg, raan_deg) -> angle between the Sun direction and the orbit plane, in [-90, 90];
      positive when the Sun is on the side of the orbit angular momentum. Sun and RAAN in the same equatorial frame.
  in_shadow(r_sat, sun, body_radius=6378.137) -> True when the satellite is inside the cylindrical shadow of the body
      (no penumbra, parallel rays). r_sat and body_radius in the same unit; only the direction of `sun` is used.
The Julian date is UT1 (UTC is equivalent at this accuracy), given as day + fraction to keep precision.
Refusals (ValueError): non-numeric, boolean or non-finite input, a date outside 1950-2050, a zero Sun vector, a
satellite inside the body, an inclination outside [0, 180], a right ascension of the node outside [-360, 360].
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["sun_vector_au", "sun_ra_dec_deg", "beta_angle_deg", "in_shadow"]
__version__ = "0.1.0"
JD_1950, JD_2050 = 2433282.5, 2469807.5
J2000 = 2451545.0
EARTH_RADIUS_KM = 6378.137
Vec = Tuple[float, float, float]


def _num(*values) -> None:
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e300 < float(v) < 1e300    # NaN fails both
        except OverflowError:                                                    # an integer too large for a float
            ok = False
        if not ok:
            raise ValueError("inputs must be finite real numbers (magnitude below 1e300)")


def _vec(v, what: str) -> Vec:
    try:                                                   # lists, tuples and arrays; not text, sets or mappings
        ok = not isinstance(v, (str, bytes, dict, set, frozenset)) and len(v) == 3
        items = (v[0], v[1], v[2]) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a sequence of three numbers")
    _num(*items)
    return float(items[0]), float(items[1]), float(items[2])


def _unit(v: Vec, what: str) -> Vec:
    scale = max(abs(c) for c in v)
    if scale == 0.0:
        raise ValueError(f"{what} is the zero vector: no direction")
    x, y, z = (c / scale for c in v)                       # scaled first: no overflow or underflow in the norm
    n = math.hypot(x, y, z)
    return x / n, y / n, z / n


def _centuries(jd_day: float, jd_frac: float) -> float:
    _num(jd_day, jd_frac)
    jd = jd_day + jd_frac
    if not JD_1950 <= jd <= JD_2050:
        raise ValueError("date outside 1950-2050: the series is not stated to hold there")
    return ((jd_day - J2000) + jd_frac) / 36525.0


def sun_vector_au(jd_day: float, jd_frac: float = 0.0) -> Vec:
    t = _centuries(jd_day, jd_frac)
    mean_longitude = 280.460 + 36000.771 * t
    m = math.radians((357.5291092 + 35999.05034 * t) % 360.0)
    ecliptic_longitude = math.radians((mean_longitude + 1.914666471 * math.sin(m) + 0.019994643 * math.sin(2 * m)) % 360.0)
    r = 1.000140612 - 0.016708617 * math.cos(m) - 0.000139589 * math.cos(2 * m)
    obliquity = math.radians(23.439291 - 0.0130042 * t)
    return (r * math.cos(ecliptic_longitude), r * math.cos(obliquity) * math.sin(ecliptic_longitude),
            r * math.sin(obliquity) * math.sin(ecliptic_longitude))


def sun_ra_dec_deg(jd_day: float, jd_frac: float = 0.0) -> Tuple[float, float]:
    x, y, z = sun_vector_au(jd_day, jd_frac)
    ra = math.degrees(math.atan2(y, x)) % 360.0
    return (0.0 if ra >= 360.0 else ra), math.degrees(math.atan2(z, math.hypot(x, y)))


def beta_angle_deg(sun: Sequence[float], inc_deg: float, raan_deg: float) -> float:
    s = _unit(_vec(sun, "sun"), "sun")
    _num(inc_deg, raan_deg)
    if not 0.0 <= inc_deg <= 180.0:
        raise ValueError("inclination must be within [0, 180] deg")
    if not -360.0 <= raan_deg <= 360.0:
        raise ValueError("right ascension of the node must be within [-360, 360] deg")
    i, o = math.radians(inc_deg), math.radians(raan_deg)
    h = (math.sin(i) * math.sin(o), -math.sin(i) * math.cos(o), math.cos(i))        # unit angular momentum
    return math.degrees(math.asin(max(-1.0, min(1.0, s[0] * h[0] + s[1] * h[1] + s[2] * h[2]))))


def in_shadow(r_sat: Sequence[float], sun: Sequence[float], body_radius: float = EARTH_RADIUS_KM) -> bool:
    r = _vec(r_sat, "r_sat")
    s = _unit(_vec(sun, "sun"), "sun")
    _num(body_radius)
    if body_radius <= 0.0:
        raise ValueError("body radius must be positive")
    if math.hypot(*r) < body_radius:                       # hypot scales internally: 1e-200 squared would underflow to 0
        raise ValueError("the satellite is inside the body")
    along = r[0] * s[0] + r[1] * s[1] + r[2] * s[2]                                  # component towards the Sun
    if along >= 0.0:
        return False                                                                 # day side
    px, py, pz = r[0] - along * s[0], r[1] - along * s[1], r[2] - along * s[2]
    return math.hypot(px, py, pz) < body_radius
