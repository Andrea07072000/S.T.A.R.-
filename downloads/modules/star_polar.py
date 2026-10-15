"""star_polar - polar stereographic projection and UPS coordinates (S.T.A.R., 2026-10-06). Standard library only.

  ps_forward(lat_deg, lon_deg, pole, lon0_deg=0.0, lat_ts_deg=None, k0=1.0, a=WGS84_A, f=WGS84_F) -> (x, y) metres
  ps_inverse(x, y, pole, lon0_deg=0.0, lat_ts_deg=None, k0=1.0, a=WGS84_A, f=WGS84_F)             -> (lat_deg, lon_deg)
  ps_scale(lat_deg, pole, lat_ts_deg=None, k0=1.0, a=WGS84_A, f=WGS84_F)                          -> point scale factor
  ups_forward(lat_deg, lon_deg) -> (pole, easting, northing) on WGS-84;  ups_inverse(pole, easting, northing) -> (lat, lon)
`pole` is 'N' or 'S': the pole at the centre of the map. `lat_ts_deg` is the parallel of true scale, in the
hemisphere of that pole and given with its sign; None means the pole itself. `k0` multiplies the scale (UPS uses
the pole with k0 = 0.994). The plane has its origin at the pole; the meridian lon0 runs down the page from the
North pole (x = rho sin(dlon), y = -rho cos(dlon)) and up the page from the South pole (y = +rho cos(dlon)).
UPS: easting and northing with 2,000,000 m added, lon0 = 0, North for latitude >= 0.
Method: Snyder (USGS PP 1395, eqs. 21-33 ... 21-41) with the isometric latitude written without cancellation and
inverted by Newton's method.
Refusals (ValueError): non-numeric, boolean or non-finite input; a pole other than 'N' or 'S'; a latitude more than
60 deg on the other side of the equator from the pole; lat_ts in the other hemisphere or closer than 1 deg to the
equator; longitude outside [-180, 180]; k0 not in [0.5, 2]; a not in [1e3, 1e9] m; f not in [0, 0.1]; x or y beyond
10 a in absolute value.
"""
from __future__ import annotations

import math
import numbers
from typing import Optional, Tuple

__all__ = ["ps_forward", "ps_inverse", "ps_scale", "ups_forward", "ups_inverse", "WGS84_A", "WGS84_F"]
__version__ = "0.1.0"

WGS84_A, WGS84_F = 6378137.0, 1.0 / 298.257223563
K0_UPS, FALSE_UPS = 0.994, 2000000.0
FAR_SIDE = 60.0


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _sign(pole) -> float:
    if not isinstance(pole, str) or pole not in ("N", "S"):
        raise ValueError("pole must be 'N' or 'S'")
    return 1.0 if pole == "N" else -1.0


def _psi(phi: float, e: float) -> float:
    return math.asinh(math.tan(phi)) - e * math.atanh(e * math.sin(phi))


def _setup(pole, lat_ts_deg, k0, a, f):
    """Sign of the hemisphere, eccentricity and the constant C of rho = C exp(-psi), psi taken towards the pole."""
    s = _sign(pole)
    a, f, k0 = _real(a, 1e3, 1e9, "a (m)"), _real(f, 0.0, 0.1, "f"), _real(k0, 0.5, 2.0, "k0")
    e = math.sqrt(f * (2.0 - f))
    ts = 90.0 if lat_ts_deg is None else s * _real(lat_ts_deg, -90.0, 90.0, "latitude of true scale (deg)")
    if ts < 1.0:
        raise ValueError("the latitude of true scale must be in the hemisphere of the pole, at least 1 deg from the equator")
    if ts == 90.0:
        c = 2.0 * a / math.sqrt((1.0 + e) ** (1.0 + e) * (1.0 - e) ** (1.0 - e))
    else:
        p = math.radians(ts)
        c = a * math.cos(p) / math.sqrt(1.0 - (e * math.sin(p)) ** 2) * math.exp(_psi(p, e))
    return s, e, k0 * c, a


def _rho(lat_deg, s: float, e: float, c: float) -> Tuple[float, float]:
    lat = s * _real(lat_deg, -90.0, 90.0, "latitude (deg)")          # latitude counted towards the pole of the map
    if lat < -FAR_SIDE:
        raise ValueError("the latitude is more than 60 deg beyond the equator from the pole of the map")
    return (0.0 if lat == 90.0 else c * math.exp(-_psi(math.radians(lat), e))), lat


def ps_forward(lat_deg: float, lon_deg: float, pole: str, lon0_deg: float = 0.0, lat_ts_deg: Optional[float] = None, k0: float = 1.0,
               a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    s, e, c, _ = _setup(pole, lat_ts_deg, k0, a, f)
    rho, _ = _rho(lat_deg, s, e, c)
    dlon = math.radians(_real(lon_deg, -180.0, 180.0, "longitude (deg)") - _real(lon0_deg, -180.0, 180.0, "central meridian (deg)"))
    return rho * math.sin(dlon), -s * rho * math.cos(dlon)


def ps_inverse(x: float, y: float, pole: str, lon0_deg: float = 0.0, lat_ts_deg: Optional[float] = None, k0: float = 1.0,
               a: float = WGS84_A, f: float = WGS84_F) -> Tuple[float, float]:
    s, e, c, a = _setup(pole, lat_ts_deg, k0, a, f)
    lon0 = _real(lon0_deg, -180.0, 180.0, "central meridian (deg)")
    x, y = _real(x, -10.0 * a, 10.0 * a, "x (m)"), _real(y, -10.0 * a, 10.0 * a, "y (m)")
    rho = math.hypot(x, y)
    if rho == 0.0:
        return s * 90.0, lon0                               # the pole: every longitude is the same point
    taup = math.sinh(-math.log(rho / c))                    # tangent of the conformal latitude, towards the pole
    tau = taup
    for _ in range(10):                                     # Newton on tan(lat) (Karney 2011, eqs. 19-21)
        sigma = math.sinh(e * math.atanh(e * tau / math.hypot(1.0, tau)))
        tpi = tau * math.hypot(1.0, sigma) - sigma * math.hypot(1.0, tau)
        step = (taup - tpi) / math.hypot(1.0, tpi) * (1.0 + (1.0 - e * e) * tau * tau) / ((1.0 - e * e) * math.hypot(1.0, tau))
        tau += step
        if abs(step) <= 1e-15 * max(1.0, abs(tau)):
            break
    lat = math.degrees(math.atan(tau))
    if lat < -FAR_SIDE - 1e-9:                              # the image of the limit itself must come back
        raise ValueError("the point is more than 60 deg beyond the equator from the pole of the map")
    return s * lat, (lon0 + math.degrees(math.atan2(x, -s * y)) + 180.0) % 360.0 - 180.0


def ps_scale(lat_deg: float, pole: str, lat_ts_deg: Optional[float] = None, k0: float = 1.0, a: float = WGS84_A, f: float = WGS84_F) -> float:
    s, e, c, a = _setup(pole, lat_ts_deg, k0, a, f)
    rho, lat = _rho(lat_deg, s, e, c)
    if lat == 90.0:                                         # the limit at the pole: C sqrt((1+e)^(1+e) (1-e)^(1-e)) / (2 a)
        return c * math.sqrt((1.0 + e) ** (1.0 + e) * (1.0 - e) ** (1.0 - e)) / (2.0 * a)
    p = math.radians(lat)
    return rho * math.sqrt(1.0 - (e * math.sin(p)) ** 2) / (a * math.cos(p))


def ups_forward(lat_deg: float, lon_deg: float) -> Tuple[str, float, float]:
    pole = "N" if _real(lat_deg, -90.0, 90.0, "latitude (deg)") >= 0.0 else "S"
    x, y = ps_forward(lat_deg, lon_deg, pole, 0.0, None, K0_UPS)
    return pole, FALSE_UPS + x, FALSE_UPS + y


def ups_inverse(pole: str, easting: float, northing: float) -> Tuple[float, float]:
    _sign(pole)
    e, n = _real(easting, -1e8, 1e8, "easting (m)"), _real(northing, -1e8, 1e8, "northing (m)")
    return ps_inverse(e - FALSE_UPS, n - FALSE_UPS, pole, 0.0, None, K0_UPS)
