"""star_quaternion - unit quaternions and rotation matrices with one stated convention (S.T.A.R., 2026-10-06).
Standard library only.

Convention (the usual source of attitude bugs, so it is fixed and tested against two libraries):
  - a quaternion is (w, x, y, z), scalar FIRST, Hamilton product (ij = k);
  - it represents an ACTIVE rotation: rotate(q, v) = q v q*, the vector turned by the angle about the axis,
    right-hand rule; to_dcm(q) is the matrix R with rotate(q, v) = R v;
  - multiply(a, b) applies b first, then a: to_dcm(multiply(a, b)) = to_dcm(a) to_dcm(b).
NAIF SPICE (q2m, m2q) uses the same quaternion; SciPy stores the scalar LAST: (x, y, z, w).
Functions that need a unit quaternion accept a norm within 1e-6 of 1 and renormalise; anything further from 1 is
refused instead of being silently normalised. from_dcm refuses a matrix that is not a rotation (orthonormal to
1e-9, determinant +1) and returns the quaternion with w >= 0 (first non-zero component positive when w = 0).
Refusals (ValueError): wrong shape, non-numeric, boolean or non-finite input, zero quaternion or axis, a quaternion
that is not unit where one is required, a matrix that is not a rotation.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["normalize", "conjugate", "multiply", "rotate", "to_dcm", "from_dcm", "from_axis_angle", "to_axis_angle", "angle_between_deg"]
__version__ = "0.1.0"
UNIT_TOL = 1e-6
DCM_TOL = 1e-9
Quat = Tuple[float, float, float, float]
Vec = Tuple[float, float, float]
Mat = Tuple[Vec, Vec, Vec]


def _seq(v, n: int, what: str) -> tuple:
    try:
        ok = not isinstance(v, (str, bytes, dict, set, frozenset)) and len(v) == n
        items = tuple(v[i] for i in range(n)) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a sequence of {n} numbers")
    out = []
    for x in items:
        try:
            good = not isinstance(x, bool) and isinstance(x, numbers.Real) and -1e150 < float(x) < 1e150     # NaN fails both
        except OverflowError:
            good = False
        if not good:
            raise ValueError(f"{what} must contain finite real numbers (magnitude below 1e150)")
        out.append(float(x))
    return tuple(out)


def normalize(q: Sequence[float]) -> Quat:
    """The unit quaternion with the direction of q (any non-zero quaternion)."""
    w, x, y, z = _seq(q, 4, "quaternion")
    n = math.hypot(w, x, y, z)
    if n == 0.0:
        raise ValueError("the zero quaternion has no direction")
    return w / n, x / n, y / n, z / n


def _unit(q: Sequence[float]) -> Quat:
    w, x, y, z = _seq(q, 4, "quaternion")
    n = math.hypot(w, x, y, z)
    if abs(n - 1.0) > UNIT_TOL:
        raise ValueError(f"not a unit quaternion (norm {n!r}); call normalize() if that is intended")
    return w / n, x / n, y / n, z / n


def conjugate(q: Sequence[float]) -> Quat:
    """The inverse rotation."""
    w, x, y, z = _unit(q)
    return w, -x, -y, -z


def multiply(a: Sequence[float], b: Sequence[float]) -> Quat:
    """Hamilton product a b: the rotation b followed by the rotation a."""
    aw, ax, ay, az = _unit(a)
    bw, bx, by, bz = _unit(b)
    return (aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw)


def to_dcm(q: Sequence[float]) -> Mat:
    """Rotation matrix R with rotate(q, v) = R v."""
    w, x, y, z = _unit(q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
            (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
            (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)))


def rotate(q: Sequence[float], v: Sequence[float]) -> Vec:
    """The vector v turned by the rotation q."""
    r = to_dcm(q)
    a, b, c = _seq(v, 3, "vector")
    return (r[0][0] * a + r[0][1] * b + r[0][2] * c, r[1][0] * a + r[1][1] * b + r[1][2] * c, r[2][0] * a + r[2][1] * b + r[2][2] * c)


def _matrix(m) -> Mat:
    rows = _seq_rows(m)
    for i in range(3):
        for j in range(3):
            dot = sum(rows[k][i] * rows[k][j] for k in range(3))
            if abs(dot - (1.0 if i == j else 0.0)) > DCM_TOL:
                raise ValueError("not a rotation matrix: columns are not orthonormal to 1e-9")
    det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1]) - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
           + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    if det < 0.0:
        raise ValueError("not a rotation matrix: determinant is -1 (a reflection)")
    return rows


def _seq_rows(m) -> Mat:
    try:
        ok = not isinstance(m, (str, bytes, dict, set, frozenset)) and len(m) == 3
        rows = tuple(m[i] for i in range(3)) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok:
        raise ValueError("matrix must be 3 rows of 3 numbers")
    return tuple(_seq(r, 3, "matrix row") for r in rows)


def from_dcm(m) -> Quat:
    """The unit quaternion of a rotation matrix (largest-component method: no division by a small number)."""
    r = _matrix(m)
    trace = r[0][0] + r[1][1] + r[2][2]
    cand = (trace, r[0][0], r[1][1], r[2][2])
    k = max(range(4), key=lambda i: cand[i])
    if k == 0:
        s = 2.0 * math.sqrt(1.0 + trace)
        q = (0.25 * s, (r[2][1] - r[1][2]) / s, (r[0][2] - r[2][0]) / s, (r[1][0] - r[0][1]) / s)
    elif k == 1:
        s = 2.0 * math.sqrt(1.0 + r[0][0] - r[1][1] - r[2][2])
        q = ((r[2][1] - r[1][2]) / s, 0.25 * s, (r[0][1] + r[1][0]) / s, (r[0][2] + r[2][0]) / s)
    elif k == 2:
        s = 2.0 * math.sqrt(1.0 + r[1][1] - r[0][0] - r[2][2])
        q = ((r[0][2] - r[2][0]) / s, (r[0][1] + r[1][0]) / s, 0.25 * s, (r[1][2] + r[2][1]) / s)
    else:
        s = 2.0 * math.sqrt(1.0 + r[2][2] - r[0][0] - r[1][1])
        q = ((r[1][0] - r[0][1]) / s, (r[0][2] + r[2][0]) / s, (r[1][2] + r[2][1]) / s, 0.25 * s)
    return _canonical(normalize(q))


def _canonical(q: Quat) -> Quat:
    """q and -q are the same rotation: return the one with w >= 0 (first non-zero component positive when w = 0)."""
    lead = next((c for c in q if abs(c) > 1e-15), 1.0)
    return tuple(-c if c != 0.0 else 0.0 for c in q) if lead < 0.0 else tuple(c if c != 0.0 else 0.0 for c in q)


def from_axis_angle(axis: Sequence[float], angle_deg: float) -> Quat:
    """Rotation by angle_deg about axis (any non-zero length), right-hand rule."""
    x, y, z = _seq(axis, 3, "axis")
    (angle,) = _seq((angle_deg,), 1, "angle")
    scale = max(abs(x), abs(y), abs(z))
    if scale == 0.0:
        raise ValueError("the zero vector is not an axis")
    x, y, z = x / scale, y / scale, z / scale
    n = math.hypot(x, y, z)
    half = math.radians(angle % 720.0) / 2.0
    s = math.sin(half) / n
    return math.cos(half), x * s, y * s, z * s


def to_axis_angle(q: Sequence[float]) -> Tuple[Vec, float]:
    """(unit axis, angle in [0, 180] degrees); for the identity the axis is (1, 0, 0) by convention."""
    w, x, y, z = _canonical(_unit(q))
    s = math.hypot(x, y, z)
    if s < 1e-15:
        return (1.0, 0.0, 0.0), 0.0
    return (x / s, y / s, z / s), math.degrees(2.0 * math.atan2(s, w))


def angle_between_deg(a: Sequence[float], b: Sequence[float]) -> float:
    """Angle in [0, 180] degrees of the single rotation that takes attitude a to attitude b."""
    w, x, y, z = multiply(conjugate(a), b)
    return math.degrees(2.0 * math.atan2(math.hypot(x, y, z), abs(w)))
