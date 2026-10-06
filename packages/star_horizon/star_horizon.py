"""star_horizon - hour angle and declination <-> azimuth and elevation (S.T.A.R., 2026-10-06). Standard library only.

  hadec_to_azel(ha_deg, dec_deg, lat_deg) -> (azimuth in [0, 360), elevation) in degrees
  azel_to_hadec(az_deg, el_deg, lat_deg)  -> (hour angle in (-180, 180], declination) in degrees
  parallactic_angle_deg(ha_deg, dec_deg, lat_deg) -> angle at the object between the pole and the zenith, (-180, 180]
Conventions: azimuth from North through East; hour angle positive West of the meridian (local sidereal time minus
right ascension); latitude is the observer's (astronomical or geodetic, as the caller's accuracy requires).
Geometry only: no refraction, no parallax, no aberration, no polar motion.
At the zenith or nadir the azimuth is undefined, at a celestial pole the hour angle is undefined, and at the zenith
the parallactic angle is undefined: the value returned there is 0.
Refusals (ValueError): non-numeric, boolean or non-finite input, hour angle or azimuth outside [-360, 360],
declination, elevation or latitude outside [-90, 90].
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["hadec_to_azel", "azel_to_hadec", "parallactic_angle_deg"]
__version__ = "0.1.0"

TINY = 1e-15                            # below the rounding of a unit vector: closer than this to the axis is 'at' the axis


def _angle(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}] deg")
    return math.radians(float(v))


def _turn(lon: float, lat: float, phi: float) -> Tuple[float, float]:
    """The same construction serves both directions: it is its own inverse (radians in, radians out)."""
    x = -math.cos(lon) * math.cos(lat) * math.sin(phi) + math.sin(lat) * math.cos(phi)
    y = -math.sin(lon) * math.cos(lat)
    z = math.cos(lon) * math.cos(lat) * math.cos(phi) + math.sin(lat) * math.sin(phi)
    r = math.hypot(x, y)
    return (math.atan2(y, x) if r > TINY else 0.0), math.atan2(z, r)


def hadec_to_azel(ha_deg: float, dec_deg: float, lat_deg: float) -> Tuple[float, float]:
    ha, dec = _angle(ha_deg, -360.0, 360.0, "hour angle"), _angle(dec_deg, -90.0, 90.0, "declination")
    az, el = _turn(ha, dec, _angle(lat_deg, -90.0, 90.0, "latitude"))
    az = math.degrees(az) % 360.0
    return (0.0 if az >= 360.0 else az), math.degrees(el)


def azel_to_hadec(az_deg: float, el_deg: float, lat_deg: float) -> Tuple[float, float]:
    az, el = _angle(az_deg, -360.0, 360.0, "azimuth"), _angle(el_deg, -90.0, 90.0, "elevation")
    ha, dec = _turn(az, el, _angle(lat_deg, -90.0, 90.0, "latitude"))
    ha = math.degrees(ha)
    return (180.0 if ha <= -180.0 else ha), math.degrees(dec)


def parallactic_angle_deg(ha_deg: float, dec_deg: float, lat_deg: float) -> float:
    ha, dec = _angle(ha_deg, -360.0, 360.0, "hour angle"), _angle(dec_deg, -90.0, 90.0, "declination")
    phi = _angle(lat_deg, -90.0, 90.0, "latitude")
    s = math.cos(phi) * math.sin(ha)
    c = math.sin(phi) * math.cos(dec) - math.cos(phi) * math.sin(dec) * math.cos(ha)
    if math.hypot(s, c) < TINY:
        return 0.0
    q = math.degrees(math.atan2(s, c))
    return 180.0 if q <= -180.0 else q
