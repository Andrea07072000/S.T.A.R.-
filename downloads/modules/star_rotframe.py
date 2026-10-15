"""star_rotframe - position and velocity between an inertial frame and a frame rotating about z (S.T.A.R., 2026-10-07).
Standard library only.

  to_rotating(r, v, angle, rate=EARTH_RATE)   state in the rotating frame from the state in the inertial frame
  to_inertial(r, v, angle, rate=EARTH_RATE)   the inverse
`angle` (radians) is the angle of the rotating x axis from the inertial x axis, counted about +z; `rate` (rad/s) is its
time derivative. For the Earth, with the Earth Rotation Angle or sidereal time as `angle`, this is the step between an
Earth-centred inertial frame and the Earth-fixed frame when polar motion, precession and nutation are left out.
    r' = Rz(angle) r                  x' =  x cos(angle) + y sin(angle),  y' = -x sin(angle) + y cos(angle),  z' = z
    v' = Rz(angle) v - w x r'         with w = (0, 0, rate): the velocity SEEN in the rotating frame
The velocity term is what is most often forgotten: a point fixed on the equator has an inertial speed of 465 m/s and
a rotating-frame speed of zero. Units: any consistent pair (km and km/s, m and m/s); time in seconds if EARTH_RATE is used.
Refusals (ValueError): r or v that is not a list or tuple of 3 finite real numbers within +-1e15; an angle that is not
a finite real number within +-1e9 rad; a rate that is not finite or exceeds 1000 rad/s in size; booleans everywhere.
"""
from __future__ import annotations

import math
import numbers
from typing import Sequence, Tuple

__all__ = ["to_rotating", "to_inertial", "EARTH_RATE"]
__version__ = "0.1.0"

EARTH_RATE = 7.292115e-5                                    # rad/s, WGS-84 defining value of the Earth's angular velocity
BIG = 1e15
MAX_ANGLE = 1e9
MAX_RATE = 1000.0

Vector = Tuple[float, float, float]


def _real(v, what: str, limit: float) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -limit <= float(v) <= limit     # NaN fails the comparison
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError(f"{what} must be a finite real number within +-{limit:g}")
    return float(v)


def _vector(v, what: str) -> Vector:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"{what} must be a list or tuple of 3 numbers")
    return _real(v[0], f"a component of {what}", BIG), _real(v[1], f"a component of {what}", BIG), _real(v[2], f"a component of {what}", BIG)


def _turn(vec: Vector, c: float, s: float) -> Vector:
    """Components of the same vector in a frame turned by the angle whose cosine and sine are c and s, about +z."""
    return c * vec[0] + s * vec[1] + 0.0, c * vec[1] - s * vec[0] + 0.0, vec[2] + 0.0


def to_rotating(r: Sequence[float], v: Sequence[float], angle: float, rate: float = EARTH_RATE) -> Tuple[Vector, Vector]:
    pos, vel = _vector(r, "r"), _vector(v, "v")
    a, w = _real(angle, "angle", MAX_ANGLE), _real(rate, "rate", MAX_RATE)
    c, s = math.cos(a), math.sin(a)
    rr, vv = _turn(pos, c, s), _turn(vel, c, s)
    return rr, (vv[0] + w * rr[1], vv[1] - w * rr[0], vv[2])       # minus w x r', with w along +z: (-w y', w x', 0)


def to_inertial(r: Sequence[float], v: Sequence[float], angle: float, rate: float = EARTH_RATE) -> Tuple[Vector, Vector]:
    pos, vel = _vector(r, "r"), _vector(v, "v")
    a, w = _real(angle, "angle", MAX_ANGLE), _real(rate, "rate", MAX_RATE)
    c, s = math.cos(a), math.sin(a)
    carried = (vel[0] - w * pos[1], vel[1] + w * pos[0], vel[2])               # plus w x r', still in rotating components
    return _turn(pos, c, -s), _turn(carried, c, -s)
