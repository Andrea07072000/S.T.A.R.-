"""star_spline - natural cubic spline through tabulated points, correctly rounded (S.T.A.R., 2026-10-07).
Standard library only.

  second_derivatives(xs, ys)          the second derivative of the spline at every knot (the first and the last are 0)
  values(xs, ys, points)              the spline at each of `points`
  derivatives(xs, ys, points)         its first derivative at each of `points`
  integral(xs, ys, a, b)              the integral of the spline from a to b
The natural cubic spline is the smoothest curve through the points (it minimises the integral of the square of the
second derivative), a cubic between consecutive knots, with continuous first and second derivatives and zero second
derivative at the two ends. With two points it is the straight line through them.

Every float is an exact fraction: the tridiagonal system of the second derivatives is solved in rational arithmetic
and every result is evaluated exactly and rounded once. Each number returned is therefore the float nearest to the
true value of the spline of the data as given: nothing is lost to knots that are close together, to values far from
zero, or to the length of the table.
Refusals (ValueError): xs or ys that are not a list or tuple of 2 to 300 finite real numbers within +-1e100 (booleans
refused); different lengths; xs not strictly increasing; a point (or a limit of integration) outside [xs[0], xs[-1]]:
a spline is not extrapolated; a result too large for a float.
"""
from __future__ import annotations

import bisect
import numbers
from fractions import Fraction
from typing import List, Sequence, Tuple

__all__ = ["second_derivatives", "values", "derivatives", "integral"]
__version__ = "0.1.0"

BIG = 1e100
MAX_POINTS = 300


def _number(v, what: str) -> Fraction:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be finite real numbers within +-1e100")
    return Fraction(float(v))


def _table(xs, ys) -> Tuple[List[Fraction], List[Fraction], List[Fraction]]:
    for values_, what in ((xs, "xs"), (ys, "ys")):
        if not isinstance(values_, (list, tuple)) or not 2 <= len(values_) <= MAX_POINTS:
            raise ValueError(f"{what} must be a list or tuple of 2 to {MAX_POINTS} numbers")
    fx, fy = [_number(v, "xs") for v in xs], [_number(v, "ys") for v in ys]
    if len(fx) != len(fy):
        raise ValueError("xs and ys must have the same length")
    if any(b <= a for a, b in zip(fx, fx[1:])):
        raise ValueError("xs must be strictly increasing")
    return fx, fy, _solve(fx, fy)


def _solve(x: List[Fraction], y: List[Fraction]) -> List[Fraction]:
    """Second derivatives M_i of the natural spline: h_(i-1) M_(i-1) + 2 (h_(i-1) + h_i) M_i + h_i M_(i+1) = 6 (slope_i - slope_(i-1))."""
    n = len(x)
    m = [Fraction(0)] * n
    if n < 3:
        return m
    h = [x[i + 1] - x[i] for i in range(n - 1)]
    slope = [(y[i + 1] - y[i]) / h[i] for i in range(n - 1)]
    diagonal = [2 * (h[i - 1] + h[i]) for i in range(1, n - 1)]
    rhs = [6 * (slope[i] - slope[i - 1]) for i in range(1, n - 1)]
    for i in range(1, n - 2):                                # forward elimination; the matrix is diagonally dominant: no pivoting
        factor = h[i] / diagonal[i - 1]
        diagonal[i] -= factor * h[i]
        rhs[i] -= factor * rhs[i - 1]
    for i in range(n - 3, -1, -1):
        upper = h[i + 1] * m[i + 2] if i + 2 < n - 1 else Fraction(0)
        m[i + 1] = (rhs[i] - upper) / diagonal[i]
    return m


def _float(q: Fraction) -> float:
    try:
        return float(q)
    except OverflowError:
        raise ValueError("the result is too large for a float") from None


def _locate(x: List[Fraction], point, what: str) -> Tuple[int, Fraction]:
    p = _number(point, what)
    if not x[0] <= p <= x[-1]:
        raise ValueError(f"{what} must be inside the table, from {float(x[0])!r} to {float(x[-1])!r}: a spline is not extrapolated")
    return min(bisect.bisect_right(x, p) - 1, len(x) - 2), p


def _points(points) -> Sequence:
    if not isinstance(points, (list, tuple)):
        raise ValueError("points must be a list or tuple of numbers")
    return points


def second_derivatives(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, ...]:
    return tuple(_float(v) for v in _table(xs, ys)[2])


def _piece(x, y, m, i):
    """Coefficients (a, b, c, d) of a + b t + c t^2 + d t^3 with t = point - x_i on the interval i."""
    h = x[i + 1] - x[i]
    return y[i], (y[i + 1] - y[i]) / h - h * (2 * m[i] + m[i + 1]) / 6, m[i] / 2, (m[i + 1] - m[i]) / (6 * h)


def values(xs: Sequence[float], ys: Sequence[float], points: Sequence[float]) -> Tuple[float, ...]:
    x, y, m = _table(xs, ys)
    out = []
    for point in _points(points):
        i, p = _locate(x, point, "points")
        a, b, c, d = _piece(x, y, m, i)
        t = p - x[i]
        out.append(_float(a + t * (b + t * (c + t * d))))
    return tuple(out)


def derivatives(xs: Sequence[float], ys: Sequence[float], points: Sequence[float]) -> Tuple[float, ...]:
    x, y, m = _table(xs, ys)
    out = []
    for point in _points(points):
        i, p = _locate(x, point, "points")
        _, b, c, d = _piece(x, y, m, i)
        t = p - x[i]
        out.append(_float(b + t * (2 * c + 3 * t * d)))
    return tuple(out)


def _primitive(x, y, m, i, p) -> Fraction:
    a, b, c, d = _piece(x, y, m, i)
    t = p - x[i]
    return t * (a + t * (b / 2 + t * (c / 3 + t * d / 4)))


def integral(xs: Sequence[float], ys: Sequence[float], a: float, b: float) -> float:
    x, y, m = _table(xs, ys)
    (ia, pa), (ib, pb) = _locate(x, a, "a"), _locate(x, b, "b")
    if pb < pa:
        return -integral(xs, ys, b, a)
    total = _primitive(x, y, m, ib, pb) - _primitive(x, y, m, ia, pa)
    total += sum(_primitive(x, y, m, i, x[i + 1]) for i in range(ia, ib))
    return _float(total)
