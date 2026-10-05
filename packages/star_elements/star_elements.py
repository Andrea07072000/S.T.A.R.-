# -*- coding: utf-8 -*-
"""star_elements — classical orbital elements <-> Cartesian state (Curtis, Orbital Mechanics for Engineering Students,
Algorithms 4.2 and 4.5). S.T.A.R., 2026-10-03. Standard library only. Units: km, km/s, km^3/s^2, radians.

Contract: elements are (h, e, i, raan, argp, nu) with h the specific angular momentum. Singular cases are explicit:
equatorial orbits (i = 0 or pi) have no RAAN and circular orbits no argument of periapsis; they raise ValueError
instead of returning an arbitrary angle that looks like a result.
"""
from __future__ import annotations

import math
from typing import Sequence, Tuple

MU_EARTH = 398600.4418  # km^3/s^2 (IERS Conventions 2010)
_EPS = 1e-10


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(_dot(a, a))


def rv_to_coe(r: Sequence[float], v: Sequence[float], mu: float = MU_EARTH) -> Tuple[float, ...]:
    """Curtis Algorithm 4.2. Returns (h, e, i, raan, argp, nu)."""
    # 2026-10-05 (probe of R3): non-finite r or v returned NaN/inf elements instead of refusing
    if not all(map(math.isfinite, (mu, *r, *v))):
        raise ValueError("inputs must be finite")
    if mu <= 0:
        raise ValueError("mu must be positive")
    R, V = _norm(r), _norm(v)
    if R == 0 or V == 0:
        raise ValueError("position and velocity must be non-zero")
    vr = _dot(r, v) / R
    hv = _cross(r, v)
    h = _norm(hv)
    if h < _EPS:
        raise ValueError("rectilinear trajectory (r parallel to v): elements undefined")
    i = math.acos(max(-1.0, min(1.0, hv[2] / h)))
    nv = (-hv[1], hv[0], 0.0)
    n = _norm(nv)
    ev = tuple(((V * V - mu / R) * r[k] - R * vr * v[k]) / mu for k in range(3))
    e = _norm(ev)
    if n < _EPS:
        raise ValueError("equatorial orbit: RAAN undefined")
    if e < _EPS:
        raise ValueError("circular orbit: argument of periapsis undefined")
    raan = math.acos(max(-1.0, min(1.0, nv[0] / n)))
    if nv[1] < 0:
        raan = 2 * math.pi - raan
    argp = math.acos(max(-1.0, min(1.0, _dot(nv, ev) / (n * e))))
    if ev[2] < 0:
        argp = 2 * math.pi - argp
    nu = math.acos(max(-1.0, min(1.0, _dot(ev, r) / (e * R))))
    if vr < 0:
        nu = 2 * math.pi - nu
    return h, e, i, raan, argp, nu


def coe_to_rv(h: float, e: float, i: float, raan: float, argp: float, nu: float, mu: float = MU_EARTH):
    """Curtis Algorithm 4.5. Returns (r, v) in the geocentric equatorial frame."""
    if not all(map(math.isfinite, (h, e, i, raan, argp, nu, mu))):
        raise ValueError("inputs must be finite")
    if h <= 0 or e < 0 or mu <= 0:
        raise ValueError("h and mu must be positive, e non-negative")
    if e >= 1 and 1 + e * math.cos(nu) <= 0:
        raise ValueError("true anomaly outside the hyperbola's asymptotes")
    rp = (h * h / mu) / (1 + e * math.cos(nu))
    r_pf = (rp * math.cos(nu), rp * math.sin(nu), 0.0)
    v_pf = (-mu / h * math.sin(nu), mu / h * (e + math.cos(nu)), 0.0)
    cO, sO, ci, si, cw, sw = math.cos(raan), math.sin(raan), math.cos(i), math.sin(i), math.cos(argp), math.sin(argp)
    Q = ((cO * cw - sO * sw * ci, -cO * sw - sO * ci * cw, sO * si),
         (sO * cw + cO * ci * sw, -sO * sw + cO * ci * cw, -cO * si),
         (si * sw, si * cw, ci))
    rot = lambda x: tuple(Q[k][0] * x[0] + Q[k][1] * x[1] + Q[k][2] * x[2] for k in range(3))
    return rot(r_pf), rot(v_pf)


# --- Anomaly conversions (elliptic orbits, 0 <= e < 1) ---------------------------------------------------------------

def _wrap(a: float) -> float:
    """Angle in [0, 2*pi). Plain `a % (2*pi)` returns exactly 2*pi for tiny negative a (found by mutation testing:
    mean_to_eccentric(0.0, 0.95) returned 6.283185307179586)."""
    w = a % (2 * math.pi)
    return 0.0 if w >= 2 * math.pi else w


def mean_to_eccentric(M: float, e: float, tol: float = 1e-14, max_iter: int = 50) -> float:
    """Solve Kepler's equation M = E - e sin E (Newton; starting guess per Vallado Alg. 2). Never returns an
    unconverged value: RuntimeError instead. Result in [0, 2*pi)."""
    if not 0 <= e < 1:
        raise ValueError("elliptic anomalies need 0 <= e < 1 (hyperbolic/parabolic not supported)")
    if not math.isfinite(M):  # was reported as "did not converge"
        raise ValueError("mean anomaly must be finite")
    M = M % (2 * math.pi)
    E = M + e if M < math.pi else M - e
    for _ in range(max_iter):
        f = E - e * math.sin(E) - M
        dE = -f / (1 - e * math.cos(E))
        E += dE
        if abs(dE) < tol:
            return _wrap(E)
    raise RuntimeError(f"Kepler equation did not converge (M={M}, e={e})")


def eccentric_to_true(E: float, e: float) -> float:
    if not 0 <= e < 1:
        raise ValueError("0 <= e < 1 required")
    if not math.isfinite(E):
        raise ValueError("eccentric anomaly must be finite")
    return _wrap(2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2)))


def true_to_eccentric(nu: float, e: float) -> float:
    if not 0 <= e < 1:
        raise ValueError("0 <= e < 1 required")
    if not math.isfinite(nu):
        raise ValueError("true anomaly must be finite")
    return _wrap(2 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2)))


def eccentric_to_mean(E: float, e: float) -> float:
    if not 0 <= e < 1:
        raise ValueError("0 <= e < 1 required")
    if not math.isfinite(E):
        raise ValueError("eccentric anomaly must be finite")
    return _wrap(E - e * math.sin(E))
