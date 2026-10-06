"""Public inventory, exact constants, and ValueError refusals of star_units.

Exercises every public argument with hostile inputs, dimension mismatches,
overflow, and both sides of each absolute-zero boundary.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release. One of its tests asked for an exact degree-to-milliarcsecond factor: the module now holds angles as exact fractions of a degree."""
import math
from fractions import Fraction as F

import pytest

import star_units as su


# None is hostile as a unit or value, but is the documented default argument
# to units(). Finite, representable numbers are deliberately not in BAD_VALUE.
BAD_VALUE = [
    float("nan"), float("inf"), float("-inf"),
    10 ** 400, -(10 ** 400), F(10 ** 400),
    True, False, "1", None, 1j, [1.0], (1.0,), b"1",
]
BAD_NAME = [
    float("nan"), float("inf"), float("-inf"),
    10 ** 400, -(10 ** 400), F(10 ** 400),
    True, False, "1", None, 1j, [1.0], (1.0,), b"m",
    "", "M", "Km", "LBF", "n",
]

# The names are pinned independently of UNITS and TEMPERATURES. This also
# checks the distinction between lb/lbf and N*s/lbf*s.
NAMES = {
    "angle": "rad deg arcmin arcsec mas rev".split(),
    "energy": "J kJ MJ Wh kWh eV cal BTU erg ft*lbf".split(),
    "force": "N kN lbf kgf dyn".split(),
    "impulse": ["N*s", "kN*s", "lbf*s"],
    "length": "m km cm mm in ft yd mi nmi au ly pc".split(),
    "mass": "kg g t lb oz slug".split(),
    "power": "W kW hp".split(),
    "pressure": "Pa kPa MPa bar atm psi torr".split(),
    "speed": "m/s km/s km/h mph kn ft/s".split(),
    "time": "s min h day week julian_year".split(),
    "temperature": ["K", "degC", "degF", "degR"],
}


def test_public_inventory_and_pinned_names():
    assert su.__version__ == "0.1.0"
    assert su.__all__ == ["convert", "convert_temperature", "dimension", "units"]
    assert su.units() == sorted(name for group in NAMES.values() for name in group)
    assert len(su.units()) == 68
    assert su.units(None) == su.units()
    assert su.units("impulse") == ["N*s", "kN*s", "lbf*s"]
    assert su.units("temperature") == ["K", "degC", "degF", "degR"]
    for dimension, names in NAMES.items():
        assert su.units(dimension) == sorted(names)
        for name in names:
            assert su.dimension(name) == dimension


def test_pinned_exact_defining_constants():
    # Inch, pound, standard gravity, light speed, Julian year, nautical
    # mile, and astronomical unit are exact definitions from FACTS.
    assert su.INCH == F("0.0254")
    assert su.POUND == F("0.45359237")
    assert su.G0 == F("9.80665")
    assert su.FOOT == 12 * F("0.0254")
    assert su.MILE == 63360 * F("0.0254")
    assert su.NMI == F(1852)
    assert su.AU == F(149597870700)
    assert su.LBF == F("0.45359237") * F("9.80665")
    assert su.JULIAN_YEAR == F(31557600)
    assert su.C_LIGHT == F(299792458)
    assert su.PI == math.pi
    # Kelvin = (reading + offset) * scale, by the temperature definitions.
    assert su.TEMPERATURES == {
        "K": (F(0), F(1)),
        "degC": (F("273.15"), F(1)),
        "degF": (F("459.67"), F(5, 9)),
        "degR": (F(0), F(5, 9)),
    }


def test_every_numeric_argument_refuses_every_hostile_value():
    for bad in BAD_VALUE:
        for position in range(3):
            ordinary = [1, "ft", "m"]
            ordinary[position] = bad
            if position == 0:
                with pytest.raises(ValueError, match="finite real"):
                    su.convert(*ordinary)
            else:
                with pytest.raises(ValueError, match="unknown unit"):
                    su.convert(*ordinary)

            temperature = [20, "degC", "degF"]
            temperature[position] = bad
            if position == 0:
                with pytest.raises(ValueError, match="finite real"):
                    su.convert_temperature(*temperature)
            else:
                with pytest.raises(ValueError, match="unknown temperature unit"):
                    su.convert_temperature(*temperature)


def test_every_unit_and_inventory_argument_refuses_hostile_names():
    for bad in BAD_NAME:
        with pytest.raises(ValueError, match="unknown unit"):
            su.convert(1, bad, "m")
        with pytest.raises(ValueError, match="unknown unit"):
            su.convert(1, "m", bad)
        with pytest.raises(ValueError, match="unknown temperature unit"):
            su.convert_temperature(20, bad, "K")
        with pytest.raises(ValueError, match="unknown temperature unit"):
            su.convert_temperature(20, "K", bad)
        with pytest.raises(ValueError, match="unknown unit"):
            su.dimension(bad)
        if bad is not None:
            with pytest.raises(ValueError, match="unknown dimension"):
                su.units(bad)


@pytest.mark.parametrize("bad", ["m", "deg", "degC", "force ", "Temperature", "IMPULSE"])
def test_unknown_dimension_names(bad):
    with pytest.raises(ValueError, match="unknown dimension"):
        su.units(bad)


@pytest.mark.parametrize(
    "source,target,left,right",
    [
        ("lbf", "N*s", "force", "impulse"),
        ("N*s", "lbf", "impulse", "force"),
        ("lb", "lbf", "mass", "force"),
        ("lbf", "lb", "force", "mass"),
        ("deg", "m", "angle", "length"),
        ("m", "deg", "length", "angle"),
    ],
)
def test_mismatched_dimensions_name_both_sides(source, target, left, right):
    with pytest.raises(ValueError) as error:
        su.convert(1, source, target)
    assert left in str(error.value) and right in str(error.value)
    assert source in str(error.value) and target in str(error.value)


@pytest.mark.parametrize("name", ["K", "degC", "degF", "degR"])
def test_temperature_names_are_not_linear_units(name):
    with pytest.raises(ValueError, match="unknown unit"):
        su.convert(1, name, "m")
    with pytest.raises(ValueError, match="unknown unit"):
        su.convert(1, "m", name)


@pytest.mark.parametrize("name", ["m", "N", "deg", "lbf*s"])
def test_linear_names_are_not_temperature_units(name):
    with pytest.raises(ValueError, match="unknown temperature unit"):
        su.convert_temperature(1, name, "K")
    with pytest.raises(ValueError, match="unknown temperature unit"):
        su.convert_temperature(1, "K", name)


def test_finite_values_and_output_overflow_are_distinct():
    assert su.convert(10 ** 3, "m", "m") == 1000.0
    assert su.convert(F(7, 2), "m", "m") == 3.5
    assert su.convert(1e300, "m", "m") == 1e300
    assert su.convert_temperature(F(1, 2), "K", "K") == 0.5
    with pytest.raises(ValueError, match="overflows"):
        su.convert(1e308, "km", "mm")
    with pytest.raises(ValueError, match="overflows"):
        su.convert(-1e308, "km", "mm")


@pytest.mark.parametrize(
    "unit,zero,inside,outside",
    [
        # A negative Kelvin reading within 1e-9 K is clamped to zero.
        ("K", 0.0, -1e-10, -2e-9),
        # 273.15 C and 459.67 F are the offsets; 2e-9 C and
        # 2e-8 F respectively put the reading below the tolerance.
        ("degC", -273.15, -273.15 - 1e-10, -273.15 - 2e-9),
        ("degF", -459.67, -459.67 - 1e-10, -459.67 - 2e-8),
        # Rankine degrees are 5/9 Kelvin.
        ("degR", 0.0, -1e-10, -1e-8),
    ],
)
def test_both_sides_of_absolute_zero_for_every_scale(unit, zero, inside, outside):
    assert su.convert_temperature(zero, unit, "K") == pytest.approx(0, abs=1e-12)
    assert su.convert_temperature(inside, unit, "K") == 0
    with pytest.raises(ValueError, match="below absolute zero"):
        su.convert_temperature(outside, unit, "K")
    # Going the other way reaches each scale's lower endpoint.
    assert su.convert_temperature(0, "K", unit) == pytest.approx(
        zero, abs=1e-12
    )


def test_kelvin_clamping_threshold_on_each_side():
    # The guard is the exact fraction -1/10**9 K; the float -1e-9 is a hair BELOW it (it is -1.00000000000000006e-9), so it is refused.
    assert su.convert_temperature(-9.99999e-10, "K", "K") == 0
    assert su.convert_temperature(math.nextafter(-1e-9, math.inf), "K", "K") == 0
    for below in (-1e-9, math.nextafter(-1e-9, -math.inf), -1.000001e-9):
        with pytest.raises(ValueError, match="below absolute zero"):
            su.convert_temperature(below, "K", "K")


def test_absolute_zero_round_trip_and_positive_side():
    celsius = su.convert_temperature(0, "K", "degC")
    assert su.convert_temperature(celsius, "degC", "K") == pytest.approx(
        0, abs=1e-12
    )
    assert su.convert_temperature(celsius, "degC", "K") >= 0
    # One kelvin above zero is -272.15 C, or -457.87 F:
    # Fahrenheit changes by 9/5 degrees per kelvin.
    assert su.convert_temperature(1, "K", "degC") == pytest.approx(
        -272.15, abs=1e-12
    )
    assert su.convert_temperature(1, "K", "degF") == pytest.approx(
        -457.87, abs=1e-12
    )
