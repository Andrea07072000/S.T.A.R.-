"""star_cw - relative motion near a circular orbit: Clohessy-Wiltshire (Hill) equations (S.T.A.R., 2026-10-06).
Standard library only.

Frame (rotating with the chief, origin at the chief): x radial outward, y along the velocity, z along the orbit
normal. State = (x, y, z, vx, vy, vz) of the deputy, velocities relative to the rotating frame. n = mean motion of
the chief in rad/s. Any consistent length unit.
  stm(n, t)                 -> 6x6 state transition matrix (closed form)
  propagate(state, n, t)    -> state after t seconds of free drift
  rendezvous(r0, v0, rf, n, t) -> (dv1, dv2): impulse now to reach rf after t, and impulse there to stop relative to
                               the target point (rf is a point of the rotating frame, e.g. the origin = the chief)
Model limits: chief on a CIRCULAR Keplerian orbit, separation small against the orbit radius (the neglected terms
grow as separation squared over radius; measured against full two-body motion in crosscheck_cw.py), no perturbation.
Refusals (ValueError): non-numeric, boolean or non-finite input, wrong shapes, n <= 0, and for rendezvous a transfer
time where the problem is singular (t = 0, whole revolutions, and the other roots of 8(1 - cos nt) = 3 nt sin nt for
the in-plane part; half revolutions for the out-of-plane part) - there no finite impulse reaches an arbitrary point.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["stm", "propagate", "rendezvous"]
__version__ = "0.1.0"
SINGULAR_TOL = 1e-9
Vec = Tuple[float, float, float]


def _num(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e150 < float(v) < 1e150      # NaN fails both
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number (magnitude below 1e150)")
    return float(v)


def _seq(v, n: int, what: str) -> tuple:
    try:
        ok = not isinstance(v, (str, bytes, dict, set, frozenset)) and len(v) == n
        items = tuple(v[i] for i in range(n)) if ok else ()
    except (TypeError, KeyError, IndexError):
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a sequence of {n} numbers")
    return tuple(_num(x, what) for x in items)


def _rate(n) -> float:
    n = _num(n, "mean motion")
    if n <= 0.0:
        raise ValueError("mean motion must be positive")
    return n


def _blocks(n: float, t: float):
    """The four 3x3 blocks of the transition matrix: position/velocity at t from position/velocity at 0."""
    th = n * t
    s, c = math.sin(th), math.cos(th)
    one_c = 2.0 * math.sin(th / 2.0) ** 2                       # 1 - cos, without cancellation for small angles
    rr = ((4.0 - 3.0 * c, 0.0, 0.0), (6.0 * (s - th), 1.0, 0.0), (0.0, 0.0, c))
    rv = ((s / n, 2.0 * one_c / n, 0.0), (-2.0 * one_c / n, (4.0 * s - 3.0 * th) / n, 0.0), (0.0, 0.0, s / n))
    vr = ((3.0 * n * s, 0.0, 0.0), (-6.0 * n * one_c, 0.0, 0.0), (0.0, 0.0, -n * s))
    vv = ((c, 2.0 * s, 0.0), (-2.0 * s, 4.0 * c - 3.0, 0.0), (0.0, 0.0, c))
    return rr, rv, vr, vv


def _finite(values):
    values = tuple(values)             # 2026-10-06: a generator was consumed by the check and an EMPTY tuple came back
    if not all(map(math.isfinite, values)):
        raise ValueError("result out of range")
    return values


def stm(n: float, t: float) -> Tuple[Tuple[float, ...], ...]:
    """6x6 matrix M with state(t) = M state(0)."""
    rr, rv, vr, vv = _blocks(_rate(n), _num(t, "time"))
    rows = [rr[i] + rv[i] for i in range(3)] + [vr[i] + vv[i] for i in range(3)]
    return tuple(_finite(r) for r in rows)


def propagate(state: Sequence[float], n: float, t: float) -> Tuple[float, ...]:
    """Relative state after t seconds without thrust."""
    y = _seq(state, 6, "state")
    m = stm(n, t)
    return _finite(sum(m[i][j] * y[j] for j in range(6)) for i in range(6))


def rendezvous(r0: Sequence[float], v0: Sequence[float], rf: Sequence[float], n: float, t: float) -> Tuple[Vec, Vec]:
    """Two impulses: dv1 applied now so that the deputy is at rf after t; dv2 applied there to stay at rf."""
    r0, v0, rf = _seq(r0, 3, "r0"), _seq(v0, 3, "v0"), _seq(rf, 3, "rf")
    n, t = _rate(n), _num(t, "time")
    if t <= 0.0:
        raise ValueError("transfer time must be positive")
    rr, rv, vr, vv = _blocks(n, t)
    th = n * t
    det = (rv[0][0] * rv[1][1] - rv[0][1] * rv[1][0]) * n * n          # = 8 (1 - cos) - 3 nt sin, dimensionless
    if abs(det) < SINGULAR_TOL * max(1.0, th * th) or abs(math.sin(th)) < SINGULAR_TOL:
        raise ValueError("singular transfer time: no finite impulse reaches an arbitrary point at this time")
    need = [rf[i] - sum(rr[i][j] * r0[j] for j in range(3)) for i in range(3)]      # what the velocity must contribute
    inv = n * n / det
    vx = inv * (rv[1][1] * need[0] - rv[0][1] * need[1])
    vy = inv * (-rv[1][0] * need[0] + rv[0][0] * need[1])
    vz = need[2] / rv[2][2]
    v_needed = (vx, vy, vz)
    arrive = [sum(vr[i][j] * r0[j] + vv[i][j] * v_needed[j] for j in range(3)) for i in range(3)]
    return _finite(v_needed[i] - v0[i] for i in range(3)), _finite(-a for a in arrive)
