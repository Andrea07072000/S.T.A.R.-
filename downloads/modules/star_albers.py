"""star_albers - Albers equal-area conic projection (S.T.A.R., 2026-10-06). Standard library only.

  albers_forward(lat_deg, lon_deg, lat1_deg, lat2_deg, lat0_deg, lon0_deg, a=WGS84_A, f=WGS84_F) -> (x, y) metres
  albers_inverse(x, y, lat1_deg, lat2_deg, lat0_deg, lon0_deg, a=WGS84_A, f=WGS84_F)             -> (lat_deg, lon_deg)
  albers_scale(lat_deg, lat1_deg, lat2_deg, a=WGS84_A, f=WGS84_F) -> (h, k): scale along the meridian and along the
                                                                    parallel; h * k = 1 (areas are preserved)
lat1 and lat2 are the standard parallels (k = 1 there; equal parallels give the tangent cone), lat0 and lon0 the
origin of the coordinates; x grows to the East, y to the North; no false origin.
Method: Snyder (USGS PP 1395, eqs. 14-1 ... 14-21) with the authalic function q written with atanh, and its inverse
by Newton's method (eq. 3-16).
Refusals (ValueError): non-numeric, boolean or non-finite input; latitude, lat0 or a standard parallel outside
[-89, 89]; longitude or lon0 outside [-180, 180]; standard parallels on opposite sides of the equator or closer than
1e-3 deg to it; a not in [1e3, 1e9] m; f not in [0, 0.1]; x or y beyond 10 a in absolute value; a point outside the
image of the latitudes -89 ... 89.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["albers_forward", "albers_inverse", "albers_scale", "WGS84_A", "WGS84_F"]
__version__ = "0.1.0"

WGS84_A, WGS84_F = 6378137.0, 1.0 / 298.257223563
MAX_LAT = 89.0
MIN_PARALLEL = 1e-3


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _q(sin_phi: float, e: float) -> float:
    """Authalic function: 2 sin(phi) on the sphere."""
    if e < 1e-9:
        return 2.0 * sin_phi
    return (1.0 - e * e) * (sin_phi / (1.0 - (e * sin_phi) ** 2) + math.atanh(e * sin_phi) / e)


def _m2(phi: float, e: float) -> float:
    return math.cos(phi) ** 2 / (1.0 - (e * math.sin(phi)) ** 2)


def _cone(lat1_deg, lat2_deg, a, f):
    """Eccentricity, cone constant n, the constant C and a: rho = a sqrt(C - n q) / n."""
    p1, p2 = _real(lat1_deg, -MAX_LAT, MAX_LAT, "first standard parallel (deg)"), _real(lat2_deg, -MAX_LAT, MAX_LAT, "second standard parallel (deg)")
    a, f = _real(a, 1e3, 1e9, "a (m)"), _real(f, 0.0, 0.1, "f")
    if p1 * p2 <= 0.0 or min(abs(p1), abs(p2)) < MIN_PARALLEL:
        raise ValueError("the standard parallels must be on the same side of the equator and at least 1e-3 deg from it")
    e = math.sqrt(f * (2.0 - f))
    phi1, phi2 = math.radians(p1), math.radians(p2)
    q1 = _q(math.sin(phi1), e)
    if p1 == p2:
        n = math.sin(phi1)
    else:
        n = (_m2(phi1, e) - _m2(phi2, e)) / (_q(math.sin(phi2), e) - q1)
    return e, n, _m2(phi1, e) + n * q1, a


def _rho(phi: float, e: float, n: float, c: float, a: float) -> float:
    return a * math.sqrt(max(0.0, c - n * _q(math.sin(phi), e))) / n


def _origin(lat0_deg, lon0_deg):
    return math.radians(_real(lat0_deg, -MAX_LAT, MAX_LAT, "latitude of origin (deg)")), _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")


def albers_forward(lat_deg: float, lon_deg: float, lat1_deg: float, lat2_deg: float, lat0_deg: float, lon0_deg: float,
                   a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    phi, lon = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)")), _real(lon_deg, -180.0, 180.0, "longitude (deg)")
    e, n, c, a = _cone(lat1_deg, lat2_deg, a, f)
    phi0, lon0 = _origin(lat0_deg, lon0_deg)
    rho, rho0 = _rho(phi, e, n, c, a), _rho(phi0, e, n, c, a)
    theta = n * math.radians((lon - lon0 + 180.0) % 360.0 - 180.0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def albers_inverse(x: float, y: float, lat1_deg: float, lat2_deg: float, lat0_deg: float, lon0_deg: float,
                   a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    e, n, c, a = _cone(lat1_deg, lat2_deg, a, f)
    phi0, lon0 = _origin(lat0_deg, lon0_deg)
    x, y = _real(x, -10.0 * a, 10.0 * a, "x (m)"), _real(y, -10.0 * a, 10.0 * a, "y (m)")
    rho0 = _rho(phi0, e, n, c, a)
    sign = math.copysign(1.0, n)
    rho = math.hypot(x, rho0 - y)
    theta = math.atan2(sign * x, sign * (rho0 - y))
    q = (c - (rho * n / a) ** 2) / n
    q89 = _q(math.sin(math.radians(MAX_LAT)), e)
    if abs(q) > q89 * (1.0 + 1e-12) or abs(theta / n) > math.pi:
        raise ValueError("the point is outside the image of the latitudes -89 ... 89 on this cone")
    q = max(-q89, min(q89, q))
    if e < 1e-9:
        phi = math.asin(q / 2.0)
    else:
        phi = math.asin(max(-1.0, min(1.0, q / 2.0)))
        for _ in range(12):                                 # Newton (Snyder 3-16)
            s = math.sin(phi)
            w = 1.0 - (e * s) ** 2
            step = w * w / (2.0 * math.cos(phi)) * (q / (1.0 - e * e) - s / w - math.atanh(e * s) / e)
            phi += step
            if abs(step) <= 1e-15:
                break
    return math.degrees(phi), (lon0 + math.degrees(theta / n) + 180.0) % 360.0 - 180.0


def albers_scale(lat_deg: float, lat1_deg: float, lat2_deg: float, a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    phi = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)"))
    e, n, c, a = _cone(lat1_deg, lat2_deg, a, f)
    k = _rho(phi, e, n, c, a) * n / (a * math.sqrt(_m2(phi, e)))
    return 1.0 / k, k
