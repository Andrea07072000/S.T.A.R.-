"""star_atmosphere - U.S. Standard Atmosphere 1976 below 86 km (S.T.A.R., 2026-10-06). Standard library only.

  ussa1976(z_m) -> (temperature_K, pressure_Pa, density_kg_m3, speed_of_sound_m_s) at GEOMETRIC altitude z_m.
  geopotential_m(z_m) / geometric_m(h_m): conversion between geometric and geopotential altitude.
Model: the seven layers of constant temperature gradient defined in "U.S. Standard Atmosphere, 1976" (NOAA/NASA/USAF),
with its own constants (note R* = 8.31432 J/(mol K), the 1976 value, not the present CODATA one).
Valid from -5000 m to 86 000 m geometric (84 852 m geopotential); outside, ValueError.
The temperature returned is the molecular-scale temperature T_M of the standard: it is the kinetic temperature up to
80 km; at 86 km the kinetic temperature printed in the standard is 186.87 K against T_M = 186.95 K (0.04 % lower).
Pressure, density and speed of sound are defined by the standard through T_M and are not affected. Above 86 km the standard
changes formulation (molecular weight is no longer constant): that region is not implemented and is refused.
Refusals (ValueError): non-numeric, boolean or non-finite input, altitude outside the valid range.
"""
from __future__ import annotations

import math
import numbers
from typing import Tuple

__all__ = ["ussa1976", "geopotential_m", "geometric_m"]
__version__ = "0.1.0"
G0 = 9.80665                 # m/s^2
R_STAR = 8.31432             # J/(mol K), value adopted by the 1976 standard
M0 = 0.0289644               # kg/mol
R_EARTH = 6356766.0          # m, effective radius used by the standard for geopotential altitude
GAMMA = 1.4
T0, P0 = 288.15, 101325.0
Z_MIN, Z_MAX = -5000.0, 86000.0
# base geopotential altitude (m) and temperature gradient (K/m) of each layer
LAYERS = ((0.0, -0.0065), (11000.0, 0.0), (20000.0, 0.001), (32000.0, 0.0028), (47000.0, 0.0), (51000.0, -0.0028), (71000.0, -0.002))


def _num(v) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e300 < float(v) < 1e300      # NaN fails both
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("altitude must be a finite real number")
    return float(v)


def geopotential_m(z_m: float) -> float:
    z = _num(z_m)
    if not Z_MIN <= z <= Z_MAX:
        raise ValueError("geometric altitude outside [-5000, 86000] m")
    return R_EARTH * z / (R_EARTH + z)


H_MIN, H_MAX = R_EARTH * Z_MIN / (R_EARTH + Z_MIN), R_EARTH * Z_MAX / (R_EARTH + Z_MAX)


def geometric_m(h_m: float) -> float:
    h = _num(h_m)
    if not H_MIN - 1e-6 <= h <= H_MAX + 1e-6:
        raise ValueError("geopotential altitude outside the range of the model")
    return min(Z_MAX, max(Z_MIN, R_EARTH * h / (R_EARTH - h)))


def _layer(tb: float, pb: float, hb: float, lapse: float, h: float) -> Tuple[float, float]:
    """Temperature and pressure at geopotential altitude h inside the layer that starts at (hb, tb, pb)."""
    if lapse == 0.0:
        return tb, pb * math.exp(-G0 * M0 * (h - hb) / (R_STAR * tb))
    t = tb + lapse * (h - hb)
    return t, pb * (tb / t) ** (G0 * M0 / (R_STAR * lapse))


def ussa1976(z_m: float) -> Tuple[float, float, float, float]:
    h = geopotential_m(z_m)
    t, p = T0, P0
    for i, (hb, lapse) in enumerate(LAYERS):
        top = LAYERS[i + 1][0] if i + 1 < len(LAYERS) else math.inf
        if h <= top:
            t, p = _layer(t, p, hb, lapse, h)
            break
        t, p = _layer(t, p, hb, lapse, top)
    return t, p, p * M0 / (R_STAR * t), math.sqrt(GAMMA * R_STAR * t / M0)
