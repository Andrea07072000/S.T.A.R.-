# -*- coding: utf-8 -*-
"""star_geodesy — WGS-84 geodetic <-> ECEF (S.T.A.R., 2026-10-03). Standard library only.
Units: degrees, metres. Ellipsoid: WGS-84 (a = 6378137 m, 1/f = 298.257223563, NIMA TR8350.2).
ECEF -> geodetic: fixed-point iteration on latitude (Vallado Algorithm 12 form) to 1e-14 rad; never returns an
unconverged value (RuntimeError).
"""
from __future__ import annotations

import math
from typing import Tuple

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
B = A * (1 - F)


def geodetic_to_ecef(lat_deg: float, lon_deg: float, h_m: float) -> Tuple[float, float, float]:
    if not -90.0 <= lat_deg <= 90.0:
        raise ValueError("latitude must be within [-90, 90] deg")
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    n = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
    return ((n + h_m) * math.cos(lat) * math.cos(lon), (n + h_m) * math.cos(lat) * math.sin(lon),
            (n * (1 - E2) + h_m) * math.sin(lat))


def ecef_to_geodetic(x: float, y: float, z: float, max_iter: int = 50) -> Tuple[float, float, float]:
    p = math.hypot(x, y)
    if p == 0.0 and z == 0.0:
        raise ValueError("Earth's centre has no geodetic coordinates")
    lon = math.atan2(y, x)
    if p == 0.0:  # on the polar axis
        return (90.0 if z > 0 else -90.0), 0.0, abs(z) - B
    lat = math.atan2(z, p * (1 - E2))
    for _ in range(max_iter):
        n = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - n
        new = math.atan2(z, p * (1 - E2 * n / (n + h)))
        if abs(new - lat) < 1e-14:
            lat = new
            n = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
            h = p / math.cos(lat) - n if abs(lat) < math.radians(89.9) else abs(z) / math.sin(abs(lat)) - n * (1 - E2)
            return math.degrees(lat), math.degrees(lon), h
        lat = new
    raise RuntimeError("geodetic latitude iteration did not converge")
