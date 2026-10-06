"""star_lcc - Lambert conformal conic projection with two standard parallels (S.T.A.R., 2026-10-06).
Standard library only.

  lcc_forward(lat_deg, lon_deg, lat1_deg, lat2_deg, lat0_deg, lon0_deg, a=WGS84_A, f=WGS84_F) -> (x, y) metres
  lcc_inverse(x, y, lat1_deg, lat2_deg, lat0_deg, lon0_deg, a=WGS84_A, f=WGS84_F)             -> (lat_deg, lon_deg)
  lcc_scale(lat_deg, lat1_deg, lat2_deg, a=WGS84_A, f=WGS84_F)                                -> point scale factor k
lat1 and lat2 are the standard parallels (scale exactly 1 there; equal parallels give the tangent cone), lat0 and
lon0 the origin of the coordinates; x grows to the East, y to the North; no false origin.
Method: Snyder (USGS PP 1395, eqs. 15-1 ... 15-11), with the isometric latitude written as asinh(tan(lat)) -
e atanh(e sin(lat)) so that nothing cancels, and inverted by Newton's method.
Refusals (ValueError): non-numeric, boolean or non-finite input; latitude, lat0 or a standard parallel outside
[-89, 89]; longitude or lon0 outside [-180, 180]; standard parallels on opposite sides of the equator or closer than
1e-3 deg to it (the cone degenerates into a cylinder); a not in [1e3, 1e9] m; f not in [0, 0.1]; x or y beyond
1e3 a in absolute value; a point that falls beyond the pole of the cone.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["lcc_forward", "lcc_inverse", "lcc_scale", "WGS84_A", "WGS84_F"]
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


def _psi(phi: float, e: float) -> float:
    """Isometric latitude (radians in)."""
    return math.asinh(math.tan(phi)) - e * math.atanh(e * math.sin(phi))


def _m(phi: float, e: float) -> float:
    return math.cos(phi) / math.sqrt(1.0 - (e * math.sin(phi)) ** 2)


def _cone(lat1_deg, lat2_deg, a, f):
    """Eccentricity, cone constant n and a * F of the cone: rho = a F exp(-n psi)."""
    p1, p2 = _real(lat1_deg, -MAX_LAT, MAX_LAT, "first standard parallel (deg)"), _real(lat2_deg, -MAX_LAT, MAX_LAT, "second standard parallel (deg)")
    a, f = _real(a, 1e3, 1e9, "a (m)"), _real(f, 0.0, 0.1, "f")
    if p1 * p2 <= 0.0 or min(abs(p1), abs(p2)) < MIN_PARALLEL:
        raise ValueError("the standard parallels must be on the same side of the equator and at least 1e-3 deg from it")
    e = math.sqrt(f * (2.0 - f))
    phi1, phi2 = math.radians(p1), math.radians(p2)
    if p1 == p2:
        n = math.sin(phi1)
    else:
        n = (math.log(_m(phi1, e)) - math.log(_m(phi2, e))) / (_psi(phi2, e) - _psi(phi1, e))
    return e, n, a * _m(phi1, e) / n * math.exp(n * _psi(phi1, e)), a


def _origin(lat0_deg, lon0_deg):
    return math.radians(_real(lat0_deg, -MAX_LAT, MAX_LAT, "latitude of origin (deg)")), _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")


def lcc_forward(lat_deg: float, lon_deg: float, lat1_deg: float, lat2_deg: float, lat0_deg: float, lon0_deg: float,
                a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    phi, lon = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)")), _real(lon_deg, -180.0, 180.0, "longitude (deg)")
    e, n, af, _ = _cone(lat1_deg, lat2_deg, a, f)
    phi0, lon0 = _origin(lat0_deg, lon0_deg)
    rho, rho0 = af * math.exp(-n * _psi(phi, e)), af * math.exp(-n * _psi(phi0, e))
    theta = n * math.radians((lon - lon0 + 180.0) % 360.0 - 180.0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def lcc_inverse(x: float, y: float, lat1_deg: float, lat2_deg: float, lat0_deg: float, lon0_deg: float,
                a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    e, n, af, a = _cone(lat1_deg, lat2_deg, a, f)
    phi0, lon0 = _origin(lat0_deg, lon0_deg)
    x, y = _real(x, -1e3 * a, 1e3 * a, "x (m)"), _real(y, -1e3 * a, 1e3 * a, "y (m)")
    rho0 = af * math.exp(-n * _psi(phi0, e))
    sign = math.copysign(1.0, n)
    rho = math.hypot(x, rho0 - y)                           # |rho|; the cone's pole is rho = 0
    theta = math.atan2(sign * x, sign * (rho0 - y))
    if rho == 0.0 or abs(theta / n) > math.pi:
        raise ValueError("the point is at or beyond the pole of the cone")
    psi = -math.log(rho / abs(af)) / n
    taup = math.sinh(psi)                                   # tangent of the conformal latitude
    tau = taup
    for _ in range(10):                                     # Newton on tan(lat) (Karney 2011, eqs. 19-21)
        sigma = math.sinh(e * math.atanh(e * tau / math.hypot(1.0, tau)))
        tpi = tau * math.hypot(1.0, sigma) - sigma * math.hypot(1.0, tau)
        step = (taup - tpi) / math.hypot(1.0, tpi) * (1.0 + (1.0 - e * e) * tau * tau) / ((1.0 - e * e) * math.hypot(1.0, tau))
        tau += step
        if abs(step) <= 1e-15 * max(1.0, abs(tau)):
            break
    lat = math.degrees(math.atan(tau))
    if abs(lat) > MAX_LAT:
        raise ValueError("the point is beyond 89 deg of latitude")
    return lat, (lon0 + math.degrees(theta / n) + 180.0) % 360.0 - 180.0


def lcc_scale(lat_deg: float, lat1_deg: float, lat2_deg: float, a: float = WGS84_A, f: float = WGS84_F) -> float:
    phi = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)"))
    e, n, af, a = _cone(lat1_deg, lat2_deg, a, f)
    return af * math.exp(-n * _psi(phi, e)) * n / (a * _m(phi, e))
