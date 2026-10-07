"""star_linefit - least-squares straight line and correlation, correctly rounded (S.T.A.R., 2026-10-07).
Standard library only.

  fit(xs, ys)             slope and intercept of the least-squares line y = slope * x + intercept: (slope, intercept)
  fit_errors(xs, ys)      (standard error of the slope, standard error of the intercept, residual standard deviation),
                          with n - 2 degrees of freedom: needs at least 3 points
  correlation(xs, ys)     Pearson correlation coefficient r, in [-1, 1]
Every float is an exact fraction: the sums are formed exactly in rational arithmetic and each result is rounded once,
square roots included (an integer square root decides the last bit). Points far from the origin (x = 1e9 + k) lose
nothing, the order of the points does not matter, and r is exactly 1.0 or -1.0 only when the points are exactly on a
line.
Refusals (ValueError): xs or ys that are not a list or tuple of 2 to 100000 finite real numbers within +-1e100
(booleans refused); different lengths; all x equal (no line of finite slope; for `correlation`, also all y equal);
fewer than 3 points for `fit_errors`; a result too large for a float.
"""
from __future__ import annotations

import math
import numbers
from fractions import Fraction
from typing import Sequence, Tuple

__all__ = ["fit", "fit_errors", "correlation"]
__version__ = "0.1.0"

BIG = 1e100
MAX_POINTS = 100000


def _column(values, what: str) -> Tuple[Fraction, ...]:
    if not isinstance(values, (list, tuple)) or not 2 <= len(values) <= MAX_POINTS:
        raise ValueError(f"{what} must be a list or tuple of 2 to 100000 numbers")
    out = []
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"{what} must be finite real numbers within +-1e100")
        out.append(Fraction(float(v)))
    return tuple(out)


def _sums(xs, ys):
    """n, mean of x, mean of y, and the centred sums Sxx, Sxy, Syy, all exact."""
    fx, fy = _column(xs, "xs"), _column(ys, "ys")
    n = len(fx)
    if len(fy) != n:
        raise ValueError("xs and ys must have the same length")
    mx, my = sum(fx) / n, sum(fy) / n
    sxx = sum((x - mx) ** 2 for x in fx)
    if sxx == 0:
        raise ValueError("all the x are equal: no line of finite slope")
    return n, mx, my, sxx, sum((x - mx) * (y - my) for x, y in zip(fx, fy)), sum((y - my) ** 2 for y in fy)


def _float(q: Fraction) -> float:
    try:
        return float(q)
    except OverflowError:
        raise ValueError("the result is too large for a float") from None


def _sqrt(q: Fraction) -> float:
    """The float nearest to the square root of the non-negative fraction q."""
    if q == 0:
        return 0.0
    shift = max(0, 128 - (q.numerator.bit_length() - q.denominator.bit_length()) // 2)     # the integer root gets at least 127 bits
    root = math.isqrt((q.numerator << (2 * shift)) // q.denominator)                       # floor(sqrt(q) * 2^shift)
    a, b = _float(Fraction(root, 1 << shift)), _float(Fraction(root + 1, 1 << shift))      # a <= sqrt(q) < the fraction behind b
    if a == b:
        return a
    middle = (Fraction(a) + Fraction(b)) / 2               # a rounding boundary lies between: decide exactly
    return b if middle * middle < q else a


def fit(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float]:
    _, mx, my, sxx, sxy, _ = _sums(xs, ys)
    slope = sxy / sxx
    return _float(slope), _float(my - slope * mx)


def fit_errors(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float, float]:
    n, mx, _, sxx, sxy, syy = _sums(xs, ys)
    if n < 3:
        raise ValueError("the errors of a fit need at least 3 points")
    variance = (syy - sxy * sxy / sxx) / (n - 2)             # residual sum of squares over the degrees of freedom: exact, never negative
    return _sqrt(variance / sxx), _sqrt(variance * (Fraction(1, n) + mx * mx / sxx)), _sqrt(variance)


def correlation(xs: Sequence[float], ys: Sequence[float]) -> float:
    _, _, _, sxx, sxy, syy = _sums(xs, ys)
    if syy == 0:
        raise ValueError("all the y are equal: the correlation is not defined")
    r = _sqrt(sxy * sxy / (sxx * syy))
    return -r if sxy < 0 else r
