"""star_stats - mean, variance, standard deviation, RMS and weighted mean, correctly rounded (S.T.A.R., 2026-10-07).
Standard library only.

  mean(values)                       arithmetic mean
  variance(values, sample=True)      sample variance (divisor n - 1) or population variance (divisor n)
  stdev(values, sample=True)         its square root
  rms(values)                        root mean square
  weighted_mean(values, weights)     sum(w x) / sum(w), weights >= 0 and not all zero
Every float is an exact fraction, so each statistic is first computed EXACTLY in rational arithmetic and then
rounded once: the result is the float nearest to the true value of the formula applied to the numbers given. No
cancellation (the variance of 1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16 is exactly 30), no dependence on the order of
the values, no accumulated rounding. Square roots are rounded correctly too, by an integer square root.
Refusals (ValueError): values that are not a list or tuple of 1 to 100000 finite real numbers within +-1e150
(booleans refused); fewer than 2 values for a sample variance or standard deviation; `sample` not a bool; weights
of a different length, negative, not finite, beyond 1e150 or all zero.
"""
from __future__ import annotations

import math
import numbers
from fractions import Fraction
from typing import Sequence, Tuple

__all__ = ["mean", "variance", "stdev", "rms", "weighted_mean"]
__version__ = "0.1.0"

BIG = 1e150
MAX_VALUES = 100000


def _data(values, what: str = "values") -> Tuple[Fraction, ...]:
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= MAX_VALUES:
        raise ValueError(f"{what} must be a list or tuple of 1 to 100000 numbers")
    out = []
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"{what} must be finite real numbers within +-1e150")
        out.append(Fraction(float(v)))
    return tuple(out)


def _sqrt(q: Fraction) -> float:
    """The float nearest to the square root of the non-negative fraction q."""
    if q == 0:
        return 0.0
    shift = max(0, 128 - (q.numerator.bit_length() - q.denominator.bit_length()) // 2)     # the integer root gets at least 127 bits
    root = math.isqrt((q.numerator << (2 * shift)) // q.denominator)                       # floor(sqrt(q) * 2^shift)
    low, high = Fraction(root, 1 << shift), Fraction(root + 1, 1 << shift)                 # low <= sqrt(q) < high
    a, b = float(low), float(high)
    if a == b:
        return a
    middle = (Fraction(a) + Fraction(b)) / 2               # a rounding boundary lies between: decide exactly
    return b if middle * middle < q else a


def _variance(values, sample) -> Fraction:
    if not isinstance(sample, bool):
        raise ValueError("sample must be True or False")
    xs = _data(values)
    n = len(xs)
    if sample and n < 2:
        raise ValueError("a sample variance needs at least 2 values")
    total = sum(xs)
    return (n * sum(x * x for x in xs) - total * total) / (n * (n - 1 if sample else n))


def mean(values: Sequence[float]) -> float:
    xs = _data(values)
    return float(sum(xs) / len(xs))                          # a zero fraction has no sign: never -0.0


def variance(values: Sequence[float], sample: bool = True) -> float:
    return float(_variance(values, sample))


def stdev(values: Sequence[float], sample: bool = True) -> float:
    return _sqrt(_variance(values, sample))


def rms(values: Sequence[float]) -> float:
    xs = _data(values)
    return _sqrt(sum(x * x for x in xs) / len(xs))


def weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    xs, ws = _data(values), _data(weights, "weights")
    if len(ws) != len(xs):
        raise ValueError("weights must be as many as the values")
    if any(w < 0 for w in ws):
        raise ValueError("weights must not be negative")
    total = sum(ws)
    if total == 0:
        raise ValueError("weights must not be all zero")
    return float(sum(w * x for w, x in zip(ws, xs)) / total)
