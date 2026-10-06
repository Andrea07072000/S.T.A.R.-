"""star_sigma - what "n sigma" means in one, two and three dimensions (S.T.A.R., 2026-10-06). Standard library only.

  normal_cdf(z), normal_sf(z)            probability below / above z for the standard normal distribution
  normal_quantile(p)                     the z with normal_cdf(z) == p
  sigma_coverage(n_sigma, dims=1)        probability that a Gaussian error falls WITHIN n sigma: an interval (dims 1), the
                                         n-sigma ellipse (2) or the n-sigma ellipsoid (3)
  sigma_tail(n_sigma, dims=1)            probability that it falls OUTSIDE (computed directly: 5 sigma keeps its digits)
  sigma_for_coverage(p, dims=1)          the n with sigma_coverage(n, dims) == p
The same "3 sigma" is 99.73 % on a line, 98.89 % for a covariance ellipse and 97.07 % for a covariance ellipsoid:
the squared Mahalanobis distance of a Gaussian vector follows the chi-square law with dims degrees of freedom, and
sigma_coverage(n, dims) is its distribution function at n squared.
Closed forms: dims 1: erf(n / sqrt 2); dims 2: 1 - exp(-n^2 / 2); dims 3: erf(n / sqrt 2) - sqrt(2 / pi) n exp(-n^2 / 2)
(a series replaces the last one for small n, where it cancels). The inverses are found by bisection, to the last bit.
Refusals (ValueError): non-numeric, boolean or non-finite input; z outside [-38, 38]; n_sigma outside [0, 38]; a
probability outside (0, 1) for normal_quantile and outside [0, 1) for sigma_for_coverage; dims not the integer 1, 2 or 3.
"""
from __future__ import annotations

import math
import numbers

__all__ = ["normal_cdf", "normal_sf", "normal_quantile", "sigma_coverage", "sigma_tail", "sigma_for_coverage"]
__version__ = "0.1.0"

Z_MAX = 38.0
SQRT2 = math.sqrt(2.0)
SERIES_BELOW = 1.0                      # dims 3: below this n the closed form cancels and the series is used


def _real(v, lo: float, hi: float, what: str, open_lo: bool = False, open_hi: bool = False) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and (lo < float(v) if open_lo else lo <= float(v)) \
            and (float(v) < hi if open_hi else float(v) <= hi)                                    # NaN fails the comparisons
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within {'(' if open_lo else '['}{lo:g}, {hi:g}{')' if open_hi else ']'}")
    return float(v)


def _dims(dims) -> int:
    if isinstance(dims, bool) or not isinstance(dims, numbers.Integral) or int(dims) not in (1, 2, 3):
        raise ValueError("dims must be the integer 1, 2 or 3")
    return int(dims)


def normal_cdf(z: float) -> float:
    return 0.5 * math.erfc(-_real(z, -Z_MAX, Z_MAX, "z") / SQRT2)


def normal_sf(z: float) -> float:
    return 0.5 * math.erfc(_real(z, -Z_MAX, Z_MAX, "z") / SQRT2)


def _bisect(f, target: float, lo: float, hi: float) -> float:
    """Root of the increasing function f(x) = target on [lo, hi], to the last bit."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid == lo or mid == hi:
            break
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def normal_quantile(p: float) -> float:
    p = _real(p, 0.0, 1.0, "p", open_lo=True, open_hi=True)
    if p == 0.5:
        return 0.0
    if p > 0.5:                                             # work in the tail that keeps its digits
        return _bisect(lambda z: -0.5 * math.erfc(z / SQRT2), -(1.0 - p), 0.0, Z_MAX)
    return _bisect(lambda z: 0.5 * math.erfc(-z / SQRT2), p, -Z_MAX, 0.0)


def _coverage(n: float, dims: int) -> float:
    t = 0.5 * n * n
    if dims == 1:
        return math.erf(n / SQRT2)
    if dims == 2:
        return -math.expm1(-t)
    if n < SERIES_BELOW:                                    # P(3/2, t) = t^(3/2) e^(-t) sum t^k / Gamma(5/2 + k)
        term = total = 1.0 / math.gamma(2.5)
        k = 0
        while term > 1e-18 * total:
            k += 1
            term *= t / (1.5 + k)
            total += term
        return t ** 1.5 * math.exp(-t) * total
    return math.erf(n / SQRT2) - math.sqrt(2.0 / math.pi) * n * math.exp(-t)


def sigma_coverage(n_sigma: float, dims: int = 1) -> float:
    return _coverage(_real(n_sigma, 0.0, Z_MAX, "n_sigma"), _dims(dims))


def sigma_tail(n_sigma: float, dims: int = 1) -> float:
    n, d = _real(n_sigma, 0.0, Z_MAX, "n_sigma"), _dims(dims)
    t = 0.5 * n * n
    if d == 1:
        return math.erfc(n / SQRT2)
    if d == 2:
        return math.exp(-t)
    return math.erfc(n / SQRT2) + math.sqrt(2.0 / math.pi) * n * math.exp(-t)


def sigma_for_coverage(p: float, dims: int = 1) -> float:
    p, d = _real(p, 0.0, 1.0, "p", open_hi=True), _dims(dims)
    if p == 0.0:
        return 0.0
    if p > 0.5:                                             # the tail keeps its digits where the coverage is close to 1
        tail = 1.0 - p
        return _bisect(lambda n: -sigma_tail(n, d), -tail, 0.0, Z_MAX)
    return _bisect(lambda n: _coverage(n, d), p, 0.0, Z_MAX)
