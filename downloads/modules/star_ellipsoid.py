"""star_ellipsoid - the WGS-84 ellipsoid as a surface: radii of curvature, auxiliary latitudes, meridian arc
(S.T.A.R., 2026-10-06). Standard library only.

All functions take the GEODETIC latitude in degrees and return metres or degrees:
  meridian_radius(lat)         M, radius of curvature in the meridian (north-south)
  prime_vertical_radius(lat)   N, radius of curvature in the prime vertical (east-west)
  gaussian_radius(lat)         sqrt(M N), mean radius of curvature at the point
  geocentric_radius(lat)       distance from the centre of the Earth to the surface point
  geocentric_latitude(lat)     angle at the centre between the equator and the surface point
  parametric_latitude(lat)     reduced latitude (the one of the auxiliary sphere used by geodesic methods)
  meridian_arc(lat)            distance along the meridian from the equator (negative in the south)
  rectifying_latitude(lat)     latitude on the sphere whose meridian has the same length
Constants: a = 6378137 m, 1/f = 298.257223563. The meridian arc uses Helmert's series in the third flattening up to
n^5 (error below a micrometre for the Earth). On the sphere-like scale of a degree: 1 deg of latitude is
meridian_radius * pi/180 metres, 1 deg of longitude is prime_vertical_radius * cos(lat) * pi/180 metres.
Refusals (ValueError): non-numeric, boolean or non-finite input, latitude outside [-90, 90].
"""
from __future__ import annotations

import math
import numbers

__all__ = ["meridian_radius", "prime_vertical_radius", "gaussian_radius", "geocentric_radius", "geocentric_latitude",
           "parametric_latitude", "meridian_arc", "rectifying_latitude", "A", "F", "B", "E2", "MERIDIAN_QUADRANT"]
__version__ = "0.1.0"
A = 6378137.0
F = 1 / 298.257223563
B = A * (1 - F)
E2 = F * (2 - F)
_N = F / (2 - F)                                       # third flattening
_ARC0 = A / (1 + _N) * (1 + _N ** 2 / 4 + _N ** 4 / 64 + _N ** 6 / 256)
_ARC = (-1.5 * (_N - _N ** 3 / 8 - _N ** 5 / 64), 15 / 16 * (_N ** 2 - _N ** 4 / 4), -35 / 48 * (_N ** 3 - 5 * _N ** 5 / 16),
        315 / 512 * _N ** 4, -693 / 1280 * _N ** 5)
MERIDIAN_QUADRANT = _ARC0 * math.pi / 2


def _lat(lat_deg) -> float:
    try:
        ok = not isinstance(lat_deg, bool) and isinstance(lat_deg, numbers.Real) and -90.0 <= float(lat_deg) <= 90.0     # NaN fails
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("latitude must be a real number within [-90, 90] deg")
    return math.radians(float(lat_deg))


def _w2(phi: float) -> float:
    return 1.0 - E2 * math.sin(phi) ** 2


def meridian_radius(lat_deg: float) -> float:
    return A * (1 - E2) / _w2(_lat(lat_deg)) ** 1.5


def prime_vertical_radius(lat_deg: float) -> float:
    return A / math.sqrt(_w2(_lat(lat_deg)))


def gaussian_radius(lat_deg: float) -> float:
    return B / _w2(_lat(lat_deg))                       # sqrt(M N) = a sqrt(1 - e^2) / w^2 = b / w^2


def geocentric_radius(lat_deg: float) -> float:
    phi = _lat(lat_deg)
    c, s = A * math.cos(phi), B * math.sin(phi)
    return math.hypot(A * c, B * s) / math.hypot(c, s)


def geocentric_latitude(lat_deg: float) -> float:
    phi = _lat(lat_deg)
    return math.degrees(math.atan2((1 - E2) * math.sin(phi), math.cos(phi)))


def parametric_latitude(lat_deg: float) -> float:
    phi = _lat(lat_deg)
    return math.degrees(math.atan2((1 - F) * math.sin(phi), math.cos(phi)))


def meridian_arc(lat_deg: float) -> float:
    phi = _lat(lat_deg)
    # the sine terms are scaled by a / (1 + n), NOT by the coefficient of phi (2026-10-06: scaling them by _ARC0
    # multiplied them by 1 + n^2/4 and put the arc 1.1 cm off at mid latitudes; found by the cross-check)
    return _ARC0 * phi + A / (1 + _N) * sum(c * math.sin(2 * (k + 1) * phi) for k, c in enumerate(_ARC))


def rectifying_latitude(lat_deg: float) -> float:
    return 90.0 * meridian_arc(lat_deg) / MERIDIAN_QUADRANT
