"""star_anomaly - mean, eccentric, hyperbolic and true anomaly, and Kepler's equation between them
(S.T.A.R., 2026-10-07). Standard library only.

Closed orbits (0 <= e < 1), angles in radians:
  eccentric_from_mean(M, e)     solves Kepler's equation E - e sin E = M
  mean_from_eccentric(E, e)     E - e sin E
  true_from_eccentric(E, e)     the true anomaly;  eccentric_from_true(nu, e) its inverse
  true_from_mean(M, e), mean_from_true(nu, e)
Open orbits (e > 1):
  hyperbolic_from_mean(M, e)    solves e sinh F - F = M
  mean_from_hyperbolic(F, e)    e sinh F - F
  true_from_hyperbolic(F, e)    the true anomaly, inside the asymptotes;  hyperbolic_from_true(nu, e) its inverse
The closed-orbit functions keep the revolution: an anomaly of 7 turns and a bit gives 7 turns and a bit (E - M and
nu - E are periodic and bounded), so nothing is wrapped and a propagation over many orbits stays continuous.

How: Kepler's equation by Newton's method kept inside a bracket that always contains the root (it cannot diverge,
whatever the eccentricity); the residual is formed as (1 - e) E + e (E - sin E), with E - sin E from its series near
zero, so that near-parabolic orbits close to periapsis do not lose their digits to cancellation. True and eccentric
anomaly are related through nu = E + 2 atan(b sin E / (1 - b cos E)), b = e / (1 + sqrt(1 - e^2)), which has no
quadrant to choose and no square root of a small difference.
Refusals (ValueError): a value that is not a finite real number (booleans refused); e outside [0, 1) for the
closed-orbit functions or not above 1 for the open ones (e = 1, the parabola, is not covered); an angle beyond 1e9
radians for a closed orbit; a mean or hyperbolic anomaly beyond 1e150 / 700 for an open one; a true anomaly at or
beyond the asymptote of an open orbit.
"""
from __future__ import annotations

import math
import numbers

__all__ = ["eccentric_from_mean", "mean_from_eccentric", "true_from_eccentric", "eccentric_from_true", "true_from_mean", "mean_from_true",
           "hyperbolic_from_mean", "mean_from_hyperbolic", "true_from_hyperbolic", "hyperbolic_from_true"]
__version__ = "0.1.0"

TWO_PI = 2.0 * math.pi
MAX_ANGLE = 1e9
MAX_HYPERBOLIC = 700.0
MAX_MEAN = 1e150


def _real(v, limit: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -limit <= float(v) <= limit        # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-{limit:g}, got {v!r}")
    return float(v)


def _closed(e) -> float:
    e = _real(e, 1e300, "e")
    if not 0.0 <= e < 1.0:
        raise ValueError(f"e must be in [0, 1) for a closed orbit, got {e!r}")
    return e


def _open(e) -> float:
    e = _real(e, 1e150, "e")
    if not e > 1.0:
        raise ValueError(f"e must be greater than 1 for an open orbit, got {e!r}")
    return e


def _x_minus_sin(x: float) -> float:
    """x - sin(x), by its series near zero where the subtraction would lose every digit."""
    if abs(x) >= 0.5:
        return x - math.sin(x)
    term = x * x * x / 6.0
    total, k, x2 = term, 3, x * x
    while True:
        k += 2
        term = -term * x2 / ((k - 1) * k)
        if total + term == total:
            return total
        total += term


def _sinh_minus_x(x: float) -> float:
    if abs(x) >= 0.5:
        return math.sinh(x) - x
    term = x * x * x / 6.0
    total, k, x2 = term, 3, x * x
    while True:
        k += 2
        term = term * x2 / ((k - 1) * k)
        if total + term == total:
            return total
        total += term


def _bracketed_newton(value, slope, low: float, high: float) -> float:
    """Root of an increasing function with value(low) <= 0 <= value(high), starting from high: Newton steps, bisection
    whenever one would leave the bracket. It ends when the bracket cannot shrink any more."""
    x = high
    while True:
        fx = value(x)
        if fx > 0.0:
            high = x
        elif fx < 0.0:
            low = x
        else:
            return x
        new = x - fx / slope(x)
        if not low < new < high:
            new = low + (high - low) / 2.0
            if not low < new < high:                         # low and high are neighbouring floats: nothing between them
                return x
        x = new


def mean_from_eccentric(E: float, e: float) -> float:
    return _mean_from_eccentric(_real(E, MAX_ANGLE, "E"), _closed(e))


def _mean_from_eccentric(E: float, e: float) -> float:
    if abs(E) < 0.5:                                         # near periapsis: no subtraction of nearly equal numbers
        return (1.0 - e) * E + e * _x_minus_sin(E)
    return E - e * math.sin(E)


def eccentric_from_mean(M: float, e: float) -> float:
    e = _closed(e)
    M = _real(M, MAX_ANGLE, "M")
    turns = round(M / TWO_PI)
    local = M - turns * TWO_PI                               # in [-pi, pi]
    target = abs(local)
    if target == 0.0:
        return M
    one_minus_e = 1.0 - e
    # the slope 1 - e cos x is written (1 - e) + 2 e sin^2(x / 2), which does not cancel for any x
    root = _bracketed_newton(lambda x: one_minus_e * x + e * _x_minus_sin(x) - target, lambda x: one_minus_e + 2.0 * e * math.sin(x / 2.0) ** 2,
                             target, min(math.pi, target + e))
    return turns * TWO_PI + math.copysign(root, local)


def _beta(e: float):
    """b = e / (1 + sqrt(1 - e^2)) and 1 - b, the second without subtracting two nearly equal numbers."""
    s = math.sqrt((1.0 - e) * (1.0 + e))
    return e / (1.0 + s), ((1.0 - e) + s) / (1.0 + s)


def true_from_eccentric(E: float, e: float) -> float:
    return _true_from_eccentric(_real(E, MAX_ANGLE, "E"), _closed(e))


def _true_from_eccentric(E: float, e: float) -> float:
    b, one_minus_b = _beta(e)
    # 1 - b cos E = (1 - b) + 2 b sin^2(E/2): no cancellation near periapsis of a very eccentric orbit
    return E + 2.0 * math.atan2(b * math.sin(E), one_minus_b + 2.0 * b * math.sin(E / 2.0) ** 2)


def eccentric_from_true(nu: float, e: float) -> float:
    return _eccentric_from_true(_real(nu, MAX_ANGLE, "nu"), _closed(e))


def _eccentric_from_true(nu: float, e: float) -> float:
    b, one_minus_b = _beta(e)
    return nu - 2.0 * math.atan2(b * math.sin(nu), one_minus_b + 2.0 * b * math.cos(nu / 2.0) ** 2)      # 1 + b cos(nu), the same way


def true_from_mean(M: float, e: float) -> float:
    # the intermediate anomaly may pass the limit of the inputs by a fraction of a turn: it is not an input
    return _true_from_eccentric(eccentric_from_mean(M, e), _closed(e))


def mean_from_true(nu: float, e: float) -> float:
    e = _closed(e)
    return _mean_from_eccentric(_eccentric_from_true(_real(nu, MAX_ANGLE, "nu"), e), e)


def mean_from_hyperbolic(F: float, e: float) -> float:
    e = _open(e)
    F = _real(F, MAX_HYPERBOLIC, "F")
    value = (e - 1.0) * F + e * _sinh_minus_x(F)
    if not math.isfinite(value):
        raise ValueError("the mean anomaly is too large for a float")
    return value


def hyperbolic_from_mean(M: float, e: float) -> float:
    e = _open(e)
    M = _real(M, MAX_MEAN, "M")
    target = abs(M)
    if target == 0.0:
        return M
    e_minus_one = e - 1.0
    # e sinh F - F >= (e - 1) sinh F, so the root is not above asinh(M / (e - 1)); the slope e cosh x - 1 written without cancellation
    root = _bracketed_newton(lambda x: e_minus_one * x + e * _sinh_minus_x(x) - target, lambda x: e_minus_one + 2.0 * e * math.sinh(x / 2.0) ** 2,
                             0.0, math.asinh(target / e_minus_one))
    return math.copysign(root, M)


def true_from_hyperbolic(F: float, e: float) -> float:
    e = _open(e)
    F = _real(F, MAX_HYPERBOLIC, "F")
    return 2.0 * math.atan(math.sqrt((e + 1.0) / (e - 1.0)) * math.tanh(F / 2.0))


def hyperbolic_from_true(nu: float, e: float) -> float:
    e = _open(e)
    nu = _real(nu, math.pi, "nu")
    ratio = math.sqrt((e - 1.0) / (e + 1.0)) * math.tan(nu / 2.0)
    if not abs(ratio) < 1.0:
        raise ValueError("the true anomaly is at or beyond the asymptote of this open orbit")
    return 2.0 * math.atanh(ratio)
