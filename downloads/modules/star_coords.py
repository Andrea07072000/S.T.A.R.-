"""star_coords - spherical and cylindrical coordinates <-> rectangular (S.T.A.R., 2026-10-06). Standard library only.

  spherical_to_xyz(lon_deg, lat_deg, r=1.0) -> (x, y, z)        x = r cos(lat) cos(lon), y = r cos(lat) sin(lon), z = r sin(lat)
  xyz_to_spherical(x, y, z) -> (lon in [0, 360), lat, r)
  cylindrical_to_xyz(rho, lon_deg, z) -> (x, y, z)              x = rho cos(lon), y = rho sin(lon)
  xyz_to_cylindrical(x, y, z) -> (rho, lon in [0, 360), z)
Longitude is counted from +x towards +y; latitude from the xy plane towards +z (right ascension and declination,
longitude and geocentric latitude, azimuth-like and elevation-like angles of any right-handed frame).
On the z axis the longitude is undefined and returned as 0; the zero vector has latitude 0 too.
The length is computed without intermediate overflow or underflow (hypot), so components from 1e-300 to 1e300 keep
their digits.
Refusals (ValueError): non-numeric, boolean or non-finite input, longitude outside [-360, 360], latitude outside
[-90, 90], a negative radius, any length or component above 1e300 in absolute value.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["spherical_to_xyz", "xyz_to_spherical", "cylindrical_to_xyz", "xyz_to_cylindrical"]
__version__ = "0.1.0"

BIG = 1e300
Vec = Tuple[float, float, float]


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _lon(x: float, y: float) -> float:
    if x == 0.0 and y == 0.0:
        return 0.0                                          # on the axis: undefined
    d = math.degrees(math.atan2(y, x)) % 360.0
    return 0.0 if d >= 360.0 else d


def spherical_to_xyz(lon_deg: float, lat_deg: float, r: float = 1.0) -> Vec:
    lon, lat = math.radians(_real(lon_deg, -360.0, 360.0, "longitude (deg)")), math.radians(_real(lat_deg, -90.0, 90.0, "latitude (deg)"))
    radius = _real(r, 0.0, BIG, "radius")
    c = radius * math.cos(lat)
    return c * math.cos(lon), c * math.sin(lon), radius * math.sin(lat)


def xyz_to_spherical(x: float, y: float, z: float) -> Vec:
    x, y, z = _real(x, -BIG, BIG, "x"), _real(y, -BIG, BIG, "y"), _real(z, -BIG, BIG, "z")
    rho = math.hypot(x, y)
    return _lon(x, y), math.degrees(math.atan2(z, rho)), math.hypot(rho, z)


def cylindrical_to_xyz(rho: float, lon_deg: float, z: float) -> Vec:
    radius = _real(rho, 0.0, BIG, "rho")
    lon = math.radians(_real(lon_deg, -360.0, 360.0, "longitude (deg)"))
    return radius * math.cos(lon), radius * math.sin(lon), _real(z, -BIG, BIG, "z")


def xyz_to_cylindrical(x: float, y: float, z: float) -> Vec:
    x, y, z = _real(x, -BIG, BIG, "x"), _real(y, -BIG, BIG, "y"), _real(z, -BIG, BIG, "z")
    return math.hypot(x, y), _lon(x, y), z
