"""star_gasdynamics - isentropic flow and normal shock of a perfect gas (S.T.A.R., 2026-10-06). Standard library only.

  isentropic(mach, gamma=1.4) -> (T/T0, p/p0, rho/rho0, A/A*)      static over stagnation; area over throat area
  mach_from_area_ratio(area_ratio, gamma=1.4, supersonic=True) -> Mach number on the chosen branch
  normal_shock(mach1, gamma=1.4) -> (M2, p2/p1, rho2/rho1, T2/T1, p02/p01)
The gas is calorically perfect (constant ratio of specific heats gamma): the textbook relations of NACA Report 1135.
A/A* is infinite at Mach 0: isentropic(0) returns math.inf there, and 1 for the other three ratios.
The inverse of the area ratio is found by bisection on the branch asked for (the function is monotonic on each),
to the last bit; an area ratio of exactly 1 is Mach 1 on both branches.
Refusals (ValueError): non-numeric, boolean or non-finite input; Mach outside [0, 50] (shock: [1, 50]); gamma outside
[1.01, 3]; an area ratio below 1 or above the one of Mach 50 (supersonic) or of Mach 1e-6 (subsonic); `supersonic`
not a bool.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["isentropic", "mach_from_area_ratio", "normal_shock"]
__version__ = "0.1.0"

MACH_MAX = 50.0
MACH_MIN_SUBSONIC = 1e-6
GAMMA_MIN, GAMMA_MAX = 1.01, 3.0


def _real(v, lo: float, hi: float, what: str) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and lo <= float(v) <= hi       # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [{lo:g}, {hi:g}]")
    return float(v)


def _area(m: float, g: float) -> float:
    """A/A* for Mach m > 0."""
    return ((2.0 + (g - 1.0) * m * m) / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0))) / m


def isentropic(mach: float, gamma: float = 1.4) -> Tuple[float, float, float, float]:
    m, g = _real(mach, 0.0, MACH_MAX, "Mach number"), _real(gamma, GAMMA_MIN, GAMMA_MAX, "gamma")
    t = 1.0 / (1.0 + 0.5 * (g - 1.0) * m * m)
    return t, t ** (g / (g - 1.0)), t ** (1.0 / (g - 1.0)), (_area(m, g) if m > 0.0 else math.inf)


def mach_from_area_ratio(area_ratio: float, gamma: float = 1.4, supersonic: bool = True) -> float:
    g = _real(gamma, GAMMA_MIN, GAMMA_MAX, "gamma")
    if not isinstance(supersonic, bool):
        raise ValueError("supersonic must be True or False")
    lo, hi = (1.0, MACH_MAX) if supersonic else (MACH_MIN_SUBSONIC, 1.0)
    far = MACH_MAX if supersonic else MACH_MIN_SUBSONIC
    ratio = _real(area_ratio, 1.0, _area(far, g), "area ratio")
    if ratio == 1.0:
        return 1.0
    for _ in range(200):                                    # A/A* decreases to 1 at Mach 1 and increases beyond it
        mid = 0.5 * (lo + hi)
        if mid == lo or mid == hi:
            break
        if (_area(mid, g) < ratio) == supersonic:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def normal_shock(mach1: float, gamma: float = 1.4) -> Tuple[float, float, float, float, float]:
    m, g = _real(mach1, 1.0, MACH_MAX, "upstream Mach number"), _real(gamma, GAMMA_MIN, GAMMA_MAX, "gamma")
    m2 = m * m
    p = 1.0 + 2.0 * g / (g + 1.0) * (m2 - 1.0)
    rho = (g + 1.0) * m2 / ((g - 1.0) * m2 + 2.0)
    mach2 = math.sqrt(((g - 1.0) * m2 + 2.0) / (2.0 * g * m2 - (g - 1.0)))
    # in logarithms: for gamma near 1 the two powers are 1e+230 and 1e-340 and their product underflowed to 0
    p0 = math.exp((g * math.log(rho) - math.log(p)) / (g - 1.0))
    return mach2, p, rho, p / rho, p0
