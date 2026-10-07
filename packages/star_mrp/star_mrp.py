"""star_mrp - modified Rodrigues parameters: the three-number attitude set of spacecraft control laws
(S.T.A.R., 2026-10-07). Standard library only.

  mrp_from_quaternion(q)             sigma = v / (1 + w) for the unit quaternion (w, x, y, z), on the short rotation
  quaternion_from_mrp(s)             back, with w >= 0
  shadow(s)                          the other MRP of the same attitude, -sigma / |sigma|^2
  switch(s, threshold=1.0)           sigma, or its shadow when |sigma| > threshold
  compose(first, second)             the MRP of the rotation `first` followed by `second`, on the short rotation
  dcm_from_mrp(s)                    the direction cosine matrix C (reference to body: v_body = C v_reference)
  rotation_vector_from_mrp(s)        principal axis times principal angle (radians), angle in [0, pi]
  mrp_from_rotation_vector(v)        back; any angle
  mrp_rate(s, omega)                 d(sigma)/dt for the body angular velocity omega (rad/s, body frame)
Definition (Schaub and Junkins, Analytical Mechanics of Space Systems): sigma = e tan(phi / 4), e the principal axis
and phi the principal angle. |sigma| <= 1 is a rotation of at most 180 degrees; beyond, the shadow set describes the
same attitude with a smaller norm. The set is singular only at a full turn of 360 degrees, which the shadow set avoids.
Conventions: quaternions scalar first; C takes reference to body; composing C(second) C(first).
Refusals (ValueError): a vector that is not three (or four, for a quaternion) finite real numbers within 1e150 in
absolute value (booleans refused); a zero quaternion; the shadow of the zero MRP (it is at infinity); a threshold
that is not positive.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["mrp_from_quaternion", "quaternion_from_mrp", "shadow", "switch", "compose", "dcm_from_mrp", "rotation_vector_from_mrp",
           "mrp_from_rotation_vector", "mrp_rate"]
__version__ = "0.1.0"

BIG = 1e150
Vector = Tuple[float, float, float]


def _seq(v, n: int, what: str) -> Tuple[float, ...]:
    if not isinstance(v, (list, tuple)) or len(v) != n:
        raise ValueError(f"{what} must be a list or tuple of {n} numbers")
    out = []
    for c in v:
        try:
            ok = not isinstance(c, bool) and isinstance(c, numbers.Real) and -BIG <= float(c) <= BIG       # NaN fails the comparison
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f"{what} must hold finite real numbers within +-1e150, got {c!r}")
        out.append(float(c))
    return tuple(out)


def _norm2(s) -> float:
    return s[0] * s[0] + s[1] * s[1] + s[2] * s[2]


def _inverted(s) -> Vector:
    """-s / |s|^2 for a non-zero s; the squared norm underflows below 1e-162, so tiny vectors go through the norm."""
    n2 = _norm2(s)
    if n2 > 1e-280:
        return (-s[0] / n2, -s[1] / n2, -s[2] / n2)
    n = math.hypot(*s)
    return (-s[0] / n / n, -s[1] / n / n, -s[2] / n / n)


def mrp_from_quaternion(q) -> Vector:
    w, x, y, z = _seq(q, 4, "q")
    scale = max(abs(w), abs(x), abs(y), abs(z))
    if scale == 0.0:
        raise ValueError("q is the zero quaternion: it is not a rotation")
    w, x, y, z = w / scale, x / scale, y / scale, z / scale
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if w < 0.0:                                              # q and -q are the same attitude: take the short rotation
        w, x, y, z = -w, -x, -y, -z
    d = norm + w
    return (x / d, y / d, z / d)


def quaternion_from_mrp(s) -> Tuple[float, float, float, float]:
    s = _seq(s, 3, "s")
    n2 = _norm2(s)
    if n2 > 1.0:                                             # the shadow set is the same attitude and has w > 0
        s = (-s[0] / n2, -s[1] / n2, -s[2] / n2)
        n2 = 1.0 / n2
    d = 1.0 + n2
    return ((1.0 - n2) / d, 2.0 * s[0] / d, 2.0 * s[1] / d, 2.0 * s[2] / d)


def shadow(s) -> Vector:
    s = _seq(s, 3, "s")
    if s == (0.0, 0.0, 0.0):
        raise ValueError("the zero MRP has no shadow set: it would be at infinity")
    return _inverted(s)


def switch(s, threshold: float = 1.0) -> Vector:
    s = _seq(s, 3, "s")
    (t,) = _seq((threshold,), 1, "threshold")
    if t <= 0.0:
        raise ValueError(f"threshold must be positive, got {threshold!r}")
    n = math.hypot(*s)
    return _inverted(s) if n > t else s


def _multiply(a, b):
    """Quaternion of C(b) C(a) in the reference-to-body convention."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (bw * aw - bx * ax - by * ay - bz * az, bw * ax + bx * aw - by * az + bz * ay, bw * ay + bx * az + by * aw - bz * ax,
            bw * az - bx * ay + by * ax + bz * aw)


def compose(first, second) -> Vector:
    # through quaternions: the direct MRP formula divides by zero when the two rotations add up to a full turn
    return mrp_from_quaternion(_multiply(quaternion_from_mrp(first), quaternion_from_mrp(second)))


def dcm_from_mrp(s) -> Tuple[Vector, Vector, Vector]:
    w, x, y, z = quaternion_from_mrp(s)
    return ((w * w + x * x - y * y - z * z, 2.0 * (x * y + w * z), 2.0 * (x * z - w * y)),
            (2.0 * (x * y - w * z), w * w - x * x + y * y - z * z, 2.0 * (y * z + w * x)),
            (2.0 * (x * z + w * y), 2.0 * (y * z - w * x), w * w - x * x - y * y + z * z))


def rotation_vector_from_mrp(s) -> Vector:
    s = switch(s)                                            # |sigma| <= 1: angle in [0, pi]
    n = math.hypot(*s)
    if n == 0.0:
        return (0.0, 0.0, 0.0)
    factor = 4.0 * math.atan(n) / n
    return (factor * s[0], factor * s[1], factor * s[2])


def mrp_from_rotation_vector(v) -> Vector:
    v = _seq(v, 3, "v")
    scale = max(abs(c) for c in v)
    if scale == 0.0:
        return (0.0, 0.0, 0.0)
    unit = [c / scale for c in v]
    size = math.sqrt(unit[0] ** 2 + unit[1] ** 2 + unit[2] ** 2)
    angle = math.remainder(scale * size, 2.0 * math.pi)      # in [-pi, pi]: the short rotation
    factor = math.tan(angle / 4.0) / size
    return (factor * unit[0], factor * unit[1], factor * unit[2])


def mrp_rate(s, omega) -> Vector:
    s, w = _seq(s, 3, "s"), _seq(omega, 3, "omega")
    n2 = _norm2(s)
    dot = s[0] * w[0] + s[1] * w[1] + s[2] * w[2]
    cross = (s[1] * w[2] - s[2] * w[1], s[2] * w[0] - s[0] * w[2], s[0] * w[1] - s[1] * w[0])
    return tuple(0.25 * ((1.0 - n2) * w[i] + 2.0 * cross[i] + 2.0 * dot * s[i]) for i in range(3))
