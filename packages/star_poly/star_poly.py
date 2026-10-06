"""star_poly - real roots of quadratics and cubics, and polynomial evaluation (S.T.A.R., 2026-10-06).
Standard library only.

  quadratic_roots(a, b, c)     the distinct real roots of a x^2 + b x + c, sorted: (), (r,) or (r1, r2)
  cubic_roots(a, b, c, d)      the distinct real roots of a x^3 + b x^2 + c x + d, sorted: one, two or three
  evaluate(coefficients, x)    value of c0 x^n + c1 x^(n-1) + ... + cn (Horner), with its first derivative: (p, dp)
How many real roots there are is decided EXACTLY: the discriminant is computed in rational arithmetic (a float is an
exact fraction), so a double root is reported as one root and never as two close ones or as none. Each root is then
located inside an interval that contains no other root (between the turning points and Cauchy's bound) by bisection
over the floats, driven by the EXACT sign of the polynomial: at most 64 steps, no starting guess, no formula that
can cancel. A small root next to a large one keeps its digits, and no root can be lost to its neighbour.
Refusals (ValueError): a leading coefficient equal to zero (the polynomial is not of that degree); any coefficient or
x that is not a finite real number (booleans included) or exceeds 1e60 in absolute value; for `evaluate`, coefficients
that are not a list or tuple of 1 to 30 numbers; a result that overflows.
"""
from __future__ import annotations

import math
import numbers
import struct
from fractions import Fraction
from typing import Sequence, Tuple

__all__ = ["quadratic_roots", "cubic_roots", "evaluate"]
__version__ = "0.1.0"

BIG = 1e60
MAX_COEFFICIENTS = 30


def _num(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-1e60")
    return float(v)


def _leading(v, what: str) -> float:
    a = _num(v, what)
    if a == 0.0:
        raise ValueError(f"{what} must not be zero")
    return a


def _float(q: Fraction) -> float:
    try:
        return float(q)
    except OverflowError:
        raise ValueError("a root overflows a float") from None


def _sign(coeffs: Sequence[Fraction], x) -> int:
    """Sign of the polynomial at x (a float or a fraction), exactly."""
    fx = Fraction(x)
    p = Fraction(0)
    for c in coeffs:
        p = p * fx + c
    return (p > 0) - (p < 0)


def _rank(x: float) -> int:
    """Position of a float among all floats, in increasing order (-0.0 and 0.0 share a position)."""
    n = struct.unpack("<q", struct.pack("<d", x))[0]
    return n if n >= 0 else -(n & 0x7FFFFFFFFFFFFFFF)


def _unrank(n: int) -> float:
    return struct.unpack("<d", struct.pack("<q", n))[0] if n >= 0 else -struct.unpack("<d", struct.pack("<q", -n))[0]


def _between(coeffs: Sequence[Fraction], lo: float, hi: float) -> float:
    """The root in [lo, hi], where the polynomial changes sign: bisection over the floats with exact signs."""
    slo = _sign(coeffs, lo)
    if slo == 0:
        return lo
    if _sign(coeffs, hi) == 0:
        return hi
    a, b = _rank(lo), _rank(hi)
    while b - a > 1:
        mid = (a + b) // 2
        s = _sign(coeffs, _unrank(mid))
        if s == 0:
            return _unrank(mid)
        if s == slo:
            a = mid
        else:
            b = mid
    lo, hi = _unrank(a), _unrank(b)                         # two neighbouring floats enclose the root: the nearer one is returned
    return hi if _sign(coeffs, (Fraction(lo) + Fraction(hi)) / 2) == slo else lo


def _separated(coeffs: Sequence[Fraction], cuts: Sequence[float]) -> Tuple[float, ...]:
    """One root in each interval between consecutive cuts; the outermost limits are twice Cauchy's bound."""
    bound = 2.0 * _float(1 + max(abs(c) for c in coeffs[1:]) / abs(coeffs[0]))
    edges = [-bound] + list(cuts) + [bound]
    roots = []
    for k in range(len(edges) - 1):
        lo, hi = edges[k], edges[k + 1]
        if _sign(coeffs, lo) * _sign(coeffs, hi) > 0:
            # a float cut fell on the wrong side of a root that is within rounding of it: the root is that cut, to one float
            roots.append(lo if k else hi)
        else:
            roots.append(_between(coeffs, lo, hi))
    roots.sort()
    for k in range(1, len(roots)):                          # distinct by the exact discriminant: two roots within one float are its two ends
        if roots[k] <= roots[k - 1]:
            roots[k] = math.nextafter(roots[k - 1], math.inf)
    return tuple(r + 0.0 for r in roots)


def _quadratic(fa: Fraction, fb: Fraction, fc: Fraction) -> Tuple[float, ...]:
    disc = fb * fb - 4 * fa * fc                            # exact
    if disc < 0:
        return ()
    vertex = _float(-fb / (2 * fa))
    if disc == 0:
        return (vertex + 0.0,)
    return _separated((fa, fb, fc), [vertex])               # the vertex separates the two roots


def quadratic_roots(a: float, b: float, c: float) -> Tuple[float, ...]:
    return _quadratic(Fraction(_leading(a, "a")), Fraction(_num(b, "b")), Fraction(_num(c, "c")))


def cubic_roots(a: float, b: float, c: float, d: float) -> Tuple[float, ...]:
    fa, fb, fc, fd = Fraction(_leading(a, "a")), Fraction(_num(b, "b")), Fraction(_num(c, "c")), Fraction(_num(d, "d"))
    shift = fb / (3 * fa)                                   # x = t - shift gives t^3 + p t + q
    p = (3 * fa * fc - fb * fb) / (3 * fa * fa)
    q = (2 * fb ** 3 - 9 * fa * fb * fc + 27 * fa * fa * fd) / (27 * fa ** 3)
    disc = -(4 * p ** 3 + 27 * q * q)                       # exact: > 0 three real roots, == 0 a multiple root, < 0 one real root
    if disc == 0:
        if p == 0:                                          # triple root
            return (_float(-shift) + 0.0,)
        double, simple = -3 * q / (2 * p) - shift, 3 * q / p - shift          # exact rational roots
        return tuple(sorted((_float(double) + 0.0, _float(simple) + 0.0)))
    turning = _quadratic(3 * fa, 2 * fb, fc) if disc > 0 else ()                # three real roots are separated by the two turning points
    return _separated((fa, fb, fc, fd), turning)


def evaluate(coefficients: Sequence[float], x: float) -> Tuple[float, float]:
    if not isinstance(coefficients, (list, tuple)) or not 1 <= len(coefficients) <= MAX_COEFFICIENTS:
        raise ValueError("coefficients must be a list or tuple of 1 to 30 numbers, highest power first")
    cs = [_num(c, "a coefficient") for c in coefficients]
    at = _num(x, "x")
    p = dp = 0.0
    for c in cs:
        dp = dp * at + p
        p = p * at + c
    if not (math.isfinite(p) and math.isfinite(dp)):
        raise ValueError("the result overflows a float")
    return p, dp
