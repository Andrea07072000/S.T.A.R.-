"""star_vec3 - the operations on three-dimensional vectors that orbit and attitude code repeats (S.T.A.R., 2026-10-06).
Standard library only.

  dot(a, b), cross(a, b), norm(a), distance(a, b), triple(a, b, c)
  unit(a)                      a / |a|
  angle_deg(a, b)              angle between two directions, [0, 180], accurate for nearly parallel and nearly opposite vectors
  project(a, b), reject(a, b)  the part of a along b and the part of a perpendicular to b (they add up to a)
Vectors are lists or tuples of three finite real numbers; results are tuples of floats (or a float).
The length is computed without intermediate overflow or underflow (hypot), the dot and triple products with a
compensated sum (fsum), and the angle as atan2(|a x b|, a . b): the arc-cosine of the normalised dot product loses half
of its digits near 0 and 180 degrees.
Refusals (ValueError): a vector that is not a list or tuple of exactly three finite real numbers (booleans
included) no larger than 1e100 in absolute value; the zero vector where a direction is needed (unit, angle_deg, and
the second argument of project and reject).
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["dot", "cross", "norm", "distance", "triple", "unit", "angle_deg", "project", "reject"]
__version__ = "0.1.0"

BIG = 1e100                             # so that a triple product (1e300) cannot overflow
Vec = Tuple[float, float, float]


def _vec(v, what: str = "a vector") -> Vec:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"{what} must be a list or tuple of three numbers")
    out = []
    for c in v:
        try:
            ok = not isinstance(c, bool) and isinstance(c, numbers.Real) and -BIG <= float(c) <= BIG      # NaN fails the comparison
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"{what} must hold finite real numbers within +-1e100")
        out.append(float(c))
    return out[0], out[1], out[2]


def _direction(v, what: str) -> Vec:
    a = _vec(v, what)
    if a == (0.0, 0.0, 0.0):
        raise ValueError(f"{what} is the zero vector: it has no direction")
    return a


def _cross(a: Vec, b: Vec) -> Vec:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def _dot(a: Vec, b: Vec) -> float:
    return math.fsum((a[0] * b[0], a[1] * b[1], a[2] * b[2]))


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return _dot(_vec(a), _vec(b))


def cross(a: Sequence[float], b: Sequence[float]) -> Vec:
    return _cross(_vec(a), _vec(b))


def norm(a: Sequence[float]) -> float:
    return math.hypot(*_vec(a))


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    a, b = _vec(a), _vec(b)
    return math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])


def triple(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    return _dot(_vec(a), _cross(_vec(b), _vec(c)))


def unit(a: Sequence[float]) -> Vec:
    a = _direction(a, "the vector")
    m = max(abs(a[0]), abs(a[1]), abs(a[2]))                # scale first: the components may be 1e-300 or 1e100
    s = (a[0] / m, a[1] / m, a[2] / m)
    n = math.hypot(*s)
    return s[0] / n, s[1] / n, s[2] / n


def angle_deg(a: Sequence[float], b: Sequence[float]) -> float:
    ua, ub = unit(a), unit(b)
    return math.degrees(math.atan2(math.hypot(*_cross(ua, ub)), _dot(ua, ub)))


def project(a: Sequence[float], b: Sequence[float]) -> Vec:
    a, ub = _vec(a), unit(_direction(b, "the vector projected onto"))
    k = _dot(a, ub)
    return k * ub[0], k * ub[1], k * ub[2]


def reject(a: Sequence[float], b: Sequence[float]) -> Vec:
    a = _vec(a)
    p = project(a, b)
    return a[0] - p[0], a[1] - p[1], a[2] - p[2]
