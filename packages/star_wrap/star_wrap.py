"""star_wrap - reducing, differencing and averaging angles (S.T.A.R., 2026-10-06). Standard library only.

  wrap360(deg)          the same angle in [0, 360)
  wrap180(deg)          the same angle in [-180, 180)
  difference(a, b)      a - b as the shortest signed rotation, in [-180, 180)
  circular_mean(angles) direction of the mean of the unit vectors, in [0, 360)
The reduction uses the exact floating-point remainder, so 1e9 deg loses nothing that it still had.
Half a turn is returned as -180 by wrap180 and difference (the convention of ERFA and astropy), never +180.
The mean of angles is undefined when their unit vectors cancel (two opposite directions, a full even spread):
circular_mean refuses that instead of returning the argument of rounding noise.
Refusals (ValueError): non-numeric, boolean or non-finite input, an angle beyond 1e12 deg in absolute value, an
empty or non-list/tuple collection or one longer than 1,000,000, a mean resultant length below 1e-9.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence

__all__ = ["wrap360", "wrap180", "difference", "circular_mean"]
__version__ = "0.1.0"

LIMIT = 1e12
MIN_RESULTANT = 1e-9
MAX_ITEMS = 1_000_000


def _deg(v, what: str = "angle") -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -LIMIT <= float(v) <= LIMIT          # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a real number within [-1e12, 1e12] deg")
    return float(v)


def _w360(d: float) -> float:
    r = math.fmod(d, 360.0)
    if r < 0.0:
        r += 360.0
    return 0.0 if r >= 360.0 else r + 0.0                   # -1e-20 + 360 rounds to 360; -0.0 becomes 0.0


def _w180(d: float) -> float:
    r = math.fmod(d, 360.0)
    if r >= 180.0:
        r -= 360.0
    elif r < -180.0:
        r += 360.0
    return r + 0.0


def wrap360(deg: float) -> float:
    return _w360(_deg(deg))


def wrap180(deg: float) -> float:
    return _w180(_deg(deg))


def difference(a: float, b: float) -> float:
    # reduce each angle first: the subtraction of two reduced angles is exact enough, that of two huge ones is not
    return _w180(_w360(_deg(a, "first angle")) - _w360(_deg(b, "second angle")))


def circular_mean(angles: Sequence[float]) -> float:
    if not isinstance(angles, (list, tuple)) or not 1 <= len(angles) <= MAX_ITEMS:
        raise ValueError("angles must be a non-empty list or tuple of at most 1,000,000 angles")
    rad = [math.radians(_w360(_deg(a))) for a in angles]
    s, c = math.fsum(math.sin(r) for r in rad), math.fsum(math.cos(r) for r in rad)
    if math.hypot(s, c) / len(rad) < MIN_RESULTANT:
        raise ValueError("the mean direction is undefined: the unit vectors cancel")
    return _w360(math.degrees(math.atan2(s, c)))
