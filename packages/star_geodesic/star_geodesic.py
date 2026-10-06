"""star_geodesic - distance and azimuths along the WGS-84 ellipsoid (S.T.A.R., 2026-10-06). Standard library only.

  inverse(lat1, lon1, lat2, lon2) -> (distance_m, azimuth1_deg, azimuth2_deg): length of the geodesic between two
      points and its azimuth at each end, both in the direction of travel from point 1 to point 2.
  direct(lat1, lon1, azimuth1_deg, distance_m) -> (lat2, lon2, azimuth2_deg): the point reached and the azimuth there.
Units: degrees, metres. Azimuths from North towards East in [0, 360); longitude returned in [-180, 180).
Method: Vincenty (1975) iteration on the auxiliary sphere, to 1e-12 rad plus two further contractions. It is known not to converge for nearly
antipodal points: in that case inverse() raises RuntimeError after a bounded number of iterations - it never returns
an unconverged value. Coincident points give distance 0 and azimuths 0.0 (direction undefined).
Refusals (ValueError): non-numeric, boolean or non-finite input, latitude outside [-90, 90], longitude or azimuth
outside [-360, 360], distance negative or longer than 20 000 km.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["inverse", "direct"]
__version__ = "0.1.0"
A = 6378137.0
F = 1 / 298.257223563
B = A * (1 - F)
MAX_ITER = 200
MAX_DISTANCE_M = 2.0e7
TOL = 1e-12
POLISH = 2          # iterations run after the tolerance is met (each one contracts the error by about 1/f = 300)


def _num(*values) -> None:
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e300 < float(v) < 1e300    # NaN fails both
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError("inputs must be finite real numbers")


def _point(lat: float, lon: float) -> None:
    _num(lat, lon)
    if not -90.0 <= lat <= 90.0:
        raise ValueError("latitude must be within [-90, 90] deg")
    if not -360.0 <= lon <= 360.0:
        raise ValueError("longitude must be within [-360, 360] deg")


def _az(rad: float) -> float:
    d = math.degrees(rad) % 360.0
    return 0.0 if d >= 360.0 else d


def _series(cos_sq_alpha: float) -> Tuple[float, float]:
    u2 = cos_sq_alpha * (A * A - B * B) / (B * B)
    big_a = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    big_b = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    return big_a, big_b


def _delta_sigma(big_b: float, sin_s: float, cos_s: float, cos_2sm: float) -> float:
    return big_b * sin_s * (cos_2sm + big_b / 4 * (cos_s * (-1 + 2 * cos_2sm * cos_2sm)
                                                  - big_b / 6 * cos_2sm * (-3 + 4 * sin_s * sin_s) * (-3 + 4 * cos_2sm * cos_2sm)))


def inverse(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float, float]:
    _point(lat1, lon1)
    _point(lat2, lon2)
    u1 = math.atan((1 - F) * math.tan(math.radians(lat1)))
    u2 = math.atan((1 - F) * math.tan(math.radians(lat2)))
    big_l = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    su1, cu1, su2, cu2 = math.sin(u1), math.cos(u1), math.sin(u2), math.cos(u2)
    lam = big_l
    polish = POLISH
    for _ in range(MAX_ITER):
        sl, cl = math.sin(lam), math.cos(lam)
        sin_s = math.hypot(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
        cos_s = su1 * su2 + cu1 * cu2 * cl
        if sin_s < 1e-15:                                  # 1e-15 rad on the auxiliary sphere is 6 nanometres
            if cos_s > 0.0:
                return 0.0, 0.0, 0.0                       # coincident points (also the same pole at two longitudes)
            raise RuntimeError("antipodal points: the geodesic is not unique")
        sigma = math.atan2(sin_s, cos_s)
        sin_a = cu1 * cu2 * sl / sin_s
        cos_sq_a = 1 - sin_a * sin_a
        cos_2sm = cos_s - 2 * su1 * su2 / cos_sq_a if cos_sq_a > 1e-300 else 0.0     # equatorial line
        c = F / 16 * cos_sq_a * (4 + F * (4 - 3 * cos_sq_a))
        new = big_l + (1 - c) * F * sin_a * (sigma + c * sin_s * (cos_2sm + c * cos_s * (-1 + 2 * cos_2sm * cos_2sm)))
        if abs(new) > math.pi:
            raise RuntimeError("nearly antipodal points: Vincenty's iteration does not converge")
        if abs(new - lam) < TOL and polish:
            polish -= 1                                    # 1e-12 rad is 6 micrometres on the ground: contract further
        elif abs(new - lam) < TOL:
            big_a, big_b = _series(cos_sq_a)
            s = B * big_a * (sigma - _delta_sigma(big_b, sin_s, cos_s, cos_2sm))
            az1 = math.atan2(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
            az2 = math.atan2(cu1 * sl, -su1 * cu2 + cu1 * su2 * cl)
            return s, _az(az1), _az(az2)
        lam = new
    raise RuntimeError("nearly antipodal points: Vincenty's iteration does not converge")


def direct(lat1: float, lon1: float, azimuth1_deg: float, distance_m: float) -> Tuple[float, float, float]:
    _point(lat1, lon1)
    _num(azimuth1_deg, distance_m)
    if not -360.0 <= azimuth1_deg <= 360.0:
        raise ValueError("azimuth must be within [-360, 360] deg")
    if not 0.0 <= distance_m <= MAX_DISTANCE_M:
        raise ValueError("distance must be within [0, 20 000 km]")
    a1 = math.radians(azimuth1_deg)
    sa1, ca1 = math.sin(a1), math.cos(a1)
    u1 = math.atan((1 - F) * math.tan(math.radians(lat1)))
    su1, cu1 = math.sin(u1), math.cos(u1)
    sigma1 = math.atan2(su1, cu1 * ca1)
    sin_a = cu1 * sa1
    cos_sq_a = 1 - sin_a * sin_a
    big_a, big_b = _series(cos_sq_a)
    first = distance_m / (B * big_a)
    sigma = first
    polish = POLISH
    for _ in range(MAX_ITER):
        cos_2sm = math.cos(2 * sigma1 + sigma)
        sin_s, cos_s = math.sin(sigma), math.cos(sigma)
        new = first + _delta_sigma(big_b, sin_s, cos_s, cos_2sm)
        if abs(new - sigma) < TOL:
            if not polish:
                sigma = new
                break
            polish -= 1
        sigma = new
    else:
        raise RuntimeError("direct geodesic iteration did not converge")
    cos_2sm = math.cos(2 * sigma1 + sigma)
    sin_s, cos_s = math.sin(sigma), math.cos(sigma)
    x = su1 * sin_s - cu1 * cos_s * ca1
    lat2 = math.atan2(su1 * cos_s + cu1 * sin_s * ca1, (1 - F) * math.hypot(sin_a, x))
    lam = math.atan2(sin_s * sa1, cu1 * cos_s - su1 * sin_s * ca1)
    c = F / 16 * cos_sq_a * (4 + F * (4 - 3 * cos_sq_a))
    big_l = lam - (1 - c) * F * sin_a * (sigma + c * sin_s * (cos_2sm + c * cos_s * (-1 + 2 * cos_2sm * cos_2sm)))
    lon2 = (lon1 + math.degrees(big_l) + 180.0) % 360.0 - 180.0
    return math.degrees(lat2), lon2, _az(math.atan2(sin_a, -x))
