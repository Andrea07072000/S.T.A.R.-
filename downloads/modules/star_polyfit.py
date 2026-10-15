"""star_polyfit - least-squares polynomial of degree 0 to 10, correctly rounded (S.T.A.R., 2026-10-07).
Standard library only.

  polyfit(xs, ys, degree, weights=None)        coefficients (c0, c1, ..., c_degree) of the polynomial that minimises
                                               the sum of w * (y - p(x))^2, lowest power first
  polyval(coefficients, x)                     c0 + c1 x + ... at one x
  residual_sum(xs, ys, coefficients, weights=None)   the sum of w * (y - p(x))^2 for the coefficients given
Every float is an exact fraction: the normal equations are formed and solved in rational arithmetic and each result
is rounded once. The answer is therefore the float nearest to the true least-squares coefficient of the data as
given, whatever the conditioning: x far from the origin (1e9 + k), a high degree, nearly equal abscissas lose nothing.
What exactness does not give: a high-degree fit of noisy data is still a bad model, and the exact coefficients of a
badly conditioned problem still change a lot when the data change a little.
Refusals (ValueError): a degree that is not an integer from 0 to 10; xs or ys that are not a list or tuple of 1 to
10000 finite real numbers within +-1e100 (booleans refused); different lengths; weights that are not None or as many
finite numbers >= 0; fewer distinct x with a positive weight than degree + 1 (the fit is not unique); a result too
large for a float.
"""
from __future__ import annotations

import numbers
from fractions import Fraction
from typing import Optional, Sequence, Tuple

__all__ = ["polyfit", "polyval", "residual_sum"]
__version__ = "0.1.0"

BIG = 1e100
MAX_POINTS = 10000
MAX_DEGREE = 10


def _number(v, what: str) -> Fraction:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be finite real numbers within +-1e100")
    return Fraction(float(v))


def _column(values, what: str, lowest: int = 1, highest: int = MAX_POINTS) -> Tuple[Fraction, ...]:
    if not isinstance(values, (list, tuple)) or not lowest <= len(values) <= highest:
        raise ValueError(f"{what} must be a list or tuple of {lowest} to {highest} numbers")
    return tuple(_number(v, what) for v in values)


def _data(xs, ys, weights):
    fx, fy = _column(xs, "xs"), _column(ys, "ys")
    if len(fy) != len(fx):
        raise ValueError("xs and ys must have the same length")
    if weights is None:
        return fx, fy, (Fraction(1),) * len(fx)
    fw = _column(weights, "weights")
    if len(fw) != len(fx):
        raise ValueError("weights must be as many as the points")
    if any(w < 0 for w in fw):
        raise ValueError("weights must be >= 0")
    return fx, fy, fw


def _float(q: Fraction) -> float:
    try:
        return float(q)
    except OverflowError:
        raise ValueError("the result is too large for a float") from None


def _evaluate(coefficients, x: Fraction) -> Fraction:
    total = Fraction(0)
    for c in reversed(coefficients):
        total = total * x + c
    return total


def polyfit(xs: Sequence[float], ys: Sequence[float], degree: int, weights: Optional[Sequence[float]] = None) -> Tuple[float, ...]:
    if isinstance(degree, bool) or not isinstance(degree, numbers.Integral) or not 0 <= degree <= MAX_DEGREE:
        raise ValueError(f"degree must be an integer from 0 to {MAX_DEGREE}")
    degree = int(degree)
    fx, fy, fw = _data(xs, ys, weights)
    size = degree + 1
    moments = [Fraction(0)] * (2 * degree + 1)             # sum of w x^k
    rhs = [Fraction(0)] * size                             # sum of w x^k y
    for x, y, w in zip(fx, fy, fw):
        power = w
        for k in range(2 * degree + 1):
            moments[k] += power
            if k < size:
                rhs[k] += power * y
            power *= x
    rows = [[moments[i + j] for j in range(size)] + [rhs[i]] for i in range(size)]
    for col in range(size):                                # exact elimination: any non-zero pivot will do
        pivot = next((r for r in range(col, size) if rows[r][col] != 0), None)
        if pivot is None:
            raise ValueError(f"a fit of degree {degree} needs at least {size} distinct x with a positive weight")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        head = rows[col][col]
        for r in range(col + 1, size):
            factor = rows[r][col] / head
            if factor:
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col])]
    solution = [Fraction(0)] * size
    for i in range(size - 1, -1, -1):
        solution[i] = (rows[i][size] - sum(rows[i][j] * solution[j] for j in range(i + 1, size))) / rows[i][i]
    return tuple(_float(c) for c in solution)


def _coefficients(coefficients) -> Tuple[Fraction, ...]:
    return _column(coefficients, "coefficients", 1, MAX_DEGREE + 1)


def polyval(coefficients: Sequence[float], x: float) -> float:
    return _float(_evaluate(_coefficients(coefficients), _number(x, "x")))


def residual_sum(xs: Sequence[float], ys: Sequence[float], coefficients: Sequence[float], weights: Optional[Sequence[float]] = None) -> float:
    fc = _coefficients(coefficients)
    fx, fy, fw = _data(xs, ys, weights)
    return _float(sum(w * (y - _evaluate(fc, x)) ** 2 for x, y, w in zip(fx, fy, fw)))
