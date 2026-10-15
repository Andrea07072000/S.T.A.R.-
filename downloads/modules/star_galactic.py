"""star_galactic - equatorial <-> galactic directions (S.T.A.R., 2026-10-06). Standard library only.

  equatorial_to_galactic(ra_deg, dec_deg, system="icrs") -> (l in [0, 360), b) in degrees
  galactic_to_equatorial(l_deg, b_deg, system="icrs")    -> (right ascension in [0, 360), declination) in degrees
Two definitions of the galactic frame, each by the equatorial direction of the galactic pole and the galactic
longitude of the celestial pole:
  "icrs"   Hipparcos (ESA 1997, vol. 1, 1.5.3): pole at 192.85948, +27.12825; longitude of the celestial pole 122.93192
  "b1950"  IAU 1958 (Blaauw et al. 1960): pole at 192.25, +27.4; longitude of the celestial pole 123.0;
           the equatorial directions are B1950.0 (FK4 without E-terms)
No precession and no FK4 -> FK5 conversion is applied: the directions must already be in the system named.
At a pole of the target frame the longitude is undefined and the value returned is arbitrary within [0, 360).
Refusals (ValueError): non-numeric, boolean or non-finite input, latitude or declination outside [-90, 90],
longitude or right ascension outside [-360, 360], an unknown system.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["equatorial_to_galactic", "galactic_to_equatorial"]
__version__ = "0.1.0"

# system: (right ascension of the galactic pole, its declination, galactic longitude of the celestial pole), degrees
SYSTEMS = {"icrs": (192.85948, 27.12825, 122.93192), "b1950": (192.25, 27.4, 123.0)}


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}] deg")
    return math.radians(float(v))


def _wrap360(deg: float) -> float:
    d = deg % 360.0
    return 0.0 if d >= 360.0 else d


def _system(system) -> Tuple[float, float, float]:
    if not isinstance(system, str) or system not in SYSTEMS:
        raise ValueError("system must be 'icrs' or 'b1950'")
    return tuple(math.radians(x) for x in SYSTEMS[system])


def _about_pole(lon: float, lat: float, pole_lon: float, pole_lat: float) -> Tuple[float, float]:
    """Latitude above the equator whose pole is (pole_lon, pole_lat), and the angle at that pole measured from the
    great circle through the old pole, in the direction of increasing old longitude (radians)."""
    d = lon - pole_lon
    s = math.sin(lat) * math.sin(pole_lat) + math.cos(lat) * math.cos(pole_lat) * math.cos(d)
    n = math.cos(lat) * math.sin(d)
    c = math.sin(lat) * math.cos(pole_lat) - math.cos(lat) * math.sin(pole_lat) * math.cos(d)
    return math.atan2(s, math.hypot(n, c)), math.atan2(n, c)


def equatorial_to_galactic(ra_deg: float, dec_deg: float, system: str = "icrs") -> Tuple[float, float]:
    a, d = _real(ra_deg, -360.0, 360.0, "right ascension"), _real(dec_deg, -90.0, 90.0, "declination")
    ra_p, dec_p, l_ncp = _system(system)
    b, ang = _about_pole(a, d, ra_p, dec_p)
    return _wrap360(math.degrees(l_ncp - ang)), math.degrees(b)


def galactic_to_equatorial(l_deg: float, b_deg: float, system: str = "icrs") -> Tuple[float, float]:
    lon, lat = _real(l_deg, -360.0, 360.0, "galactic longitude"), _real(b_deg, -90.0, 90.0, "galactic latitude")
    ra_p, dec_p, l_ncp = _system(system)
    # seen from the galactic frame the celestial pole is at (l_ncp, dec_p) and the same construction applies, mirrored
    dec, ang = _about_pole(l_ncp, lat, lon, dec_p)
    return _wrap360(math.degrees(ra_p + ang)), math.degrees(dec)
