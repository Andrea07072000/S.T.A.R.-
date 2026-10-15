"""star_quantile - median, quantiles, interquartile range and median absolute deviation (S.T.A.R., 2026-10-07).
Standard library only.

  median(values)           the middle value, or the mean of the two middle values
  quantile(values, q)      the q-quantile, 0 <= q <= 1, by linear interpolation between order statistics
  iqr(values)              quantile 0.75 minus quantile 0.25
  mad(values)              median of the absolute deviations from the median (not scaled)
The quantile is the definition numbered 7 by Hyndman and Fan (1996), the default of NumPy, R and spreadsheets: with
the n values sorted, position h = (n - 1) q, and the result is x[floor h] + (h - floor h) (x[floor h + 1] - x[floor
h]). Every float is an exact fraction (q included): the interpolation is done exactly and rounded once, so the result
is the float nearest to the exact value of the definition, and a difference such as the interquartile range is not
the difference of two rounded numbers. These statistics resist outliers: one wild sample does not move the median.
Refusals (ValueError): values that are not a list or tuple of 1 to 100000 finite real numbers within +-1e150
(booleans refused); q that is not a finite real number in [0, 1] (booleans refused).
"""
from __future__ import annotations

import numbers
from fractions import Fraction
from typing import List, Sequence

__all__ = ["median", "quantile", "iqr", "mad"]
__version__ = "0.1.0"

BIG = 1e150
MAX_VALUES = 100000
HALF, QUARTER = Fraction(1, 2), Fraction(1, 4)


def _sorted(values) -> List[Fraction]:
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= MAX_VALUES:
        raise ValueError("values must be a list or tuple of 1 to 100000 numbers")
    out = []
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError("values must be finite real numbers within +-1e150")
        out.append(Fraction(float(v)))
    return sorted(out)


def _at(ordered: Sequence[Fraction], q: Fraction) -> Fraction:
    """The q-quantile of sorted values, exact."""
    h = (len(ordered) - 1) * q
    low = h.numerator // h.denominator
    if low == len(ordered) - 1:                              # q == 1: the largest value, nothing to interpolate
        return ordered[low]
    return ordered[low] + (h - low) * (ordered[low + 1] - ordered[low])


def median(values: Sequence[float]) -> float:
    return float(_at(_sorted(values), HALF))


def quantile(values: Sequence[float], q: float) -> float:
    ordered = _sorted(values)
    try:
        ok = not isinstance(q, bool) and isinstance(q, numbers.Real) and 0.0 <= float(q) <= 1.0
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("q must be a finite real number from 0 to 1")
    return float(_at(ordered, Fraction(float(q))))


def iqr(values: Sequence[float]) -> float:
    ordered = _sorted(values)
    return float(_at(ordered, 3 * QUARTER) - _at(ordered, QUARTER))


def mad(values: Sequence[float]) -> float:
    ordered = _sorted(values)
    centre = _at(ordered, HALF)
    return float(_at(sorted(abs(v - centre) for v in ordered), HALF))
