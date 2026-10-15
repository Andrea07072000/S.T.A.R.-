"""star_mat3 - the 3x3 matrix operations of frame and attitude code (S.T.A.R., 2026-10-06). Standard library only.

  transpose(m), determinant(m), inverse(m)
  matmul(a, b)            the matrix product a b
  matvec(m, v)            m v;   matvec(transpose(m), v) applies the inverse of a rotation
  identity()
  is_rotation(m, tol=1e-12)   True if m is orthonormal with determinant +1 within tol (a proper rotation, no reflection)
A matrix is a list or tuple of three rows, each a list or tuple of three finite real numbers; results are tuples of
tuples of floats. The determinant and the inverse are computed in exact rational arithmetic (a float is an exact
fraction) and rounded once, so they are correct to the last digit whatever the conditioning; the products use
compensated sums. `inverse` refuses a matrix whose determinant is zero or negligible against the size of its
entries: a nearly singular matrix has no usable inverse in double precision, and returning one would hide it.
Refusals (ValueError): a matrix or vector of the wrong shape or type; an entry that is not a finite real number
(booleans included) or exceeds 1e60 in absolute value; for `inverse`, a determinant of the matrix scaled to unit
largest entry that is 1e-12 or less in absolute value; a tolerance outside (0, 1].
"""
from __future__ import annotations

import math
import numbers
from fractions import Fraction
from typing import Sequence, Tuple

__all__ = ["transpose", "determinant", "inverse", "matmul", "matvec", "identity", "is_rotation"]
__version__ = "0.1.0"

BIG = 1e60                              # so that a determinant (6 BIG^3) and a product cannot overflow
SINGULAR = 1e-12
Vec = Tuple[float, float, float]
Mat = Tuple[Vec, Vec, Vec]


def _num(c, what: str) -> float:
    try:
        ok = not isinstance(c, bool) and isinstance(c, numbers.Real) and -BIG <= float(c) <= BIG       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must hold finite real numbers within +-1e60")
    return float(c)


def _vec(v, what: str = "a vector") -> Vec:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"{what} must be a list or tuple of three numbers")
    return _num(v[0], what), _num(v[1], what), _num(v[2], what)


def _mat(m, what: str = "a matrix") -> Mat:
    if not isinstance(m, (list, tuple)) or len(m) != 3:
        raise ValueError(f"{what} must be a list or tuple of three rows")
    return _vec(m[0], what), _vec(m[1], what), _vec(m[2], what)


def _exact(m: Mat):
    return tuple(tuple(Fraction(c) for c in row) for row in m)       # a float is an exact fraction


def _det_exact(e):
    return (e[0][0] * (e[1][1] * e[2][2] - e[1][2] * e[2][1]) - e[0][1] * (e[1][0] * e[2][2] - e[1][2] * e[2][0])
            + e[0][2] * (e[1][0] * e[2][1] - e[1][1] * e[2][0]))


def _det(m: Mat) -> float:
    return float(_det_exact(_exact(m)))                     # exact, rounded once


def identity() -> Mat:
    return (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)


def transpose(m: Sequence[Sequence[float]]) -> Mat:
    m = _mat(m)
    return (m[0][0], m[1][0], m[2][0]), (m[0][1], m[1][1], m[2][1]), (m[0][2], m[1][2], m[2][2])


def determinant(m: Sequence[Sequence[float]]) -> float:
    return _det(_mat(m))


def matmul(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> Mat:
    a, b = _mat(a, "the first matrix"), _mat(b, "the second matrix")
    return tuple(tuple(math.fsum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def matvec(m: Sequence[Sequence[float]], v: Sequence[float]) -> Vec:
    m, v = _mat(m), _vec(v)
    return tuple(math.fsum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def inverse(m: Sequence[Sequence[float]]) -> Mat:
    m = _mat(m)
    scale = max(abs(c) for row in m for c in row)
    e = _exact(m)
    det = _det_exact(e)
    # the test is on the matrix scaled to unit largest entry, so that it does not depend on the units of the matrix
    if scale == 0.0 or abs(det) <= Fraction(SINGULAR) * Fraction(scale) ** 3:
        raise ValueError("the matrix is singular or nearly singular: it has no usable inverse")

    def cof(i: int, j: int):                                # cofactor of the element (i, j), indices cyclic, exact
        return e[(i + 1) % 3][(j + 1) % 3] * e[(i + 2) % 3][(j + 2) % 3] - e[(i + 1) % 3][(j + 2) % 3] * e[(i + 2) % 3][(j + 1) % 3]

    try:
        out = tuple(tuple(float(cof(j, i) / det) for j in range(3)) for i in range(3))     # exact adjugate over exact determinant, rounded once
    except OverflowError:
        raise ValueError("the inverse overflows a float") from None
    return out


def is_rotation(m: Sequence[Sequence[float]], tol: float = 1e-12) -> bool:
    m = _mat(m)
    try:
        ok = not isinstance(tol, bool) and isinstance(tol, numbers.Real) and 0.0 < float(tol) <= 1.0
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("tol must be a real number within (0, 1]")
    for i in range(3):
        for j in range(i, 3):
            want = 1.0 if i == j else 0.0
            if abs(math.fsum(m[i][k] * m[j][k] for k in range(3)) - want) > tol:
                return False
    return abs(_det(m) - 1.0) <= tol
