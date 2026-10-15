"""star_mercator - Mercator projection on the ellipsoid, and Web Mercator (S.T.A.R., 2026-10-06).
Standard library only.

  mercator_forward(lat_deg, lon_deg, lon0_deg=0.0, lat_ts_deg=0.0, a=WGS84_A, f=WGS84_F) -> (x, y) metres
  mercator_inverse(x, y, lon0_deg=0.0, lat_ts_deg=0.0, a=WGS84_A, f=WGS84_F)             -> (lat_deg, lon_deg)
  mercator_scale(lat_deg, lat_ts_deg=0.0, f=WGS84_F)                                      -> point scale factor k
  web_mercator_forward(lat_deg, lon_deg) -> (x, y);  web_mercator_inverse(x, y) -> (lat_deg, lon_deg)
The ellipsoidal Mercator is conformal: y = a k0 psi, with psi the isometric latitude, and k0 the scale at the
equator that makes the scale 1 on the parallels +-lat_ts (k0 = 1 for lat_ts = 0). Rhumb lines are straight.
Web Mercator (EPSG:3857) is NOT that projection: it applies the formulas of the sphere of radius 6378137 m to
geodetic latitudes; it is offered because every web map uses it, and it is not conformal.
Longitudes returned by the inverses are in [-180, 180).
Refusals (ValueError): non-numeric, boolean or non-finite input; latitude outside [-89.5, 89.5]; lat_ts outside
[-80, 80]; longitude or lon0 outside [-180, 180]; a not in [1e3, 1e9] m; f not in [0, 0.1]; x beyond pi a k0 (half a
turn) or y beyond the image of latitude 89.5 in absolute value.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["mercator_forward", "mercator_inverse", "mercator_scale", "web_mercator_forward", "web_mercator_inverse", "WGS84_A", "WGS84_F"]
__version__ = "0.1.0"

WGS84_A, WGS84_F = 6378137.0, 1.0 / 298.257223563
MAX_LAT = 89.5
MAX_TS = 80.0


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _wrap180(deg: float) -> float:
    d = (deg + 180.0) % 360.0 - 180.0
    return -180.0 if d >= 180.0 else d                      # -180 - 3e-14 would round up to +180


def _psi(phi: float, e: float) -> float:
    """Isometric latitude (radians in)."""
    return math.asinh(math.tan(phi)) - e * math.atanh(e * math.sin(phi))


def _setup(lat_ts_deg, a, f):
    a, f = _real(a, 1e3, 1e9, "a (m)"), _real(f, 0.0, 0.1, "f")
    ts = math.radians(_real(lat_ts_deg, -MAX_TS, MAX_TS, "latitude of true scale (deg)"))
    e = math.sqrt(f * (2.0 - f))
    return e, a * math.cos(ts) / math.sqrt(1.0 - (e * math.sin(ts)) ** 2)        # e and a * k0


def mercator_forward(lat_deg: float, lon_deg: float, lon0_deg: float = 0.0, lat_ts_deg: float = 0.0,
                     a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    phi, lon = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)")), _real(lon_deg, -180.0, 180.0, "longitude (deg)")
    lon0 = _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")
    e, ak0 = _setup(lat_ts_deg, a, f)
    return ak0 * math.radians(_wrap180(lon - lon0)), ak0 * _psi(phi, e)


def mercator_inverse(x: float, y: float, lon0_deg: float = 0.0, lat_ts_deg: float = 0.0,
                     a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    lon0 = _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")
    e, ak0 = _setup(lat_ts_deg, a, f)
    y_max = ak0 * _psi(math.radians(MAX_LAT), e)
    x = _real(x, -math.pi * ak0, math.pi * ak0, "x (m)")
    y = _real(y, -y_max * (1.0 + 1e-12), y_max * (1.0 + 1e-12), "y (m)")
    taup = math.sinh(y / ak0)                               # tangent of the conformal latitude
    tau = taup
    for _ in range(10):                                     # Newton on tan(lat) (Karney 2011, eqs. 19-21)
        sigma = math.sinh(e * math.atanh(e * tau / math.hypot(1.0, tau)))
        tpi = tau * math.hypot(1.0, sigma) - sigma * math.hypot(1.0, tau)
        step = (taup - tpi) / math.hypot(1.0, tpi) * (1.0 + (1.0 - e * e) * tau * tau) / ((1.0 - e * e) * math.hypot(1.0, tau))
        tau += step
        if abs(step) <= 1e-15 * max(1.0, abs(tau)):
            break
    return math.degrees(math.atan(tau)), _wrap180(lon0 + math.degrees(x / ak0))


def mercator_scale(lat_deg: float, lat_ts_deg: float = 0.0, f: float = WGS84_F) -> float:
    phi = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)"))
    e, k0 = _setup(lat_ts_deg, 1e3, f)
    return k0 / 1e3 * math.sqrt(1.0 - (e * math.sin(phi)) ** 2) / math.cos(phi)


def web_mercator_forward(lat_deg: float, lon_deg: float) -> Tuple[float, float]:
    phi, lon = math.radians(_real(lat_deg, -MAX_LAT, MAX_LAT, "latitude (deg)")), _real(lon_deg, -180.0, 180.0, "longitude (deg)")
    return WGS84_A * math.radians(lon), WGS84_A * math.asinh(math.tan(phi))


def web_mercator_inverse(x: float, y: float) -> Tuple[float, float]:
    y_max = WGS84_A * math.asinh(math.tan(math.radians(MAX_LAT)))
    x = _real(x, -math.pi * WGS84_A, math.pi * WGS84_A, "x (m)")
    y = _real(y, -y_max * (1.0 + 1e-12), y_max * (1.0 + 1e-12), "y (m)")
    return math.degrees(math.atan(math.sinh(y / WGS84_A))), _wrap180(math.degrees(x / WGS84_A))
