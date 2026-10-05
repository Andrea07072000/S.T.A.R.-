# -*- coding: utf-8 -*-
"""star_lambert — Lambert's problem, zero revolutions, universal variables (Bate-Mueller-White / Curtis Alg. 5.2).

S.T.A.R., Claude Code, 2026-10-03. Standard library only. Lineage: universal-variable formulation with Stumpff
functions and Newton iteration on z — a DIFFERENT lineage from Izzo's algorithm (hapsira/poliastro), which is the
independent oracle used in the cross-check campaign XC-006.
Contract: never return an unconverged result — RuntimeError instead (a degraded result must not look like success).
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

MU_EARTH = 398600.4418  # km^3/s^2


def _stumpff_c(z: float) -> float:
    if z > 1e-8:
        return (1 - math.cos(math.sqrt(z))) / z
    if z < -1e-8:
        return (math.cosh(math.sqrt(-z)) - 1) / (-z)
    return 0.5 - z / 24 + z * z / 720


def _stumpff_s(z: float) -> float:
    if z > 1e-8:
        sz = math.sqrt(z)
        return (sz - math.sin(sz)) / sz ** 3
    if z < -1e-8:
        sz = math.sqrt(-z)
        return (math.sinh(sz) - sz) / sz ** 3
    return 1 / 6 - z / 120 + z * z / 5040


def _norm(v):
    return math.sqrt(sum(x * x for x in v))


def _universal_functions(r1n: float, r2n: float, A: float, mu: float, tof: float):
    """y(z), F(z) and dF/dz of the universal-variable Lambert formulation (Curtis Alg. 5.2), exposed so that the
    derivative can be tested against a numerical derivative (mutation testing showed it was untested)."""
    def y(z):
        return r1n + r2n + A * (z * _stumpff_s(z) - 1) / math.sqrt(_stumpff_c(z))

    def F(z):
        yz = y(z)
        return (yz / _stumpff_c(z)) ** 1.5 * _stumpff_s(z) + A * math.sqrt(yz) - math.sqrt(mu) * tof

    def dF(z):
        if abs(z) < 1e-8:
            y0 = y(0.0)
            return math.sqrt(2) / 40 * y0 ** 1.5 + A / 8 * (math.sqrt(y0) + A * math.sqrt(1 / (2 * y0)))
        C, S, yz = _stumpff_c(z), _stumpff_s(z), y(z)
        return ((yz / C) ** 1.5 * (1 / (2 * z) * (C - 1.5 * S / C) + 0.75 * S * S / C)
                + A / 8 * (3 * S / C * math.sqrt(yz) + A * math.sqrt(C / yz)))

    return y, F, dF


def lambert(r1: Sequence[float], r2: Sequence[float], tof: float, mu: float = MU_EARTH, prograde: bool = True,
            tol: float = 1e-10, max_iter: int = 200) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    if tof <= 0:
        raise ValueError("time of flight must be positive")
    r1n, r2n = _norm(r1), _norm(r2)
    if r1n == 0 or r2n == 0:
        raise ValueError("position vectors must be non-zero")
    cz = r1[0] * r2[1] - r1[1] * r2[0]
    cos_dnu = max(-1.0, min(1.0, sum(a * b for a, b in zip(r1, r2)) / (r1n * r2n)))
    dnu = math.acos(cos_dnu)
    if (prograde and cz < 0) or (not prograde and cz >= 0):
        dnu = 2 * math.pi - dnu
    A = math.sin(dnu) * math.sqrt(r1n * r2n / (1 - math.cos(dnu)))
    if abs(A) < 1e-12:
        raise ValueError("degenerate geometry (transfer angle 0 or 180 deg)")

    y, F, dF = _universal_functions(r1n, r2n, A, mu, tof)

    # Bracket (Curtis Alg. 5.2 march), guarded: F(z) needs sqrt(y(z)), so first move into y(z) > 0, then until F >= 0.
    # (first version evaluated F with y < 0 -> math domain error; found by the published-value test)
    z = -100.0
    while y(z) < 0 or F(z) < 0:
        z += 0.1
        if z > 4 * math.pi ** 2:
            raise RuntimeError("no zero-revolution solution bracket found")
    for _ in range(max_iter):
        step = F(z) / dF(z)
        z -= step
        if y(z) < 0:
            raise RuntimeError("iteration left the physical domain (y < 0)")
        if abs(step) < tol:
            break
    else:
        raise RuntimeError("Lambert iteration did not converge")
    yz = y(z)
    f = 1 - yz / r1n
    g = A * math.sqrt(yz / mu)
    gdot = 1 - yz / r2n
    v1 = tuple((r2[i] - f * r1[i]) / g for i in range(3))
    v2 = tuple((gdot * r2[i] - r1[i]) / g for i in range(3))
    return v1, v2
