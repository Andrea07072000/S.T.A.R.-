"""star_utm - transverse Mercator and UTM coordinates (S.T.A.R., 2026-10-06). Standard library only.

  tm_forward(lat_deg, lon_deg, lon0_deg, a=WGS84_A, f=WGS84_F, k0=0.9996) -> (x, y) metres from the central meridian
                                                                                 and the equator (no false origin)
  tm_inverse(x, y, lon0_deg, a=WGS84_A, f=WGS84_F, k0=0.9996)             -> (lat_deg, lon_deg)
  utm_zone(lon_deg)                                                         -> 1 ... 60
  utm_forward(lat_deg, lon_deg, zone=None) -> (zone, hemisphere, easting, northing) on WGS-84
  utm_inverse(zone, hemisphere, easting, northing) -> (lat_deg, lon_deg)
Method: Krueger's series in the third flattening n, to n^4, as written by Karney (2011), with the conformal latitude
computed without cancellation and inverted by Newton's method. Measured accuracy is in the README; the series is
used within 12 deg of the central meridian only.
UTM: false easting 500000 m, false northing 10000000 m in the southern hemisphere ('S'), k0 = 0.9996, zones of 6 deg
numbered from 180 W; a point on a zone boundary belongs to the zone to its East, and longitude 180 to zone 60.
Refusals (ValueError): non-numeric, boolean or non-finite input, latitude outside [-90, 90] (UTM: [-80, 84]),
longitude outside [-180, 180], a point further than 12 deg from the central meridian, a not in [1e3, 1e9] m,
f not in [0, 0.1], k0 not in [0.5, 2], a zone not an integer in 1 ... 60, a hemisphere other than 'N' or 'S',
x beyond 0.25 a k0 or y beyond 1.6 a k0 in absolute value, a UTM northing outside [0, 10000000].
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["tm_forward", "tm_inverse", "utm_zone", "utm_forward", "utm_inverse", "WGS84_A", "WGS84_F"]
__version__ = "0.1.0"

WGS84_A, WGS84_F = 6378137.0, 1.0 / 298.257223563
K0_UTM, FALSE_EASTING, FALSE_NORTHING = 0.9996, 500000.0, 10000000.0
MAX_DLON = 12.0


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _ellipsoid(a, f, k0):
    a, f, k0 = _real(a, 1e3, 1e9, "a (m)"), _real(f, 0.0, 0.1, "f"), _real(k0, 0.5, 2.0, "k0")
    n = f / (2.0 - f)
    n2, n3, n4 = n * n, n ** 3, n ** 4
    radius = k0 * a / (1.0 + n) * (1.0 + n2 / 4.0 + n4 / 64.0)                    # k0 times the rectifying radius
    alpha = (n / 2.0 - 2.0 * n2 / 3.0 + 5.0 * n3 / 16.0 + 41.0 * n4 / 180.0,
             13.0 * n2 / 48.0 - 3.0 * n3 / 5.0 + 557.0 * n4 / 1440.0,
             61.0 * n3 / 240.0 - 103.0 * n4 / 140.0,
             49561.0 * n4 / 161280.0)
    beta = (n / 2.0 - 2.0 * n2 / 3.0 + 37.0 * n3 / 96.0 - n4 / 360.0,
            n2 / 48.0 + n3 / 15.0 - 437.0 * n4 / 1440.0,
            17.0 * n3 / 480.0 - 37.0 * n4 / 840.0,
            4397.0 * n4 / 161280.0)
    return math.sqrt(f * (2.0 - f)), radius, alpha, beta, a * k0


def _conformal_tan(tau: float, e: float) -> float:
    """Tangent of the conformal latitude from the tangent of the geodetic one (Karney 2011, eqs. 7-9)."""
    sigma = math.sinh(e * math.atanh(e * tau / math.hypot(1.0, tau)))
    return tau * math.hypot(1.0, sigma) - sigma * math.hypot(1.0, tau)


def tm_forward(lat_deg: float, lon_deg: float, lon0_deg: float, a: float = WGS84_A, f: float = WGS84_F, k0: float = K0_UTM) -> Tuple[float, float]:
    lat, lon = _real(lat_deg, -90.0, 90.0, "latitude (deg)"), _real(lon_deg, -180.0, 180.0, "longitude (deg)")
    lon0 = _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")
    e, radius, alpha, _, _ = _ellipsoid(a, f, k0)
    dlon = (lon - lon0 + 180.0) % 360.0 - 180.0
    if abs(dlon) > MAX_DLON:
        raise ValueError("the point is more than 12 deg from the central meridian")
    if abs(lat) == 90.0:
        tau = math.copysign(1e300, lat)                     # the pole: tan is infinite, the limit is finite
    else:
        tau = math.tan(math.radians(lat))
    taup = _conformal_tan(tau, e)
    lam = math.radians(dlon)
    xi = math.atan2(taup, math.cos(lam))
    eta = math.asinh(math.sin(lam) / math.hypot(taup, math.cos(lam)))
    x, y = eta, xi
    for j, c in enumerate(alpha, start=1):
        y += c * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
        x += c * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
    return radius * x, radius * y


def tm_inverse(x: float, y: float, lon0_deg: float, a: float = WGS84_A, f: float = WGS84_F, k0: float = K0_UTM) -> Tuple[float, float]:
    lon0 = _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")
    e, radius, _, beta, scale = _ellipsoid(a, f, k0)
    eta, xi = _real(x, -0.25 * scale, 0.25 * scale, "x (m)") / radius, _real(y, -1.6 * scale, 1.6 * scale, "y (m)") / radius
    xip, etap = xi, eta
    for j, c in enumerate(beta, start=1):
        xip -= c * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
        etap -= c * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
    if abs(xip) > math.pi / 2.0:
        raise ValueError("y is beyond the pole of this projection")
    lam = math.atan2(math.sinh(etap), math.cos(xip))
    taup = math.sin(xip) / math.hypot(math.sinh(etap), math.cos(xip))
    tau = taup
    for _ in range(8):                                      # Newton (Karney 2011, eqs. 19-21): converges in 2-3 steps
        tpi = _conformal_tan(tau, e)
        step = (taup - tpi) / math.hypot(1.0, tpi) * (1.0 + (1.0 - e * e) * tau * tau) / ((1.0 - e * e) * math.hypot(1.0, tau))
        tau += step
        if abs(step) <= 1e-15 * max(1.0, abs(tau)):
            break
    dlon = math.degrees(lam)
    if abs(dlon) > MAX_DLON:
        raise ValueError("the point is more than 12 deg from the central meridian")
    return math.degrees(math.atan(tau)), (lon0 + dlon + 180.0) % 360.0 - 180.0


def utm_zone(lon_deg: float) -> int:
    lon = _real(lon_deg, -180.0, 180.0, "longitude (deg)")
    return min(60, int(math.floor((lon + 180.0) / 6.0)) + 1)


def _zone(zone) -> int:
    if isinstance(zone, bool) or not isinstance(zone, numbers.Integral) or not 1 <= int(zone) <= 60:
        raise ValueError("zone must be an integer within [1, 60]")
    return int(zone)


def utm_forward(lat_deg: float, lon_deg: float, zone=None) -> Tuple[int, str, float, float]:
    lat = _real(lat_deg, -80.0, 84.0, "latitude (deg)")
    z = utm_zone(lon_deg) if zone is None else _zone(zone)
    x, y = tm_forward(lat, lon_deg, 6.0 * z - 183.0)
    south = lat < 0.0
    return z, ("S" if south else "N"), FALSE_EASTING + x, (FALSE_NORTHING + y if south else y)


def utm_inverse(zone: int, hemisphere: str, easting: float, northing: float) -> Tuple[float, float]:
    z = _zone(zone)
    if not isinstance(hemisphere, str) or hemisphere not in ("N", "S"):
        raise ValueError("hemisphere must be 'N' or 'S'")
    e = _real(easting, -1.1e6, 2.1e6, "easting (m)")
    n = _real(northing, 0.0, FALSE_NORTHING, "northing (m)")
    return tm_inverse(e - FALSE_EASTING, n - FALSE_NORTHING if hemisphere == "S" else n, 6.0 * z - 183.0)
