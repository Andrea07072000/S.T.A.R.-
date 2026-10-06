"""star_kepler - two-body (Kepler) propagation with universal variables (S.T.A.R., 2026-10-06). Standard library only.

propagate(r0, v0, tof, mu) -> (r, v): the state after `tof` seconds on the conic defined by (r0, v0).
Why it exists: the audit of five propagators (star_audit.propagation_audit, 2026-10-06) showed that composing
classical-element conversions refuses every circular or equatorial orbit (singular elements) and lost 0.44 m on one
ordinary case, and that one third-party solver never returns on NaN input. This solver:
  - has no orbit-geometry singularity (universal anomaly, Stumpff functions): circular, equatorial, elliptic, hyperbolic;
  - cannot loop forever: the root is bracketed (the universal Kepler function is strictly increasing, dF/dx = r > 0)
    and bisected a bounded number of times, with a Newton step taken only when it stays inside the bracket;
  - removes whole periods on closed orbits before solving, so long propagations do not lose precision;
  - refuses invalid input with ValueError (non-finite values, zero position, mu <= 0, rectilinear motion) and never
    returns an unconverged state (RuntimeError).
Units: any consistent set (km, km/s, s, km^3/s^2 with the default mu). Parabolic orbits (alpha = 0) are handled by the
same series; they are not separately validated.
"""
from __future__ import annotations

import math
from typing import Sequence, Tuple

MU_EARTH = 398600.4418
Vec = Tuple[float, float, float]
__all__ = ["propagate", "stumpff", "MU_EARTH"]
__version__ = "0.1.0"


def stumpff(z: float) -> Tuple[float, float]:
    """Stumpff functions (C(z), S(z)); a series near z = 0 avoids the 0/0 of the closed forms."""
    if z > 1e-6:
        s = math.sqrt(z)
        return (1.0 - math.cos(s)) / z, (s - math.sin(s)) / (s * s * s)
    if z < -1e-6:
        s = math.sqrt(-z)
        return (math.cosh(s) - 1.0) / -z, (math.sinh(s) - s) / (s * s * s)
    return 0.5 - z / 24.0 + z * z / 720.0, 1.0 / 6.0 - z / 120.0 + z * z / 5040.0


def propagate(r0: Sequence[float], v0: Sequence[float], tof: float, mu: float = MU_EARTH,
              max_iter: int = 400) -> Tuple[Vec, Vec]:
    if len(r0) != 3 or len(v0) != 3:
        raise ValueError("r0 and v0 must have 3 components")
    if not all(map(math.isfinite, (tof, mu, *r0, *v0))):
        raise ValueError("inputs must be finite")
    if mu <= 0:
        raise ValueError("mu must be positive")
    R = math.sqrt(r0[0] * r0[0] + r0[1] * r0[1] + r0[2] * r0[2])
    if R == 0.0:
        raise ValueError("position is the attracting centre")
    v2 = v0[0] * v0[0] + v0[1] * v0[1] + v0[2] * v0[2]
    rv = r0[0] * v0[0] + r0[1] * v0[1] + r0[2] * v0[2]
    # |h|^2 = R^2 v^2 - (r.v)^2 (Lagrange). A relative threshold, not "== 0": parallel vectors in a general direction
    # give a rounding-size h, not an exact zero (2026-10-06, from the mutation survivors of the first version)
    if R * R * v2 - rv * rv <= 1e-12 * R * R * v2:
        raise ValueError("rectilinear motion (zero angular momentum) is not supported")
    alpha = 2.0 / R - v2 / mu                          # 1/a: > 0 ellipse, < 0 hyperbola
    sm = math.sqrt(mu)
    dt = tof
    if alpha > 0.0:                                    # closed orbit: the state repeats every period
        period = 2.0 * math.pi / (sm * alpha ** 1.5)
        dt = math.fmod(tof, period)
    if dt == 0.0:
        return (r0[0], r0[1], r0[2]), (v0[0], v0[1], v0[2])

    def F(x):
        C, S = stumpff(alpha * x * x)
        return rv / sm * x * x * C + (1.0 - alpha * R) * x * x * x * S + R * x - sm * dt

    sign = 1.0 if dt > 0 else -1.0
    lo, hi = 0.0, sign * max(1.0, sm * abs(dt) / R)    # F(0) = -sm dt; F is strictly increasing in x
    for _ in range(200):
        if F(hi) * sign >= 0.0:
            break
        hi *= 2.0          # lo stays at 0: on a circular orbit the first guess IS the root, and a root sitting on
        #                    the bracket edge made every Newton step be rejected (43 iterations, 2026-10-06)
    else:
        raise RuntimeError("universal anomaly could not be bracketed")
    if lo > hi:
        lo, hi = hi, lo
    x = 0.5 * (lo + hi)
    for _ in range(max_iter):
        f = F(x)
        if f == 0.0:                                   # exact root: a Newton step of 0 would sit on the bracket edge
            break
        if f < 0.0:
            lo = x
        else:
            hi = x
        C, S = stumpff(alpha * x * x)
        dF = rv / sm * x * (1.0 - alpha * x * x * S) + (1.0 - alpha * R) * x * x * C + R     # = r(x) > 0
        new = x - f / dF if dF > 0.0 else 0.5 * (lo + hi)
        if not lo <= new <= hi:      # closed interval: on a circular orbit the first bound IS the root (traced
            new = 0.5 * (lo + hi)    # 2026-10-06: a strict test rejected the exact root 43 times in a row)
        # stop when the Newton step reaches the rounding noise of F (about 1e-13 relative in x). Waiting for the
        # bracket to close, or for a step below 4e-16, took 57-58 iterations on the audit corpus (2026-10-06)
        if abs(new - x) <= 1e-13 * max(1.0, abs(x)) or hi - lo <= 4e-16 * max(1.0, abs(x)):
            x = new
            break
        x = new
    else:
        raise RuntimeError("universal Kepler equation did not converge")
    C, S = stumpff(alpha * x * x)
    f = 1.0 - x * x / R * C
    g = dt - x * x * x / sm * S
    r = (f * r0[0] + g * v0[0], f * r0[1] + g * v0[1], f * r0[2] + g * v0[2])
    Rn = math.sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2])
    fd = sm / (Rn * R) * x * (alpha * x * x * S - 1.0)
    gd = 1.0 - x * x / Rn * C
    v = (fd * r0[0] + gd * v0[0], fd * r0[1] + gd * v0[1], fd * r0[2] + gd * v0[2])
    return r, v
