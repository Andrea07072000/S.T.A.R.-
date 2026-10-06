"""star_topo - look angles from a ground site: ECEF <-> local East-North-Up <-> azimuth/elevation/range
(S.T.A.R., 2026-10-06). Standard library only.

Units: degrees, metres. Ellipsoid: WGS-84 (a = 6378137 m, 1/f = 298.257223563). The site is given by geodetic
latitude, longitude and ellipsoidal height; "up" is the ellipsoid normal at the site (not the geocentric radius).
Conventions: azimuth from North, positive towards East, in [0, 360); elevation from the local horizontal plane,
in [-90, 90]; at the zenith or nadir the azimuth is undefined and returned as 0.0.
Refusals (ValueError): non-finite or non-numeric input, booleans, latitude or elevation outside [-90, 90], longitude or azimuth
outside [-360, 360], a site at
or below the Earth's centre, a zero or negative range, a target that coincides with the site, a result that
overflows. No light-time, refraction or Earth-rotation correction: geometry only.
"""
from __future__ import annotations

import math
from typing import Tuple

__all__ = ["ecef_to_enu", "enu_to_ecef", "enu_to_aer", "aer_to_enu", "ecef_to_aer", "aer_to_ecef"]
__version__ = "0.1.0"
A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
B = A * (1 - F)
Vec = Tuple[float, float, float]


def _check(*values) -> None:
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not -1e300 < v < 1e300:      # NaN fails both
            raise ValueError("inputs must be finite real numbers (magnitude below 1e300)")


def _out(*values) -> tuple:
    if not all(map(math.isfinite, values)):
        raise ValueError("result out of range")
    return values


def _site(lat_deg: float, lon_deg: float, h_m: float):
    """ECEF position of the site and the sines/cosines of its latitude and longitude."""
    _check(lat_deg, lon_deg, h_m)
    if not -90.0 <= lat_deg <= 90.0:
        raise ValueError("latitude must be within [-90, 90] deg")
    if not -360.0 <= lon_deg <= 360.0:
        raise ValueError("longitude must be within [-360, 360] deg")
    if h_m <= -B:
        raise ValueError("the site is at or below the Earth's centre")
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    sp, cp, sl, cl = math.sin(lat), math.cos(lat), math.sin(lon), math.cos(lon)
    n = A / math.sqrt(1 - E2 * sp * sp)
    return ((n + h_m) * cp * cl, (n + h_m) * cp * sl, (n * (1 - E2) + h_m) * sp), sp, cp, sl, cl


def ecef_to_enu(x: float, y: float, z: float, lat_deg: float, lon_deg: float, h_m: float) -> Vec:
    """East, North, Up (m) of the ECEF point (x, y, z) seen from the site."""
    _check(x, y, z)
    (x0, y0, z0), sp, cp, sl, cl = _site(lat_deg, lon_deg, h_m)
    dx, dy, dz = x - x0, y - y0, z - z0
    return _out(-sl * dx + cl * dy, -sp * cl * dx - sp * sl * dy + cp * dz, cp * cl * dx + cp * sl * dy + sp * dz)


def enu_to_ecef(e: float, n: float, u: float, lat_deg: float, lon_deg: float, h_m: float) -> Vec:
    """ECEF position (m) of the point with local coordinates East, North, Up at the site."""
    _check(e, n, u)
    (x0, y0, z0), sp, cp, sl, cl = _site(lat_deg, lon_deg, h_m)
    return _out(x0 - sl * e - sp * cl * n + cp * cl * u, y0 + cl * e - sp * sl * n + cp * sl * u, z0 + cp * n + sp * u)


def enu_to_aer(e: float, n: float, u: float) -> Vec:
    """Azimuth (deg, [0, 360)), elevation (deg) and range (m) of a local East-North-Up vector."""
    _check(e, n, u)
    horizontal = math.hypot(e, n)
    rng = math.hypot(horizontal, u)
    if rng == 0.0:
        raise ValueError("the target coincides with the site: no direction")
    if horizontal == 0.0:
        return _out(0.0, 90.0 if u > 0 else -90.0, rng)
    az = math.degrees(math.atan2(e, n)) % 360.0
    if az >= 360.0:                                    # -1e-20 % 360 is 360.0 in floating point
        az = 0.0
    return _out(az, math.degrees(math.atan2(u, horizontal)), rng)


def aer_to_enu(az_deg: float, el_deg: float, range_m: float) -> Vec:
    """Local East, North, Up (m) of the point at the given azimuth, elevation and range."""
    _check(az_deg, el_deg, range_m)
    if not -90.0 <= el_deg <= 90.0:
        raise ValueError("elevation must be within [-90, 90] deg")
    if not -360.0 <= az_deg <= 360.0:
        raise ValueError("azimuth must be within [-360, 360] deg")
    if range_m <= 0.0:
        raise ValueError("range must be positive")
    az, el = math.radians(az_deg), math.radians(el_deg)
    horizontal = range_m * math.cos(el)
    return _out(horizontal * math.sin(az), horizontal * math.cos(az), range_m * math.sin(el))


def ecef_to_aer(x: float, y: float, z: float, lat_deg: float, lon_deg: float, h_m: float) -> Vec:
    """Azimuth, elevation (deg) and range (m) of the ECEF point (x, y, z) seen from the site."""
    return enu_to_aer(*ecef_to_enu(x, y, z, lat_deg, lon_deg, h_m))


def aer_to_ecef(az_deg: float, el_deg: float, range_m: float, lat_deg: float, lon_deg: float, h_m: float) -> Vec:
    """ECEF position (m) of the point seen from the site at the given azimuth, elevation and range."""
    return enu_to_ecef(*aer_to_enu(az_deg, el_deg, range_m), lat_deg, lon_deg, h_m)
