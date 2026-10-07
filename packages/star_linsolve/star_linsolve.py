"""star_linsolve - determinant, solution and inverse of a small square system, correctly rounded (S.T.A.R., 2026-10-07).
Standard library only.

  det(a)          determinant of the n x n matrix a (a list or tuple of n rows of n numbers), 1 <= n <= 20
  solve(a, b)     the vector x with a x = b, as a tuple of n floats
  inverse(a)      the inverse of a, as a tuple of n tuples of n floats
Every float is an exact fraction: the elimination is done in rational arithmetic and each result is rounded once, so
every number returned is the float nearest to the true one for the matrix as given, whatever its conditioning. A
matrix is singular exactly when its exact determinant is zero: no tolerance is involved, and a nearly singular matrix
is solved, not refused.
What exactness does not give: the solution of a badly conditioned system still changes a lot when the data change a
little, and the matrix you pass is made of floats (0.1 is not one tenth).
Refusals (ValueError): a that is not a list or tuple of 1 to 20 rows, each a list or tuple of as many finite real
numbers within +-1e100 (booleans refused); b that is not a list or tuple of n such numbers; a singular matrix (for
solve and inverse); a result too large for a float.
"""
from __future__ import annotations

import numbers
from fractions import Fraction
from typing import List, Sequence, Tuple

__all__ = ["det", "solve", "inverse"]
__version__ = "0.1.0"

BIG = 1e100
MAX_SIZE = 20


def _number(v, what: str) -> Fraction:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -BIG <= float(v) <= BIG       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must hold finite real numbers within +-1e100")
    return Fraction(float(v))


def _matrix(a) -> List[List[Fraction]]:
    if not isinstance(a, (list, tuple)) or not 1 <= len(a) <= MAX_SIZE:
        raise ValueError(f"a must be a list or tuple of 1 to {MAX_SIZE} rows")
    n = len(a)
    rows = []
    for row in a:
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise ValueError(f"a must be square: every row a list or tuple of {n} numbers")
        rows.append([_number(v, "a") for v in row])
    return rows


def _float(q: Fraction) -> float:
    try:
        return float(q)
    except OverflowError:
        raise ValueError("the result is too large for a float") from None


def _eliminate(rows: List[List[Fraction]], width: int) -> Fraction:
    """Gauss-Jordan in place on rows of n + width entries; returns the determinant (0 if singular, rows then unusable)."""
    n = len(rows)
    determinant = Fraction(1)
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            determinant = -determinant
        head = rows[col][col]
        determinant *= head
        if width:
            rows[col] = [v / head for v in rows[col]]
            head = Fraction(1)
        for r in range(n):
            if r != col and rows[r][col] != 0 and (width or r > col):
                factor = rows[r][col] / head
                rows[r] = [x - factor * y for x, y in zip(rows[r], rows[col])]
    return determinant


def det(a: Sequence[Sequence[float]]) -> float:
    return _float(_eliminate(_matrix(a), 0))


def solve(a: Sequence[Sequence[float]], b: Sequence[float]) -> Tuple[float, ...]:
    rows = _matrix(a)
    n = len(rows)
    if not isinstance(b, (list, tuple)) or len(b) != n:
        raise ValueError(f"b must be a list or tuple of {n} numbers")
    for row, v in zip(rows, b):
        row.append(_number(v, "b"))
    if _eliminate(rows, 1) == 0:
        raise ValueError("the matrix is singular")
    return tuple(_float(row[n]) for row in rows)


def inverse(a: Sequence[Sequence[float]]) -> Tuple[Tuple[float, ...], ...]:
    rows = _matrix(a)
    n = len(rows)
    for i, row in enumerate(rows):
        row.extend(Fraction(int(i == j)) for j in range(n))
    if _eliminate(rows, n) == 0:
        raise ValueError("the matrix is singular")
    return tuple(tuple(_float(v) for v in row[n:]) for row in rows)
