"""star_twobody - the sizes and speeds of a Keplerian ellipse (S.T.A.R., 2026-10-06). Standard library only.

  period(a, mu=MU_EARTH)                          seconds, from the semi-major axis in km
  semi_major_axis_from_period(seconds, mu)        km
  mean_motion(a, mu)                              rad/s
  circular_speed(r, mu), escape_speed(r, mu)      km/s at distance r (km) from the centre
  apsides(a, e) -> (r_periapsis, r_apoapsis)      km
  elements_from_apsides(rp, ra) -> (a, e)
  apsis_speeds(a, e, mu) -> (v_periapsis, v_apoapsis)   km/s
  specific_energy(a, mu)                          km2/s2 (negative for an ellipse)
Units: km, s, km3/s2; any consistent set works if mu is given in it. The default mu is the Earth's, 398600.4418
km3/s2 (EGM96 / WGS-84). Two-body motion only: no J2, no drag, no third body.
Ellipses only: 0 <= e < 1; a parabola or a hyperbola is refused, not extrapolated.
Refusals (ValueError): non-numeric, boolean or non-finite input; a, r, a period or mu outside [1e-30, 1e30] (zero and
negative values included); e outside [0, 1); an apoapsis below the periapsis by more than rounding (1e-12 relative).
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["period", "semi_major_axis_from_period", "mean_motion", "circular_speed", "escape_speed", "apsides", "elements_from_apsides",
           "apsis_speeds", "specific_energy", "MU_EARTH"]
__version__ = "0.1.0"

MU_EARTH = 398600.4418
TINY, BIG = 1e-30, 1e30               # sixty orders of magnitude: beyond them the results overflow or underflow


def _positive(v, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and TINY <= float(v) <= BIG      # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [1e-30, 1e30]")
    return float(v)


def _ecc(e) -> float:
    try:
        ok = not isinstance(e, bool) and isinstance(e, numbers.Real) and 0.0 <= float(e) < 1.0
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("the eccentricity must be a real number within [0, 1): ellipses only")
    return float(e)


def period(a: float, mu: float = MU_EARTH) -> float:
    a, mu = _positive(a, "the semi-major axis"), _positive(mu, "mu")
    return 2.0 * math.pi * a * math.sqrt(a / mu)


def semi_major_axis_from_period(seconds: float, mu: float = MU_EARTH) -> float:
    t, mu = _positive(seconds, "the period"), _positive(mu, "mu")
    return (mu * (t / (2.0 * math.pi)) ** 2) ** (1.0 / 3.0)


def mean_motion(a: float, mu: float = MU_EARTH) -> float:
    a, mu = _positive(a, "the semi-major axis"), _positive(mu, "mu")
    return math.sqrt(mu / a) / a


def circular_speed(r: float, mu: float = MU_EARTH) -> float:
    r, mu = _positive(r, "the radius"), _positive(mu, "mu")
    return math.sqrt(mu / r)


def escape_speed(r: float, mu: float = MU_EARTH) -> float:
    r, mu = _positive(r, "the radius"), _positive(mu, "mu")
    return math.sqrt(2.0 * mu / r)


def apsides(a: float, e: float) -> Tuple[float, float]:
    a, e = _positive(a, "the semi-major axis"), _ecc(e)
    return a * (1.0 - e), a * (1.0 + e)


def elements_from_apsides(rp: float, ra: float) -> Tuple[float, float]:
    rp, ra = _positive(rp, "the periapsis radius"), _positive(ra, "the apoapsis radius")
    if ra < rp * (1.0 - 1e-12):
        raise ValueError("the apoapsis radius must not be smaller than the periapsis radius")
    return 0.5 * (rp + ra), max(0.0, (ra - rp) / (ra + rp))     # a circle whose two radii differ by rounding has e = 0


def apsis_speeds(a: float, e: float, mu: float = MU_EARTH) -> Tuple[float, float]:
    a, e, mu = _positive(a, "the semi-major axis"), _ecc(e), _positive(mu, "mu")
    v = math.sqrt(mu / a)
    k = math.sqrt((1.0 + e) / (1.0 - e))
    return v * k, v / k


def specific_energy(a: float, mu: float = MU_EARTH) -> float:
    a, mu = _positive(a, "the semi-major axis"), _positive(mu, "mu")
    return -0.5 * mu / a
