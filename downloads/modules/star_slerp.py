"""star_slerp - interpolation of attitudes along the shortest arc (S.T.A.R., 2026-10-07).
Standard library only.

  slerp(q0, q1, t)                    the attitude a fraction t (0..1) of the way from q0 to q1
  interpolate(times, quaternions, t)  the attitude at time t from a table of attitudes at increasing times
A quaternion is (w, x, y, z), scalar FIRST, of unit length (the convention of star_quaternion and of NAIF SPICE;
SciPy stores the scalar last). The interpolation is spherical and linear in the rotation angle: the rotation from q0
to the result is the fraction t of the rotation from q0 to q1, about the same axis, at constant angular rate.
q and -q are the same attitude: when q0 and q1 lie in opposite hemispheres q1 is negated first, so the path is
always the SHORTER rotation (at most 180 degrees). The result is of unit length and in the hemisphere of q0.
`interpolate` applies this between the two table rows that bracket t; each pair is taken along its own shortest arc.
Refusals (ValueError): a quaternion that is not a list or tuple of 4 finite real numbers or whose length differs from 1
by more than 1e-9 (it is NOT normalised silently); t outside [0, 1] or not a finite real number; for `interpolate`,
times that are not a list or tuple of 2 to 100000 finite numbers within +-1e15 and strictly increasing, a different
number of quaternions, or a t outside the table (no extrapolation). Booleans are refused everywhere.
"""
from __future__ import annotations

import bisect
import math
import numbers
from typing import Sequence, Tuple

__all__ = ["slerp", "interpolate"]
__version__ = "0.1.0"

UNIT_TOLERANCE = 1e-9
SMALL_ANGLE = 1e-8                                          # below this sine of the half-angle between the two, the arc is a chord
BIG_TIME = 1e15
MAX_ROWS = 100000

Quaternion = Tuple[float, float, float, float]


def _real(v, what: str, lowest: float, highest: float) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lowest <= float(v) <= highest     # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number from {lowest:g} to {highest:g}")
    return float(v)


def _unit(q, what: str) -> Quaternion:
    if not isinstance(q, (list, tuple)) or len(q) != 4:
        raise ValueError(f"{what} must be a list or tuple of 4 numbers (w, x, y, z)")
    w, x, y, z = (_real(c, f"a component of {what}", -2.0, 2.0) for c in q)
    if abs(math.hypot(w, x, y, z) - 1.0) > UNIT_TOLERANCE:
        raise ValueError(f"{what} must be of unit length (it is not normalised silently)")
    return w, x, y, z


def _arc(a: Quaternion, b: Quaternion, t: float) -> Quaternion:
    d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    if d < 0.0:                                             # the other hemisphere: -b is the same attitude and is nearer
        b, d = (-b[0], -b[1], -b[2], -b[3]), -d
    across = tuple(b[k] - d * a[k] for k in range(4))        # the part of b orthogonal to a: its length is the sine of the angle
    s = math.hypot(*across)
    if s < SMALL_ANGLE:
        mixed = tuple(a[k] + t * (b[k] - a[k]) for k in range(4))
    else:
        angle = math.atan2(s, d)                            # accurate for every angle, unlike acos(d) near d = 1
        ca, cb = math.sin((1.0 - t) * angle) / s, math.sin(t * angle) / s
        mixed = tuple(ca * a[k] + cb * b[k] for k in range(4))
    n = math.hypot(*mixed)                                  # already 1 to a few units in the last place: dividing removes those (measured: 5.6e-16 -> 4.4e-16)
    w, x, y, z = (c / n + 0.0 for c in mixed)
    return w, x, y, z


def slerp(q0: Sequence[float], q1: Sequence[float], t: float) -> Quaternion:
    a, b = _unit(q0, "q0"), _unit(q1, "q1")
    return _arc(a, b, _real(t, "t", 0.0, 1.0))


def interpolate(times: Sequence[float], quaternions: Sequence[Sequence[float]], t: float) -> Quaternion:
    if not isinstance(times, (list, tuple)) or not 2 <= len(times) <= MAX_ROWS:
        raise ValueError("times must be a list or tuple of 2 to 100000 numbers")
    ts = [_real(v, "a time", -BIG_TIME, BIG_TIME) for v in times]
    if any(b <= a for a, b in zip(ts, ts[1:])):
        raise ValueError("times must be strictly increasing")
    if not isinstance(quaternions, (list, tuple)) or len(quaternions) != len(ts):
        raise ValueError("quaternions must be a list or tuple with one quaternion for each time")
    rows = [_unit(q, "a quaternion of the table") for q in quaternions]
    at = _real(t, "t", ts[0], ts[-1])
    k = min(bisect.bisect_right(ts, at), len(ts) - 1) - 1    # the row at or before t; the last interval when t is the last time
    return _arc(rows[k], rows[k + 1], (at - ts[k]) / (ts[k + 1] - ts[k]))
