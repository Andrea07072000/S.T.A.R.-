# -*- coding: utf-8 -*-
"""star_sidereal — Greenwich Mean Sidereal Time, IAU 1982 model (S.T.A.R., 2026-10-04). Standard library.

GMST(UT1) = 67310.54841 s + (876600 h + 8640184.812866 s) T + 0.093104 T^2 - 6.2e-6 T^3, T in Julian centuries of
UT1 from J2000 (Vallado, Fundamentals of Astrodynamics, eq. 3-47; Aoki et al. 1982). Returns degrees in [0, 360).
Input is a UT1 Julian date split in two parts (day + fraction) to keep precision, as in ERFA/SOFA.
"""
from __future__ import annotations

import math


def gmst82_deg(jd_ut1_day: float, jd_ut1_frac: float = 0.0) -> float:
    """GMST in degrees, [0, 360). Raises ValueError for non-finite input."""
    if not (math.isfinite(jd_ut1_day) and math.isfinite(jd_ut1_frac)):
        raise ValueError("Julian date must be finite")
    t = ((jd_ut1_day - 2451545.0) + jd_ut1_frac) / 36525.0
    sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t * t * t
    deg = (sec % 86400.0) / 240.0
    deg %= 360.0
    return 0.0 if deg >= 360.0 else deg


def lst_deg(jd_ut1_day: float, jd_ut1_frac: float, east_longitude_deg: float) -> float:
    """Local mean sidereal time in degrees, [0, 360): GMST + east longitude."""
    v = (gmst82_deg(jd_ut1_day, jd_ut1_frac) + east_longitude_deg) % 360.0
    return 0.0 if v >= 360.0 else v
