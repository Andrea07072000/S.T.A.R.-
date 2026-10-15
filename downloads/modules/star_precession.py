"""star_precession - IAU 1976 precession between J2000 and the mean equator and equinox of date
(S.T.A.R., 2026-10-06). Standard library only.

  precession_matrix(jd_day, jd_frac=0.0) -> 3x3 matrix P with  r_mod = P r_j2000
  mod_from_j2000(r, jd_day, jd_frac=0.0) -> the vector referred to the mean equator and equinox of date (MOD)
  j2000_from_mod(r, jd_day, jd_frac=0.0) -> the inverse rotation (transpose)
Model: Lieske et al. (1977/1979) angles zeta, z, theta in Julian centuries of TT since J2000.0, as adopted by the IAU in
1976 and used by the FK5 system: P = R3(-z) R2(theta) R3(-zeta). This is the precession that goes with the low-precision
Sun and Moon series of star_sun and star_moon (their vectors are in MOD). It is NOT the IAU 2006 precession and it does
not include the frame bias between J2000 and GCRF (17 milliarcseconds) nor nutation.
Dates are Julian Dates (TT) given as day + fraction. Valid for 1800-2200; outside, ValueError.
Refusals (ValueError): non-numeric, boolean or non-finite input, a vector that is not three finite numbers, a date
outside the valid range.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["precession_matrix", "mod_from_j2000", "j2000_from_mod", "precession_angles_arcsec"]
__version__ = "0.1.0"
J2000 = 2451545.0
JD_MIN, JD_MAX = 2378496.5, 2524593.5              # 1800-01-01 and 2200-01-01
ZETA = (2306.2181, 0.30188, 0.017998)              # arcseconds, coefficients of T, T^2, T^3
Z = (2306.2181, 1.09468, 0.018203)
THETA = (2004.3109, -0.42665, -0.041833)
Vec = Tuple[float, float, float]
Mat = Tuple[Vec, Vec, Vec]


def _real(v) -> bool:
    try:
        return not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e150 < float(v) < 1e150      # NaN fails both
    except OverflowError:
        return False


def _centuries(jd_day, jd_frac) -> float:
    if not (_real(jd_day) and _real(jd_frac)):
        raise ValueError("the date must be given as finite real numbers")
    if not JD_MIN <= float(jd_day) + float(jd_frac) <= JD_MAX:
        raise ValueError("date outside 1800-2200")
    return ((float(jd_day) - J2000) + float(jd_frac)) / 36525.0


def _vec(r) -> Vec:
    try:
        ok = not isinstance(r, (str, bytes, dict, set, frozenset)) and len(r) == 3
        items = (r[0], r[1], r[2]) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok or not all(_real(x) for x in items):
        raise ValueError("the vector must be a sequence of three finite real numbers")
    return float(items[0]), float(items[1]), float(items[2])


def precession_angles_arcsec(jd_day: float, jd_frac: float = 0.0) -> Vec:
    """(zeta, z, theta) in arcseconds."""
    t = _centuries(jd_day, jd_frac)
    return tuple(t * (c[0] + t * (c[1] + t * c[2])) for c in (ZETA, Z, THETA))


def precession_matrix(jd_day: float, jd_frac: float = 0.0) -> Mat:
    zeta, z, theta = (math.radians(a / 3600.0) for a in precession_angles_arcsec(jd_day, jd_frac))
    cz, sz, cq, sq, ct, st = math.cos(zeta), math.sin(zeta), math.cos(z), math.sin(z), math.cos(theta), math.sin(theta)
    return ((cq * ct * cz - sq * sz, -cq * ct * sz - sq * cz, -cq * st),
            (sq * ct * cz + cq * sz, -sq * ct * sz + cq * cz, -sq * st),
            (st * cz, -st * sz, ct))


def mod_from_j2000(r: Sequence[float], jd_day: float, jd_frac: float = 0.0) -> Vec:
    x, y, z = _vec(r)
    p = precession_matrix(jd_day, jd_frac)
    return tuple(p[i][0] * x + p[i][1] * y + p[i][2] * z for i in range(3))


def j2000_from_mod(r: Sequence[float], jd_day: float, jd_frac: float = 0.0) -> Vec:
    x, y, z = _vec(r)
    p = precession_matrix(jd_day, jd_frac)
    return tuple(p[0][i] * x + p[1][i] * y + p[2][i] * z for i in range(3))
