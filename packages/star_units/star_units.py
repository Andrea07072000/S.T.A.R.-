"""star_units - unit conversion with exact definitions and a dimension check (S.T.A.R., 2026-10-06).
Standard library only.

  convert(value, from_unit, to_unit) -> float          e.g. convert(1.0, "lbf", "N") == 4.4482216152605
  convert_temperature(value, from_unit, to_unit)       "K", "degC", "degF", "degR" (these have offsets)
  dimension(unit) -> str                               "length", "mass", "time", "force", "pressure", ...
  units(dimension=None) -> sorted list of unit names
Every factor is the exact definition (SI Brochure 9th ed.; NIST SP 811; the 1959 international yard and pound;
standard gravity 9.80665 m/s2; IAU 2012 B2 for the astronomical unit, IAU 2015 B2 for the parsec), held as an exact
fraction; the ratio of two factors is formed exactly and rounded once. Only the radian and the parsec involve pi
and are held as floats.
Converting between different dimensions is an error, never a number: pounds-force are not newton-seconds, and
"lb" (mass) is not "lbf" (force).
Refusals (ValueError): a value that is not a finite real number (booleans included), a unit that is not a string of
the table (names are case-sensitive), units of different dimensions, a temperature below absolute zero.
"""
from __future__ import annotations

import math
import numbers
from fractions import Fraction as F
from typing import Dict, List, Optional, Tuple, Union

__all__ = ["convert", "convert_temperature", "dimension", "units"]
__version__ = "0.1.0"

INCH, POUND, G0 = F(254, 10000), F(45359237, 100000000), F(980665, 100000)     # m, kg, m/s2: exact by definition
FOOT, MILE, NMI, AU = 12 * INCH, 63360 * INCH, F(1852), F(149597870700)
LBF = POUND * G0                                                               # 4.4482216152605 N exactly
JULIAN_YEAR, C_LIGHT = F(31557600), F(299792458)
PI = math.pi

# name: (dimension, factor to the reference unit of that dimension: the SI unit, except degrees for angles)
UNITS: Dict[str, Tuple[str, Union[F, float]]] = {
    "m": ("length", F(1)), "km": ("length", F(1000)), "cm": ("length", F(1, 100)), "mm": ("length", F(1, 1000)),
    "in": ("length", INCH), "ft": ("length", FOOT), "yd": ("length", 3 * FOOT), "mi": ("length", MILE), "nmi": ("length", NMI),
    "au": ("length", AU), "ly": ("length", C_LIGHT * JULIAN_YEAR), "pc": ("length", float(AU) * 648000.0 / PI),
    "kg": ("mass", F(1)), "g": ("mass", F(1, 1000)), "t": ("mass", F(1000)), "lb": ("mass", POUND), "oz": ("mass", POUND / 16),
    "slug": ("mass", LBF / FOOT),
    "s": ("time", F(1)), "min": ("time", F(60)), "h": ("time", F(3600)), "day": ("time", F(86400)), "week": ("time", F(604800)),
    "julian_year": ("time", JULIAN_YEAR),
    "N": ("force", F(1)), "kN": ("force", F(1000)), "lbf": ("force", LBF), "kgf": ("force", G0), "dyn": ("force", F(1, 100000)),
    "Pa": ("pressure", F(1)), "kPa": ("pressure", F(1000)), "MPa": ("pressure", F(1000000)), "bar": ("pressure", F(100000)),
    "atm": ("pressure", F(101325)), "psi": ("pressure", LBF / (INCH * INCH)), "torr": ("pressure", F(101325, 760)),
    # angles are held in degrees, so that deg, arcmin, arcsec, mas and rev convert exactly; only the radian involves pi
    "rad": ("angle", 180.0 / PI), "deg": ("angle", F(1)), "arcmin": ("angle", F(1, 60)), "arcsec": ("angle", F(1, 3600)),
    "mas": ("angle", F(1, 3600000)), "rev": ("angle", F(360)),
    "m/s": ("speed", F(1)), "km/s": ("speed", F(1000)), "km/h": ("speed", F(1000, 3600)), "mph": ("speed", MILE / 3600),
    "kn": ("speed", NMI / 3600), "ft/s": ("speed", FOOT),
    "J": ("energy", F(1)), "kJ": ("energy", F(1000)), "MJ": ("energy", F(1000000)), "Wh": ("energy", F(3600)), "kWh": ("energy", F(3600000)),
    "eV": ("energy", F(1602176634, 10 ** 28)), "cal": ("energy", F(4184, 1000)), "BTU": ("energy", F(105505585262, 10 ** 8)),
    "erg": ("energy", F(1, 10 ** 7)), "ft*lbf": ("energy", FOOT * LBF),
    "W": ("power", F(1)), "kW": ("power", F(1000)), "hp": ("power", 550 * FOOT * LBF),
    "N*s": ("impulse", F(1)), "lbf*s": ("impulse", LBF), "kN*s": ("impulse", F(1000)),
}
# temperature: kelvin = (value + offset) * scale
TEMPERATURES = {"K": (F(0), F(1)), "degC": (F(27315, 100), F(1)), "degF": (F(45967, 100), F(5, 9)), "degR": (F(0), F(5, 9))}


def _value(v) -> float:
    try:
        ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and math.isfinite(float(v))
    except OverflowError:
        ok = False
    if not ok:
        raise ValueError("the value must be a finite real number")
    return float(v)


def _unit(name, table, what: str = "unit"):
    if not isinstance(name, str) or name not in table:
        raise ValueError(f"unknown {what}: {name!r}")
    return table[name]


def dimension(unit: str) -> str:
    if isinstance(unit, str) and unit in TEMPERATURES:
        return "temperature"
    return _unit(unit, UNITS)[0]


def units(dimension: Optional[str] = None) -> List[str]:
    known = sorted({d for d, _ in UNITS.values()} | {"temperature"})
    if dimension is None:
        return sorted(list(UNITS) + list(TEMPERATURES))
    if not isinstance(dimension, str) or dimension not in known:
        raise ValueError(f"unknown dimension: {dimension!r}; known: {', '.join(known)}")
    return sorted(TEMPERATURES) if dimension == "temperature" else sorted(n for n, (d, _) in UNITS.items() if d == dimension)


def convert(value: float, from_unit: str, to_unit: str) -> float:
    v = _value(value)
    (d1, f1), (d2, f2) = _unit(from_unit, UNITS), _unit(to_unit, UNITS)
    if d1 != d2:
        raise ValueError(f"cannot convert {from_unit} ({d1}) to {to_unit} ({d2}): different dimensions")
    if isinstance(f1, F) and isinstance(f2, F):
        ratio = float(f1 / f2)                              # exact quotient, rounded once
    else:
        ratio = float(f1) / float(f2)
    out = v * ratio
    if not math.isfinite(out):
        raise ValueError("the result overflows a float")
    return out


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    v = _value(value)
    (o1, s1), (o2, s2) = _unit(from_unit, TEMPERATURES, "temperature unit"), _unit(to_unit, TEMPERATURES, "temperature unit")
    kelvin = (F(v) + o1) * s1                               # exact: a float is a fraction
    if kelvin < -F(1, 10 ** 9):
        raise ValueError("the temperature is below absolute zero")
    kelvin = max(kelvin, F(0))                              # -273.15 degC as a float is 3e-14 K below zero: it is absolute zero
    return float(kelvin / s2 - o2)
