"""star_iod - velocity from three position vectors: Gibbs and Herrick-Gibbs (S.T.A.R., 2026-10-06).
Standard library only.

  gibbs(r1, r2, r3, mu=398600.4418, coplanar_tol_deg=3.0) -> v2: velocity at the middle position from three positions
      of the same two-body orbit, taken in time order. Pure geometry: no times needed. Loses accuracy when the
      positions are less than about one degree apart (use herrick_gibbs there).
  herrick_gibbs(r1, r2, r3, t1, t2, t3, mu=398600.4418, coplanar_tol_deg=3.0) -> v2: Taylor-series form for closely
      spaced positions with their times (seconds); loses accuracy when the positions are more than a few degrees apart.
  separation_deg(r1, r2, r3) -> (angle r1-r2, angle r2-r3): to choose between the two.
Units: km, km/s, s (any consistent set if mu is given in it). Algorithms 54 and 55 of Vallado.
Refusals (ValueError): wrong shapes, non-numeric, boolean or non-finite input, a zero position, mu <= 0, positions
further from a common plane than coplanar_tol_deg, positions that are collinear or through which no attracting
orbit passes (Gibbs), times that are not strictly increasing (Herrick-Gibbs). Gibbs takes the direction of motion
from the order r1, r2, r3: the same three positions in reverse order give the opposite velocity.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["gibbs", "herrick_gibbs", "separation_deg"]
__version__ = "0.1.0"
MU_EARTH = 398600.4418
Vec = Tuple[float, float, float]


def _num(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e100 < float(v) < 1e100      # NaN fails both
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number (magnitude below 1e100)")
    return float(v)


def _vec(v, what: str) -> Vec:
    try:
        ok = not isinstance(v, (str, bytes, dict, set, frozenset)) and len(v) == 3
        items = (v[0], v[1], v[2]) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a sequence of three numbers")
    out = tuple(_num(x, what) for x in items)
    if math.hypot(*out) == 0.0:
        raise ValueError(f"{what} is the zero vector")
    return out


def _cross(a: Vec, b: Vec) -> Vec:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _angle_deg(a: Vec, b: Vec) -> float:
    return math.degrees(math.atan2(math.hypot(*_cross(a, b)), _dot(a, b)))


def _inputs(r1, r2, r3, mu, tol):
    r1, r2, r3 = _vec(r1, "r1"), _vec(r2, "r2"), _vec(r3, "r3")
    mu, tol = _num(mu, "mu"), _num(tol, "coplanar_tol_deg")
    if mu <= 0.0:
        raise ValueError("mu must be positive")
    if not 0.0 < tol <= 90.0:
        raise ValueError("coplanar_tol_deg must be within (0, 90]")
    z23 = _cross(r2, r3)
    n23 = math.hypot(*z23)
    if n23 > 0.0:
        off_plane = abs(90.0 - _angle_deg(z23, r1))
        if off_plane > tol:
            raise ValueError(f"the three positions are not coplanar: r1 is {off_plane:.3f} deg off the plane of r2 and r3")
    return r1, r2, r3, mu


def separation_deg(r1: Sequence[float], r2: Sequence[float], r3: Sequence[float]) -> Tuple[float, float]:
    r1, r2, r3 = _vec(r1, "r1"), _vec(r2, "r2"), _vec(r3, "r3")
    return _angle_deg(r1, r2), _angle_deg(r2, r3)


def gibbs(r1: Sequence[float], r2: Sequence[float], r3: Sequence[float], mu: float = MU_EARTH, coplanar_tol_deg: float = 3.0) -> Vec:
    r1, r2, r3, mu = _inputs(r1, r2, r3, mu, coplanar_tol_deg)
    m1, m2, m3 = math.hypot(*r1), math.hypot(*r2), math.hypot(*r3)
    # Written with differences of neighbouring vectors: the textbook sums (Z12 + Z23 + Z31, ...) cancel to rounding
    # noise when the positions are close (measured: 1.5e-5 relative at 0.02 deg spacing before this form).
    d12 = tuple(r1[i] - r2[i] for i in range(3))
    d32 = tuple(r3[i] - r2[i] for i in range(3))
    z12, z23 = _cross(r1, r2), _cross(r2, r3)
    d = _cross(d32, d12)                                             # = Z12 + Z23 + Z31
    dm1 = _dot(d12, tuple(r1[i] + r2[i] for i in range(3))) / (m1 + m2)     # m1 - m2
    dm3 = _dot(d32, tuple(r3[i] + r2[i] for i in range(3))) / (m3 + m2)     # m3 - m2
    n = tuple(m2 * d[i] + dm1 * z23[i] + dm3 * z12[i] for i in range(3))    # = m1 Z23 + m2 Z31 + m3 Z12
    s = tuple(dm1 * d32[i] - dm3 * d12[i] for i in range(3))             # = (m2-m3) r1 + (m3-m1) r2 + (m1-m2) r3
    nn, dd = math.hypot(*n), math.hypot(*d)
    chord = math.hypot(*d12) * math.hypot(*d32)                      # |D| = chord * sin(bend angle of the three points)
    if chord == 0.0 or dd <= 1e-10 * chord or nn <= 1e-10 * chord * m2:
        raise ValueError("the positions are collinear or coincide: no orbit plane")
    if _dot(n, d) <= 0.0:
        raise ValueError("no orbit about the centre passes through the positions (the path would curve away from it)")
    b = _cross(d, r2)
    lg = math.sqrt(mu / (nn * dd))
    v = tuple(lg / m2 * b[i] + lg * s[i] for i in range(3))
    if not all(map(math.isfinite, v)):
        raise ValueError("result out of range")
    return v


def herrick_gibbs(r1: Sequence[float], r2: Sequence[float], r3: Sequence[float], t1: float, t2: float, t3: float,
                  mu: float = MU_EARTH, coplanar_tol_deg: float = 3.0) -> Vec:
    r1, r2, r3, mu = _inputs(r1, r2, r3, mu, coplanar_tol_deg)
    t1, t2, t3 = _num(t1, "t1"), _num(t2, "t2"), _num(t3, "t3")
    dt21, dt32, dt31 = t2 - t1, t3 - t2, t3 - t1
    if dt21 <= 0.0 or dt32 <= 0.0:
        raise ValueError("times must be strictly increasing: t1 < t2 < t3")
    m1, m2, m3 = math.hypot(*r1), math.hypot(*r2), math.hypot(*r3)
    c1 = -dt32 * (1.0 / (dt21 * dt31) + mu / (12.0 * m1 ** 3))
    c2 = (dt32 - dt21) * (1.0 / (dt21 * dt32) + mu / (12.0 * m2 ** 3))
    c3 = dt21 * (1.0 / (dt32 * dt31) + mu / (12.0 * m3 ** 3))
    v = tuple(c1 * r1[i] + c2 * r2[i] + c3 * r3[i] for i in range(3))
    if not all(map(math.isfinite, v)):
        raise ValueError("result out of range")
    return v
