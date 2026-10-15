"""star_euler - Euler angles and rotation matrices for the twelve axis sequences (S.T.A.R., 2026-10-06).
Standard library only.

Convention (stated once, tested against two libraries):
  - a sequence is three letters among X, Y, Z with no letter repeated consecutively: the six Tait-Bryan sequences
    (XYZ, XZY, YXZ, YZX, ZXY, ZYX) and the six proper Euler sequences (XYX, XZX, YXY, YZY, ZXZ, ZYZ);
  - rotations are ACTIVE and INTRINSIC: to_dcm("ZYX", a1, a2, a3) = Rz(a1) Ry(a2) Rx(a3), i.e. turn by a1 about Z,
    then by a2 about the NEW Y, then by a3 about the NEW X; Ru(a) turns vectors by a about u, right-hand rule;
  - angles in degrees. This is SciPy's upper-case sequence; NAIF SPICE eul2m returns the transpose (frame rotations).
from_dcm returns the angles with the middle one in [-90, 90] (Tait-Bryan) or [0, 180] (proper), the others in
(-180, 180]. At gimbal lock (middle angle within 1e-7 deg of +-90, or of 0 / 180) only a1 +- a3 is defined: the third
angle is returned as 0.0 and the first carries the whole rotation; is_singular() tells the caller.
Refusals (ValueError): an unknown sequence, wrong shapes, non-numeric, boolean or non-finite input, a matrix that is
not a rotation (orthonormal to 1e-9, determinant +1).
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["SEQUENCES", "to_dcm", "from_dcm", "is_singular"]
__version__ = "0.1.0"
SEQUENCES = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX", "XYX", "XZX", "YXY", "YZY", "ZXZ", "ZYZ")
DCM_TOL = 1e-9
LOCK_TOL = 2e-9          # on the sine or cosine that vanishes at gimbal lock: about 1e-7 degrees from the singular angle
Mat = Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]


def _num(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e150 < float(v) < 1e150      # NaN fails both
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number")
    return float(v)


def _axes(seq) -> Tuple[int, int, int]:
    if not isinstance(seq, str) or seq not in SEQUENCES:
        raise ValueError(f"sequence must be one of {', '.join(SEQUENCES)}")
    return tuple("XYZ".index(c) for c in seq)


def _elementary(axis: int, deg: float):
    r = math.radians(math.fmod(deg, 360.0))
    c, s = math.cos(r), math.sin(r)
    j, k = (axis + 1) % 3, (axis + 2) % 3
    m = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    m[axis][axis] = 1.0
    m[j][j], m[j][k], m[k][j], m[k][k] = c, -s, s, c
    return m


def _mul(a, b):
    return [[a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j] for j in range(3)] for i in range(3)]


def to_dcm(seq: str, a1_deg: float, a2_deg: float, a3_deg: float) -> Mat:
    i, j, k = _axes(seq)
    a1, a2, a3 = _num(a1_deg, "a1"), _num(a2_deg, "a2"), _num(a3_deg, "a3")
    m = _mul(_mul(_elementary(i, a1), _elementary(j, a2)), _elementary(k, a3))
    return tuple(tuple(row) for row in m)


def _matrix(m) -> Mat:
    try:
        ok = not isinstance(m, (str, bytes, dict, set, frozenset)) and len(m) == 3
        rows = [m[0], m[1], m[2]] if ok else []
        ok = ok and all(not isinstance(r, (str, bytes, dict, set, frozenset)) and len(r) == 3 for r in rows)
        rows = tuple(tuple(_num(r[c], "matrix entry") for c in range(3)) for r in rows) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok:
        raise ValueError("matrix must be 3 rows of 3 numbers")
    for a in range(3):
        for b in range(3):
            dot = sum(rows[c][a] * rows[c][b] for c in range(3))
            if abs(dot - (1.0 if a == b else 0.0)) > DCM_TOL:
                raise ValueError("not a rotation matrix: columns are not orthonormal to 1e-9")
    det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1]) - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
           + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    if det < 0.0:
        raise ValueError("not a rotation matrix: determinant is -1 (a reflection)")
    return rows


def _solve(seq: str, m):
    """(a1, a2, a3 in radians, singular flag) for a validated rotation matrix."""
    i, j, _ = _axes(seq)
    proper = seq[0] == seq[2]
    k = 3 - i - j                                            # the axis that is not the first two
    eps = 1.0 if (j - i) % 3 == 1 else -1.0                  # +1 when (i, j, k) is a cyclic permutation of (X, Y, Z)
    if proper:
        sin2 = math.hypot(m[j][i], m[k][i])
        a2 = math.atan2(sin2, m[i][i])
        if sin2 < LOCK_TOL:
            return math.atan2(eps * m[k][j], m[j][j]), a2, 0.0, True
        return math.atan2(m[j][i], -eps * m[k][i]), a2, math.atan2(m[i][j], eps * m[i][k]), False
    cos2 = math.hypot(m[i][i], m[i][j])
    a2 = math.atan2(eps * m[i][k], cos2)
    if cos2 < LOCK_TOL:
        return math.atan2(eps * m[k][j], m[j][j]), a2, 0.0, True
    return math.atan2(-eps * m[j][k], m[k][k]), a2, math.atan2(-eps * m[i][j], m[i][i]), False


def from_dcm(seq: str, m) -> Tuple[float, float, float]:
    _axes(seq)
    a1, a2, a3, _ = _solve(seq, _matrix(m))
    return tuple(0.0 if x == 0.0 else math.degrees(x) for x in (a1, a2, a3))


def is_singular(seq: str, m) -> bool:
    """True when the matrix is at gimbal lock for this sequence (the first and third angles are not separately defined)."""
    _axes(seq)
    return _solve(seq, _matrix(m))[3]
