"""star_quadrature - Gauss-Legendre quadrature and Legendre polynomials (S.T.A.R., 2026-10-06).
Standard library only.

  gauss_legendre(n)            nodes and weights of the n-point rule on [-1, 1]: (nodes, weights), nodes increasing
  integrate(f, a, b, n)        integral of f over [a, b] with the n-point rule (exact for polynomials up to degree 2n - 1)
  legendre(n, x)               P_n(x) and its first derivative, for -1 <= x <= 1: (p, dp)
The nodes are the roots of P_n. Its coefficients are built as exact fractions, each root is isolated between two
consecutive roots of P_(n-1) and located by bisection over the floats with the EXACT sign of the polynomial, so
every node is the float nearest to the true root. Each weight 2 / ((1 - x^2) P_n'(x)^2) is evaluated in exact
arithmetic at the root refined by one exact Newton step, then rounded once. No tolerance and no starting guess.
Refusals (ValueError): n that is not an integer from 1 to 32 (0 to 32 for `legendre`; booleans refused); x outside
[-1, 1]; a or b that is not a finite real number within +-1e150; f that is not callable or returns something that
is not a finite real number; a result that overflows.
"""
from __future__ import annotations

import math
import numbers
import struct
from fractions import Fraction
from functools import lru_cache
from typing import Callable, Tuple

__all__ = ["gauss_legendre", "integrate", "legendre"]
__version__ = "0.1.0"

MAX_POINTS = 32
BIG = 1e150


def _order(n, lowest: int) -> int:
    if isinstance(n, bool) or not isinstance(n, numbers.Integral) or not lowest <= n <= MAX_POINTS:
        raise ValueError(f"n must be an integer from {lowest} to {MAX_POINTS}")
    return int(n)


def _real(v, what: str, limit: float) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -limit <= float(v) <= limit     # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-{limit:g}")
    return float(v)


@lru_cache(maxsize=None)
def _coefficients(n: int) -> Tuple[Fraction, ...]:
    """Coefficients of P_n, highest power first, exact: (k + 1) P_(k+1) = (2k + 1) x P_k - k P_(k-1)."""
    before, current = (Fraction(1),), (Fraction(1), Fraction(0))
    if n == 0:
        return before
    for k in range(1, n):
        shifted = current + (Fraction(0),)
        padded = (Fraction(0), Fraction(0)) + before
        before, current = current, tuple(((2 * k + 1) * s - k * p) / (k + 1) for s, p in zip(shifted, padded))
    return current


def _value(coeffs: Tuple[Fraction, ...], x: Fraction) -> Tuple[Fraction, Fraction]:
    """The polynomial and its derivative at x, exactly."""
    p = dp = Fraction(0)
    for c in coeffs:
        dp = dp * x + p
        p = p * x + c
    return p, dp


def _bits(x: float) -> int:
    """Position of a non-negative float among the floats, in increasing order."""
    return struct.unpack("<q", struct.pack("<d", x))[0]


def _float(n: int) -> float:
    return struct.unpack("<d", struct.pack("<q", n))[0]


@lru_cache(maxsize=None)
def _integers(n: int) -> Tuple[int, ...]:
    """P_n times the (positive) common denominator of its coefficients: integers with the same signs and roots."""
    coeffs = _coefficients(n)
    scale = math.lcm(*(c.denominator for c in coeffs))
    return tuple(int(c * scale) for c in coeffs)


def _sign(ints: Tuple[int, ...], x: Fraction) -> int:
    """Sign of the integer polynomial at the fraction x, exactly, without any division."""
    p, power = 0, 1
    for c in ints:
        p = p * x.numerator + c * power
        power *= x.denominator
    return (p > 0) - (p < 0)


def _root(coeffs: Tuple[int, ...], lo: float, hi: float) -> float:
    """The float nearest to the single root in (lo, hi), 0 <= lo < hi: bisection over the floats with exact signs."""
    below = _sign(coeffs, Fraction(lo))
    a, b = _bits(lo), _bits(hi)
    while b - a > 1:
        mid = (a + b) // 2
        s = _sign(coeffs, Fraction(_float(mid)))
        if s == 0:
            return _float(mid)
        if s == below:
            a = mid
        else:
            b = mid
    lo, hi = _float(a), _float(b)
    return hi if _sign(coeffs, (Fraction(lo) + Fraction(hi)) / 2) == below else lo


@lru_cache(maxsize=None)
def _positive_roots(n: int) -> Tuple[float, ...]:
    """The roots of P_n in (0, 1), increasing: one between each pair of consecutive non-negative roots of P_(n-1), and 1."""
    if n < 2:
        return ()
    cuts = ((0.0,) if n % 2 == 0 else ()) + _positive_roots(n - 1) + (1.0,)
    coeffs = _integers(n)
    return tuple(_root(coeffs, cuts[k], cuts[k + 1]) for k in range(len(cuts) - 1))


@lru_cache(maxsize=None)
def _rule(n: int) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    coeffs = _coefficients(n)
    half = _positive_roots(n)
    weights = []
    for node in ((0.0,) if n % 2 else ()) + half:
        x = Fraction(node)
        p, dp = _value(coeffs, x)
        x -= p / dp                                         # one exact Newton step: the root to about 1e-32
        dp = _value(coeffs, x)[1]
        weights.append(float(2 / ((1 - x * x) * dp * dp)))
    if n % 2:
        return tuple(-r for r in reversed(half)) + (0.0,) + half, tuple(reversed(weights[1:])) + tuple(weights)
    return tuple(-r for r in reversed(half)) + half, tuple(reversed(weights)) + tuple(weights)


def gauss_legendre(n: int) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    return _rule(_order(n, 1))


def integrate(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    if not callable(f):
        raise ValueError("f must be callable")
    lo, hi = _real(a, "a", BIG), _real(b, "b", BIG)
    nodes, weights = _rule(_order(n, 1))
    mid, half = 0.5 * lo + 0.5 * hi, 0.5 * hi - 0.5 * lo
    terms = []
    for x, w in zip(nodes, weights):
        y = f(mid + half * x)
        if isinstance(y, bool) or not isinstance(y, numbers.Real) or not math.isfinite(y):
            raise ValueError("f must return a finite real number")
        terms.append(w * float(y))
    total = half * math.fsum(terms)
    if not math.isfinite(total):
        raise ValueError("the result overflows a float")
    return total


def legendre(n: int, x: float) -> Tuple[float, float]:
    order = _order(n, 0)
    at = _real(x, "x", 1.0)
    before, current = 1.0, at                               # P_0, P_1
    dbefore, dcurrent = 0.0, 1.0                            # their derivatives
    if order == 0:
        return before, dbefore
    for k in range(1, order):
        following = ((2 * k + 1) * at * current - k * before) / (k + 1)
        dbefore, dcurrent = dcurrent, dbefore + (2 * k + 1) * current          # P'_(k+1) = P'_(k-1) + (2k + 1) P_k: no division by 1 - x^2
        before, current = current, following
    return current + 0.0, dcurrent + 0.0                    # an odd order at 0 is 0.0, never -0.0
