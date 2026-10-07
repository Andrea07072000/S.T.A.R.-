"""star_doppler - range, range rate and one-way Doppler shift between two states (S.T.A.R., 2026-10-07).
Standard library only.

  range_and_rate(r_observer, v_observer, r_target, v_target)   distance and its rate of change: (range, range_rate)
  received_frequency(frequency, range_rate, relativistic=True) frequency received over a link whose length changes at range_rate
  C_KM_S                                                       speed of light, 299792.458 km/s (exact, SI definition)
The range is |r_target - r_observer| and the range rate is the component of the relative velocity along the line of
sight, (dr . dv) / |dr|: positive when the two move apart. Positions and velocities must be in the same frame and
units (km and km/s if C_KM_S is used for the frequency).
The received frequency for a source receding at range_rate is, with b = range_rate / c:
    relativistic=True   f sqrt((1 - b) / (1 + b))     exact for motion along the line of sight
    relativistic=False  f (1 - b)                     the first-order formula of link budgets (the "radio" convention)
A positive range rate lowers the frequency. The two differ by b^2 / 2: 3 parts in 1e10 at 7.5 km/s.
Refusals (ValueError): a vector that is not a list or tuple of 3 finite real numbers within +-1e15; coincident
positions (the line of sight is not defined); a frequency that is not a finite positive number up to 1e30; a range rate
that is not finite or reaches the speed of light; `relativistic` not a bool. Booleans are refused as numbers.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["range_and_rate", "received_frequency", "C_KM_S"]
__version__ = "0.1.0"

C_KM_S = 299792.458
BIG = 1e15
MAX_FREQUENCY = 1e30


def _real(v, what: str, limit: float) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -limit <= float(v) <= limit     # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-{limit:g}")
    return float(v)


def _vector(v, what: str) -> Tuple[float, float, float]:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"{what} must be a list or tuple of 3 numbers")
    return _real(v[0], f"a component of {what}", BIG), _real(v[1], f"a component of {what}", BIG), _real(v[2], f"a component of {what}", BIG)


def range_and_rate(r_observer: Sequence[float], v_observer: Sequence[float], r_target: Sequence[float], v_target: Sequence[float]) -> Tuple[float, float]:
    ro, vo, rt, vt = _vector(r_observer, "r_observer"), _vector(v_observer, "v_observer"), _vector(r_target, "r_target"), _vector(v_target, "v_target")
    dr = (rt[0] - ro[0], rt[1] - ro[1], rt[2] - ro[2])
    dv = (vt[0] - vo[0], vt[1] - vo[1], vt[2] - vo[2])
    distance = math.hypot(*dr)
    if distance == 0.0:
        raise ValueError("the two positions coincide: the line of sight is not defined")
    # the unit vector first: dividing each component by the distance cannot overflow, a dot product of 1e15-sized numbers could not either
    rate = math.fsum((dr[0] / distance * dv[0], dr[1] / distance * dv[1], dr[2] / distance * dv[2]))
    return distance, rate + 0.0


def received_frequency(frequency: float, range_rate: float, relativistic: bool = True) -> float:
    f = _real(frequency, "frequency", MAX_FREQUENCY)
    if f <= 0.0:
        raise ValueError("frequency must be positive")
    if not isinstance(relativistic, bool):
        raise ValueError("relativistic must be True or False")
    b = _real(range_rate, "range_rate", BIG) / C_KM_S
    if abs(b) >= 1.0:
        raise ValueError("range_rate must be smaller than the speed of light (299792.458 km/s)")
    return f * math.sqrt((1.0 - b) / (1.0 + b)) if relativistic else f * (1.0 - b)
