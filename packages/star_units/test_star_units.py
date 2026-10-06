"""Conversions against exact definitions, hand-derived factors, and invariants.

The published values used here are only the SI definitions and equivalences
listed in FACTS. Other expected values are derived in the comments below.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release. One of its tests asked for an exact degree-to-milliarcsecond factor: the module now holds angles as exact fractions of a degree."""
import math
from fractions import Fraction as F

import pytest

import star_units as su


# Each fraction is a factor to the SI unit. Published factors are written
# directly; the remaining factors follow by decimal prefixes, subdivision,
# or multiplication of published factors.
# Examples: cm = m/100; min = 60 s; kWh = 1000 Wh;
# kN*s = 1000 N*s; ft/s = 0.3048 m/s.
FACTORS = {
    "length": ("m", {
        "m": F(1), "km": F(1000), "cm": F(1, 100), "mm": F(1, 1000),
        "in": F("0.0254"), "ft": F("0.3048"), "yd": F("0.9144"),
        "mi": F("1609.344"), "nmi": F(1852), "au": F(149597870700),
        "ly": F(299792458) * F(31557600),
    }),
    "mass": ("kg", {
        "kg": F(1), "g": F(1, 1000), "t": F(1000),
        "lb": F("0.45359237"), "oz": F("0.45359237") / 16,
        # One slug accelerates by 1 ft/s2 under one lbf.
        "slug": F("0.45359237") * F("9.80665") / F("0.3048"),
    }),
    "time": ("s", {
        "s": F(1), "min": F(60), "h": F(3600), "day": F(86400),
        "week": F(604800), "julian_year": F(31557600),
    }),
    "force": ("N", {
        "N": F(1), "kN": F(1000), "lbf": F("0.45359237") * F("9.80665"),
        "kgf": F("9.80665"), "dyn": F(1, 100000),
    }),
    "pressure": ("Pa", {
        "Pa": F(1), "kPa": F(1000), "MPa": F(1000000),
        "bar": F(100000), "atm": F(101325),
        # Pressure is force divided by area; a torr is 1/760 atm.
        "psi": F("0.45359237") * F("9.80665") / F("0.0254") ** 2,
        "torr": F(101325, 760),
    }),
    "speed": ("m/s", {
        "m/s": F(1), "km/s": F(1000), "km/h": F(1000, 3600),
        "mph": F("1609.344") / 3600, "kn": F(1852, 3600),
        "ft/s": F("0.3048"),
    }),
    "energy": ("J", {
        "J": F(1), "kJ": F(1000), "MJ": F(1000000),
        "Wh": F(3600), "kWh": F(3600000),
        "eV": F("1.602176634e-19"), "cal": F("4.184"),
        "BTU": F("1055.05585262"), "erg": F("1e-7"),
        # Work = force times displacement.
        "ft*lbf": F("0.3048") * F("0.45359237") * F("9.80665"),
    }),
    "power": ("W", {
        "W": F(1), "kW": F(1000),
        # One horsepower is 550 ft*lbf each second.
        "hp": 550 * F("0.3048") * F("0.45359237") * F("9.80665"),
    }),
    "impulse": ("N*s", {
        "N*s": F(1), "kN*s": F(1000),
        # Impulse = force times time.
        "lbf*s": F("0.45359237") * F("9.80665"),
    }),
}


@pytest.mark.parametrize(
    "dimension,si,factors",
    [(dimension, si, factors) for dimension, (si, factors) in FACTORS.items()],
)
def test_every_rational_factor_in_both_directions(dimension, si, factors):
    for name, factor in factors.items():
        assert su.dimension(name) == dimension
        # The definition gives factor SI units per named unit. Reversing the
        # conversion gives the reciprocal, formed as an exact fraction first.
        assert su.convert(1, name, si) == float(factor)
        assert su.convert(1, si, name) == float(1 / factor)


def test_astronomical_and_angle_factors():
    # IAU parsec: 648000/pi au. Both pi-dependent expressions allow only
    # floating-point rounding, not a separately invented decimal expansion.
    pc_metres = 648000 * 149597870700 / math.pi
    assert su.convert(1, "pc", "m") == pytest.approx(pc_metres, rel=1e-15)
    assert su.convert(1, "m", "pc") == pytest.approx(1 / pc_metres, rel=1e-15)
    assert su.dimension("pc") == "length"

    # A revolution is 2 pi radians; subdivide 180 degrees into arcminutes,
    # arcseconds, and milliarcseconds.
    radians = {
        "rad": 1.0, "deg": math.pi / 180,
        "arcmin": math.pi / 10800, "arcsec": math.pi / 648000,
        "mas": math.pi / 648000000, "rev": 2 * math.pi,
    }
    for name, factor in radians.items():
        assert su.dimension(name) == "angle"
        assert su.convert(1, name, "rad") == pytest.approx(factor, rel=1e-15)
        assert su.convert(1, "rad", name) == pytest.approx(1 / factor, rel=1e-15)
    assert su.convert(180, "deg", "rad") == pytest.approx(math.pi, rel=1e-15)
    assert su.convert(1, "deg", "arcmin") == 60
    assert su.convert(1, "deg", "arcsec") == 3600
    assert su.convert(1, "deg", "mas") == 3600000
    assert su.convert(1, "rev", "deg") == pytest.approx(360, rel=1e-15)


def test_selected_published_products_and_exact_quotients():
    # These products and quotients are the definitions in FACTS, rather
    # than measurements or additional published examples.
    assert su.convert(1, "ly", "m") == 9460730472580800
    assert su.convert(1, "lbf", "N") == 4.4482216152605
    assert su.convert(1, "lbf*s", "N*s") == 4.4482216152605
    assert su.convert(1, "torr", "Pa") == float(F(101325, 760))
    assert su.convert(1, "psi", "Pa") == pytest.approx(
        6894.757293168362, rel=1e-15
    )
    assert su.convert(1, "ft*lbf", "J") == pytest.approx(
        1.3558179483314004, rel=1e-15
    )
    assert su.convert(1, "hp", "W") == pytest.approx(
        745.6998715822702, rel=1e-15
    )


def test_linear_conversions_self_inverses_and_composition():
    groups = [list(factors) for _, factors in FACTORS.values()]
    groups[0].append("pc")
    groups.append(["rad", "deg", "arcmin", "arcsec", "mas", "rev"])
    for names in groups:
        for source in names:
            for value in (0, -3, F(7, 2)):
                assert su.convert(value, source, source) == float(value)
            for target in names:
                # Linearity follows from multiplying by the factor ratio.
                forward = su.convert(1, source, target)
                assert su.convert(-3, source, target) == pytest.approx(
                    -3 * forward, rel=2e-16, abs=1e-20
                )
                assert su.convert(F(7, 2), source, target) == pytest.approx(
                    3.5 * forward, rel=2e-16, abs=1e-20
                )
                assert su.convert(0, source, target) == 0
                assert forward * su.convert(1, target, source) == pytest.approx(
                    1, rel=2e-16
                )
        # Route through the SI unit: the two factor ratios multiply to the
        # direct factor ratio, with at most the stated floating-point error.
        si = names[0]
        for source in names:
            for target in names:
                direct = su.convert(1, source, target)
                via_si = su.convert(su.convert(1, source, si), si, target)
                assert via_si == pytest.approx(direct, rel=4e-16)


# Kelvin = (reading + offset) * scale. Celsius has offset 273.15;
# Fahrenheit has offset 459.67 and scale 5/9; Rankine has scale 5/9.
TEMP = {
    "K": (F(0), F(1)),
    "degC": (F("273.15"), F(1)),
    "degF": (F("459.67"), F(5, 9)),
    "degR": (F(0), F(5, 9)),
}


def test_published_temperature_fixed_points():
    assert su.convert_temperature(0, "degC", "K") == pytest.approx(273.15, abs=1e-12)
    assert su.convert_temperature(0, "degC", "degF") == pytest.approx(32, abs=1e-12)
    assert su.convert_temperature(0, "degC", "degR") == pytest.approx(491.67, abs=1e-12)
    assert su.convert_temperature(100, "degC", "degF") == pytest.approx(212, abs=1e-12)
    assert su.convert_temperature(-40, "degC", "degF") == pytest.approx(-40, abs=1e-12)
    assert su.convert_temperature(0, "K", "degC") == pytest.approx(-273.15, abs=1e-12)
    assert su.convert_temperature(0, "K", "degF") == pytest.approx(-459.67, abs=1e-12)
    assert su.convert_temperature(0, "degR", "K") == 0
    assert su.convert_temperature(
        su.convert_temperature(0, "K", "degC"), "degC", "K"
    ) == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize("kelvin", [F(0), F("233.15"), F("273.15"), F("373.15")])
def test_all_temperature_pairs_at_hand_derived_points(kelvin):
    # 233.15 K = -40 C; 273.15 K = 0 C; 373.15 K = 100 C.
    # For each source, reading = kelvin/scale - offset. Apply the same
    # rearrangement to the destination to obtain its expected reading.
    for source, (source_offset, source_scale) in TEMP.items():
        reading = float(kelvin / source_scale - source_offset)
        assert su.dimension(source) == "temperature"
        for target, (target_offset, target_scale) in TEMP.items():
            expected = float(kelvin / target_scale - target_offset)
            result = su.convert_temperature(reading, source, target)
            assert result == pytest.approx(expected, abs=1e-12)
            assert su.convert_temperature(result, target, source) == pytest.approx(
                reading, abs=1e-12
            )


def test_temperature_offsets_and_scales_are_not_treated_as_linear_units():
    # 100 C - 0 C = 100 K = 180 F = 180 R; 491.67 R = 273.15 K.
    assert (
        su.convert_temperature(100, "degC", "degF")
        - su.convert_temperature(0, "degC", "degF")
    ) == pytest.approx(180, abs=1e-12)
    assert su.convert_temperature(491.67, "degR", "K") == pytest.approx(
        273.15, abs=1e-12
    )
    assert su.convert_temperature(671.67, "degR", "K") == pytest.approx(
        373.15, abs=1e-12
    )
    assert su.convert_temperature(100, "K", "K") == 100.0
