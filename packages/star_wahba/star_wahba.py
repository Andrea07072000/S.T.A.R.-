"""star_wahba - attitude from vector observations: TRIAD and Davenport's q-method (S.T.A.R., 2026-10-07).
Standard library only.

  triad(r1, r2, b1, b2)                    attitude matrix from two directions: the first pair is matched exactly
  q_method(refs, bodies, weights=None)     the unit quaternion (w, x, y, z) that minimises Wahba's loss over n >= 2 pairs
  rotation_matrix(q)                       the attitude matrix of a quaternion
  wahba_loss(q, refs, bodies, weights=None)   0.5 sum of w |b - A r|^2 over the unit vectors, the weights normalised to sum 1
Convention: every observation is a direction r known in the REFERENCE frame (a star, the Sun, the magnetic field) and
the same direction b measured in the BODY frame; the attitude matrix A takes reference to body, b = A r. A quaternion
q = (w, x, y, z), scalar first, w >= 0, has A = (w^2 - |v|^2) I + 2 v v^T - 2 w [v x] with v = (x, y, z). Vectors need
not be unit: only their directions are used. Matrices are tuples of three rows.

How: TRIAD builds an orthonormal triad from each pair (Black 1964). The q-method (Davenport 1968) takes the eigenvector
of the largest eigenvalue of the 4 x 4 symmetric matrix K built from B = sum of w b r^T; the eigenproblem is solved by
Jacobi rotations, which need no library and return orthonormal vectors to rounding.
Refusals (ValueError): a vector that is not three finite real numbers (booleans refused) or is zero; fewer than 2 or
more than 1000 pairs, or lists of different lengths; weights that are not as many positive finite numbers; directions
that do not fix the attitude (parallel within 1e-12 for TRIAD; for the q-method, the two largest eigenvalues of K equal
within 1e-12 of the total weight); a quaternion that is not four finite numbers or is zero.
"""
from __future__ import annotations

import math
import numbers
from typing import List, Optional, Sequence, Tuple

__all__ = ["triad", "q_method", "rotation_matrix", "wahba_loss"]
__version__ = "0.1.0"

MAX_PAIRS = 1000
PARALLEL = 1e-12
Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]
Quaternion = Tuple[float, float, float, float]


def _unit(v, what: str) -> Vector:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"{what} must be a list or tuple of 3 numbers")
    out = []
    for c in v:
        try:
            ok = not isinstance(c, bool) and isinstance(c, numbers.Real) and math.isfinite(float(c))
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"{what} must hold finite real numbers, got {c!r}")
        out.append(float(c))
    scale = max(abs(c) for c in out)
    if scale == 0.0:
        raise ValueError(f"{what} is the zero vector: it has no direction")
    out = [c / scale for c in out]                           # no overflow or underflow in the norm
    norm = math.sqrt(out[0] * out[0] + out[1] * out[1] + out[2] * out[2])
    return (out[0] / norm, out[1] / norm, out[2] / norm)


def _cross(a: Vector, b: Vector) -> Vector:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _triad_frame(first: Vector, second: Vector, what: str):
    normal = _cross(first, second)
    size = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)
    if size < PARALLEL:
        raise ValueError(f"the two {what} directions are parallel: they do not fix an attitude")
    normal = (normal[0] / size, normal[1] / size, normal[2] / size)
    return first, normal, _cross(first, normal)


def triad(r1, r2, b1, b2) -> Matrix:
    ref = _triad_frame(_unit(r1, "r1"), _unit(r2, "r2"), "reference")
    body = _triad_frame(_unit(b1, "b1"), _unit(b2, "b2"), "body")
    return tuple(tuple(sum(body[k][i] * ref[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _pairs(refs, bodies, weights):
    if not isinstance(refs, (list, tuple)) or not isinstance(bodies, (list, tuple)) or len(refs) != len(bodies):
        raise ValueError("refs and bodies must be lists or tuples of the same length")
    if not 2 <= len(refs) <= MAX_PAIRS:
        raise ValueError(f"between 2 and {MAX_PAIRS} pairs of directions are needed, got {len(refs)}")
    r = [_unit(v, "a reference vector") for v in refs]
    b = [_unit(v, "a body vector") for v in bodies]
    if weights is None:
        w = [1.0] * len(r)
    else:
        if not isinstance(weights, (list, tuple)) or len(weights) != len(r):
            raise ValueError("weights must be as many as the pairs")
        w = []
        for x in weights:
            try:
                ok = not isinstance(x, bool) and isinstance(x, numbers.Real) and math.isfinite(float(x)) and float(x) > 0.0
            except OverflowError:
                ok = False
            if not ok:
                raise ValueError(f"weights must be positive finite numbers, got {x!r}")
            w.append(float(x))
    total = math.fsum(w)
    return r, b, [x / total for x in w]


def _jacobi(k: List[List[float]]):
    """Eigenvalues and eigenvectors (columns of v) of a symmetric 4 x 4 matrix by cyclic Jacobi rotations."""
    n = 4
    a = [row[:] for row in k]
    v = [[float(i == j) for j in range(n)] for i in range(n)]
    for _ in range(60):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(i + 1, n)))
        if off < 1e-300:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if a[p][q] == 0.0:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for i in range(n):                           # columns p and q
                    a[i][p], a[i][q] = c * a[i][p] - s * a[i][q], s * a[i][p] + c * a[i][q]
                for i in range(n):                           # rows p and q
                    a[p][i], a[q][i] = c * a[p][i] - s * a[q][i], s * a[p][i] + c * a[q][i]
                for i in range(n):
                    v[i][p], v[i][q] = c * v[i][p] - s * v[i][q], s * v[i][p] + c * v[i][q]
    return [a[i][i] for i in range(n)], v


def q_method(refs, bodies, weights: Optional[Sequence[float]] = None) -> Quaternion:
    r, b, w = _pairs(refs, bodies, weights)
    bm = [[math.fsum(w[n] * b[n][i] * r[n][j] for n in range(len(r))) for j in range(3)] for i in range(3)]
    sigma = bm[0][0] + bm[1][1] + bm[2][2]
    z = (bm[1][2] - bm[2][1], bm[2][0] - bm[0][2], bm[0][1] - bm[1][0])
    k = [[bm[i][j] + bm[j][i] - (sigma if i == j else 0.0) for j in range(3)] + [z[i]] for i in range(3)] + [[z[0], z[1], z[2], sigma]]
    values, vectors = _jacobi(k)
    order = sorted(range(4), key=lambda i: values[i], reverse=True)
    if values[order[0]] - values[order[1]] < PARALLEL:       # weights sum to 1: the gap is relative to the total weight
        raise ValueError("the observations do not fix an attitude (all directions parallel, or as good as)")
    best = order[0]
    x, y, zq, s = (vectors[i][best] for i in range(4))
    norm = math.sqrt(x * x + y * y + zq * zq + s * s)
    sign = -1.0 if s < 0.0 else 1.0
    return (sign * s / norm, sign * x / norm, sign * y / norm, sign * zq / norm)


def _quaternion(q) -> Quaternion:
    if not isinstance(q, (list, tuple)) or len(q) != 4:
        raise ValueError("q must be a list or tuple of 4 numbers (w, x, y, z)")
    out = []
    for c in q:
        try:
            ok = not isinstance(c, bool) and isinstance(c, numbers.Real) and math.isfinite(float(c))
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"q must hold finite real numbers, got {c!r}")
        out.append(float(c))
    scale = max(abs(c) for c in out)
    if scale == 0.0:
        raise ValueError("q is the zero quaternion: it is not a rotation")
    out = [c / scale for c in out]
    norm = math.sqrt(sum(c * c for c in out))
    return tuple(c / norm for c in out)


def rotation_matrix(q) -> Matrix:
    w, x, y, z = _quaternion(q)
    return ((w * w + x * x - y * y - z * z, 2.0 * (x * y + w * z), 2.0 * (x * z - w * y)),
            (2.0 * (x * y - w * z), w * w - x * x + y * y - z * z, 2.0 * (y * z + w * x)),
            (2.0 * (x * z + w * y), 2.0 * (y * z - w * x), w * w - x * x - y * y + z * z))


def wahba_loss(q, refs, bodies, weights: Optional[Sequence[float]] = None) -> float:
    a = rotation_matrix(q)
    r, b, w = _pairs(refs, bodies, weights)
    total = math.fsum(w[n] * sum((b[n][i] - sum(a[i][j] * r[n][j] for j in range(3))) ** 2 for i in range(3)) for n in range(len(r)))
    return 0.5 * total
