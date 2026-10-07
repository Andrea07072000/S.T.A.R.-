"""star_tabint - integrals of tabulated data, correctly rounded (S.T.A.R., 2026-10-07).
Standard library only.

  trapezoid(xs, ys)        integral of the piecewise-linear curve through the points, xs strictly increasing
  cumulative(xs, ys)       the same integral from xs[0] up to each point: a tuple as long as the table, first 0.0
  simpson(ys, step)        composite Simpson rule for an odd number of equally spaced values (exact for cubics)
For samples of a quantity over time (power, thrust, current) these give the accumulated quantity (energy, impulse,
charge). Every float is an exact fraction: each rule is evaluated exactly in rational arithmetic and rounded once, so
the result is the float nearest to the exact value of the rule on the numbers given, with no cancellation between
positive and negative lobes and no dependence on how the sum is accumulated.
Refusals (ValueError): xs or ys that are not a list or tuple of 2 to 100000 finite real numbers within +-1e100
(booleans refused); different lengths; xs not strictly increasing; for `simpson`, fewer than 3 values, an even
number of values, or a step that is not a finite number in [1e-100, 1e100]. Within these limits no result can
overflow.
"""
from __future__ import annotations

import numbers
from fractions import Fraction
from typing import Sequence, Tuple

__all__ = ["trapezoid", "cumulative", "simpson"]
__version__ = "0.1.0"

BIG = 1e100
TINY = 1e-100
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


def _table(xs, ys):
    fx, fy = _column(xs, "xs"), _column(ys, "ys")
    if len(fy) != len(fx):
        raise ValueError("xs and ys must have the same length")
    if any(b <= a for a, b in zip(fx, fx[1:])):
        raise ValueError("xs must be strictly increasing")
    return fx, fy


def _panels(fx, fy):
    """Twice the area of each trapezoid, exact."""
    return [(fx[k + 1] - fx[k]) * (fy[k] + fy[k + 1]) for k in range(len(fx) - 1)]


def trapezoid(xs: Sequence[float], ys: Sequence[float]) -> float:
    return float(sum(_panels(*_table(xs, ys))) / 2)          # within the limits no result can overflow: at most 1e5 * 2e100 * 2e100


def cumulative(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, ...]:
    out, total = [0.0], Fraction(0)
    for panel in _panels(*_table(xs, ys)):
        total += panel
        out.append(float(total / 2))                       # each partial sum is rounded from the exact value: no error is carried forward
    return tuple(out)


def simpson(ys: Sequence[float], step: float) -> float:
    fy = _column(ys, "ys")
    if len(fy) % 2 == 0:                                    # a table has at least 2 values, so an odd one has at least 3
        raise ValueError("Simpson's rule needs an odd number of values, at least 3")
    try:
        ok = not isinstance(step, bool) and isinstance(step, numbers.Real) and TINY <= float(step) <= BIG
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("step must be a finite number within [1e-100, 1e100]")
    weighted = fy[0] + fy[-1] + 4 * sum(fy[1:-1:2]) + 2 * sum(fy[2:-1:2])
    return float(Fraction(float(step)) * weighted / 3)
