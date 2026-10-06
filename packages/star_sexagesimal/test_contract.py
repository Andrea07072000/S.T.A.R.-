"""Refusals of star_sexagesimal with hostile inputs and at the exact limits of every range.

Every public function returns the documented type in the documented ranges or raises
ValueError; no out-of-range value is silently accepted.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (four wrong expectations)."""
from fractions import Fraction

import pytest

import star_sexagesimal as ss

BAD = [
    float("nan"),
    float("inf"),
    float("-inf"),
    10 ** 400,
    -10 ** 400,
    1e300,
    -1e300,
    True,
    False,
    "10",
    None,
    1j,
    [10.0],
    (1.0,),
]


def test_the_hostile_set_and_published_constants_are_pinned():
    assert len(BAD) == 14
    assert ss.__version__ == "0.1.0"
    assert ss.__all__ == ["deg_to_dms", "deg_to_hms", "dms_to_deg", "hms_to_deg"]
    assert ss.deg_to_dms.__defaults__ == (3,)
    assert ss.deg_to_hms.__defaults__ == (4,)


@pytest.mark.parametrize("f, defaults", [
    (ss.deg_to_dms, (0.0, 3)),
    (ss.deg_to_hms, (0.0, 4)),
])
def test_split_functions_refuse_hostile_angle_and_decimals(f, defaults):
    angle, decimals = defaults
    assert isinstance(f(angle, decimals), tuple)
    for bad in BAD:
        with pytest.raises(ValueError):
            f(bad, decimals)
        with pytest.raises(ValueError):
            f(angle, bad)


@pytest.mark.parametrize("f, defaults", [
    (ss.dms_to_deg, ('+', 0, 0, 0.0)),
    (ss.hms_to_deg, ('+', 0, 0, 0.0)),
])
def test_join_functions_refuse_hostile_arguments(f, defaults):
    assert isinstance(f(*defaults), float)
    for bad in BAD:
        for i in range(len(defaults)):
            args = list(defaults)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("sign", ["", " ", " +", "+ ", "- ", "++", "--", "±", 0, 1, -1, b"+", [], "+-"])
@pytest.mark.parametrize("f", [ss.dms_to_deg, ss.hms_to_deg])
def test_only_exact_plus_or_minus_are_accepted_as_signs(sign, f):
    with pytest.raises(ValueError):
        f(sign, 0, 0, 0.0)


def test_angle_range_is_closed_at_both_ends():
    assert isinstance(ss.deg_to_dms(-360.0, 0), tuple)
    assert isinstance(ss.deg_to_dms(360.0, 0), tuple)
    assert isinstance(ss.deg_to_hms(360.0, 0), tuple)
    with pytest.raises(ValueError, match="angle"):
        ss.deg_to_dms(-360.0000001, 0)
    with pytest.raises(ValueError, match="angle"):
        ss.deg_to_dms(360.0000001, 0)
    with pytest.raises(ValueError, match="angle"):
        ss.deg_to_hms(-360.0000001, 0)


def test_decimals_must_be_an_integer_between_zero_and_six():
    for d in (0, 1, 5, 6):
        assert isinstance(ss.deg_to_dms(0.0, d), tuple)
        assert isinstance(ss.deg_to_hms(0.0, d), tuple)

    for d in (-1, 7, 3.0, "3", None, True, Fraction(1, 2)):
        with pytest.raises(ValueError, match="decimals"):
            ss.deg_to_dms(0.0, d)


def test_degrees_and_hours_have_integer_ranges_with_closed_limits():
    assert ss.dms_to_deg('+', 360, 0, 0.0) == 360.0
    assert ss.dms_to_deg('-', 360, 0, 0.0) == -360.0
    assert ss.hms_to_deg('+', 24, 0, 0.0) == 360.0
    assert ss.hms_to_deg('-', 24, 0, 0.0) == -360.0

    with pytest.raises(ValueError, match="degrees"):
        ss.dms_to_deg('+', 361, 0, 0.0)
    with pytest.raises(ValueError, match="degrees"):
        ss.dms_to_deg('+', -1, 0, 0.0)
    with pytest.raises(ValueError, match="hours"):
        ss.hms_to_deg('+', 25, 0, 0.0)
    with pytest.raises(ValueError, match="hours"):
        ss.hms_to_deg('+', -1, 0, 0.0)

    # the fields must be integers, not integral floats
    with pytest.raises(ValueError, match="degrees"):
        ss.dms_to_deg('+', 360.0, 0, 0.0)
    with pytest.raises(ValueError, match="hours"):
        ss.hms_to_deg('+', 24.0, 0, 0.0)


def test_minutes_are_integers_between_zero_and_fifty_nine():
    assert ss.dms_to_deg('+', 0, 59, 0.0) == pytest.approx(59.0 / 60.0, abs=1e-15)      # 59 arcminutes
    assert ss.hms_to_deg('+', 0, 59, 0.0) == 14.75                                      # 59 minutes of time = 59 * 15 arcminutes

    with pytest.raises(ValueError, match="minutes"):
        ss.dms_to_deg('+', 0, 60, 0.0)
    with pytest.raises(ValueError, match="minutes"):
        ss.dms_to_deg('+', 0, -1, 0.0)
    with pytest.raises(ValueError, match="minutes"):
        ss.dms_to_deg('+', 0, 59.0, 0.0)


def test_seconds_range_is_half_open_zero_inclusive_to_sixty_exclusive():
    assert ss.dms_to_deg('+', 0, 0, 0.0) == 0.0
    assert ss.dms_to_deg('+', 0, 0, 59.99999999999999) == pytest.approx(
        59.99999999999999 / 3600.0, abs=1e-15
    )
    assert ss.hms_to_deg('+', 0, 0, 59.99999999999999) == pytest.approx(
        59.99999999999999 / 240.0, abs=1e-15
    )

    with pytest.raises(ValueError, match="seconds"):
        ss.dms_to_deg('+', 0, 0, -1e-12)
    with pytest.raises(ValueError, match="seconds"):
        ss.dms_to_deg('+', 0, 0, 60.0)
    with pytest.raises(ValueError, match="seconds"):
        ss.hms_to_deg('+', 0, 0, 60.0)


def test_total_angle_must_not_exceed_three_hundred_sixty_degrees():
    # 360 deg 0' 1" and 24 h 0 m 1 s are exactly the documented refusals
    with pytest.raises(ValueError, match="angle exceeds"):
        ss.dms_to_deg('+', 360, 0, 1.0)
    with pytest.raises(ValueError, match="angle exceeds"):
        ss.hms_to_deg('+', 24, 0, 1.0)

    # just below the total limit is still accepted
    assert 360.0 - 1e-12 < ss.dms_to_deg('+', 359, 59, 59.9999999999) <= 360.0       # the float sum may round up to 360
    assert 360.0 - 1e-12 < ss.hms_to_deg('+', 23, 59, 59.9999999999) <= 360.0
