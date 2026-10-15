"""star_sphere - angles between directions on the sphere (S.T.A.R., 2026-10-06). Standard library only.

Directions are (longitude, latitude) pairs in degrees: right ascension and declination, azimuth and elevation,
geographic longitude and latitude on a sphere - the geometry is the same.
  separation_deg(lon1, lat1, lon2, lat2)      angle between the two directions, [0, 180]
  position_angle_deg(lon1, lat1, lon2, lat2)  direction of point 2 seen from point 1, from North through East, [0, 360)
  offset(lon1, lat1, position_angle_deg, distance_deg) -> (lon2, lat2): the point at that angle and distance
The separation uses the formula that is accurate at every distance (arc-tangent form): the textbook arc-cosine loses
half of the digits for nearby directions and the haversine loses them near the antipode.
At a pole the position angle follows the same limit as the libraries (atan2 of the same two quantities); for
coincident directions it is returned as 0.0. Longitude out is in [0, 360).
Refusals (ValueError): non-numeric, boolean or non-finite input, latitude outside [-90, 90], longitude or position
angle outside [-360, 360], distance outside [0, 180].
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["separation_deg", "position_angle_deg", "offset"]
__version__ = "0.1.1"


def _angle(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}] deg")
    return math.radians(float(v))


def _points(lon1, lat1, lon2, lat2):
    return (_angle(lon1, -360.0, 360.0, "longitude"), _angle(lat1, -90.0, 90.0, "latitude"),
            _angle(lon2, -360.0, 360.0, "longitude"), _angle(lat2, -90.0, 90.0, "latitude"))


def _wrap360(deg: float) -> float:
    d = deg % 360.0
    return 0.0 if d >= 360.0 else d


def _differences(lon1, lat1, lon2, lat2):
    """Differences of longitude and latitude in radians, taken in DEGREES first: the subtraction of two close floats is
    exact, the difference of their conversions to radians is not (0.1.1: at 1e-9 deg apart near longitude 40 the
    separation was wrong in its sixth digit)."""
    return math.radians(float(lon2) - float(lon1)), math.radians(float(lat2) - float(lat1))


def _towards_north(s1: float, c2: float, dl: float, db: float) -> float:
    """cos(b1) sin(b2) - sin(b1) cos(b2) cos(dl), written as sin(b2 - b1) + 2 sin(b1) cos(b2) sin^2(dl / 2): no
    subtraction of nearly equal products when the two directions are close."""
    return math.sin(db) + 2.0 * s1 * c2 * math.sin(dl / 2.0) ** 2


def separation_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = _points(lon1, lat1, lon2, lat2)
    dl, db = _differences(lon1, lat1, lon2, lat2)
    s1, c1, s2, c2, sd, cd = math.sin(b1), math.cos(b1), math.sin(b2), math.cos(b2), math.sin(dl), math.cos(dl)
    return math.degrees(math.atan2(math.hypot(c2 * sd, _towards_north(s1, c2, dl, db)), s1 * s2 + c1 * c2 * cd))


def position_angle_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = _points(lon1, lat1, lon2, lat2)
    dl, db = _differences(lon1, lat1, lon2, lat2)
    y = math.cos(b2) * math.sin(dl)
    x = _towards_north(math.sin(b1), math.cos(b2), dl, db)
    if math.hypot(x, y) < 1e-300:
        return 0.0                                          # coincident (or antipodal) directions: undefined
    return _wrap360(math.degrees(math.atan2(y, x)))


def offset(lon1: float, lat1: float, position_angle: float, distance: float) -> Tuple[float, float]:
    l1, b1 = _angle(lon1, -360.0, 360.0, "longitude"), _angle(lat1, -90.0, 90.0, "latitude")
    pa, d = _angle(position_angle, -360.0, 360.0, "position angle"), _angle(distance, 0.0, 180.0, "distance")
    s1, c1, sd, cd = math.sin(b1), math.cos(b1), math.sin(d), math.cos(d)
    z = s1 * cd + c1 * sd * math.cos(pa)                    # sine of the new latitude
    y = sd * math.sin(pa)                                   # towards East, in the tangent plane of the start
    x = c1 * cd - s1 * sd * math.cos(pa)
    lat2 = math.atan2(z, math.hypot(x, y))
    lon2 = l1 + (math.atan2(y, x) if math.hypot(x, y) > 1e-300 else 0.0)
    return _wrap360(math.degrees(lon2)), math.degrees(lat2)
