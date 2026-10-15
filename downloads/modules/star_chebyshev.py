"""star_chebyshev - evaluation of Chebyshev series with their derivative (S.T.A.R., 2026-10-07).
Standard library only.

  evaluate(coefficients, x)                 sum of c_k T_k(x) for -1 <= x <= 1, and its derivative: (p, dp)
  evaluate_on(coefficients, t, mid, radius) the same series on the interval [mid - radius, mid + radius], at the point
                                            t: (p, dp) with dp the derivative with respect to t
Chebyshev series are how planetary and spacecraft ephemerides are stored (one set of coefficients per time interval,
described by its midpoint and radius): `evaluate_on` follows that convention, x = (t - mid) / radius and
dp/dt = (dp/dx) / radius. The value and the derivative are computed together by Clenshaw's recurrence, which never
forms the polynomials T_k themselves.
Refusals (ValueError): coefficients that are not a list or tuple of 1 to 200 finite real numbers within +-1e100
(booleans refused); x outside [-1, 1]; t outside the interval (a t that falls outside by rounding alone, at most two
units in the last place of the largest of |t|, |mid| and radius, is taken as the end); mid not finite or beyond 1e100; radius
not within [1e-100, 1e100]. Within these limits no result can overflow.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["evaluate", "evaluate_on"]
__version__ = "0.1.0"

MAX_TERMS = 200
BIG = 1e100
TINY = 1e-100


def _real(v, what: str, limit: float) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -limit <= float(v) <= limit      # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-{limit:g}")
    return float(v)


def _series(coefficients) -> Tuple[float, ...]:
    if not isinstance(coefficients, (list, tuple)) or not 1 <= len(coefficients) <= MAX_TERMS:
        raise ValueError("coefficients must be a list or tuple of 1 to 200 numbers, c_0 first")
    return tuple(_real(c, "a coefficient", BIG) for c in coefficients)


def _clenshaw(cs: Sequence[float], x: float) -> Tuple[float, float]:
    w0 = w1 = d0 = d1 = 0.0
    for c in reversed(cs[1:]):
        w0, w1, previous = c + 2.0 * x * w0 - w1, w0, w0
        d0, d1 = 2.0 * previous + 2.0 * x * d0 - d1, d0
    return cs[0] + x * w0 - w1 + 0.0, w0 + x * d0 - d1 + 0.0          # within the limits nothing can overflow: |p| <= 200 * 1e100


def evaluate(coefficients: Sequence[float], x: float) -> Tuple[float, float]:
    return _clenshaw(_series(coefficients), _real(x, "x", 1.0))


def evaluate_on(coefficients: Sequence[float], t: float, mid: float, radius: float) -> Tuple[float, float]:
    cs = _series(coefficients)
    at, centre = _real(t, "t", 2.0 * BIG), _real(mid, "mid", BIG)
    half = _real(radius, "radius", BIG)
    if half < TINY:
        raise ValueError("radius must be within [1e-100, 1e100]")
    if abs(at - centre) - half > 2.0 * math.ulp(max(abs(at), abs(centre), half)):
        raise ValueError("t must lie within [mid - radius, mid + radius]")
    p, dp = _clenshaw(cs, max(-1.0, min(1.0, (at - centre) / half)))
    return p, dp / half
