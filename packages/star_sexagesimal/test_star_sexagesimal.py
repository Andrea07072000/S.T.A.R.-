"""star_sexagesimal against published examples, hand-derived angles, inverses and edge cases.

Published: Meeus, Astronomical Algorithms, J2000 mean obliquity 23 deg 26' 21.448" and
Example 13.b (RA 17h 48m 59.74s, Dec -14 deg 43' 08.2").  All other expected values are
derived by hand from 1 deg = 3600 arcsec and 15 deg = 1 h = 3600 s of time.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (four wrong expectations)."""
import pytest

import star_sexagesimal as ss


def test_published_j2000_obliquity_round_trips_exactly():
    # 23 deg 26' 21.448" = 84381.448" = 84381.448 / 3600 deg
    assert ss.dms_to_deg('+', 23, 26, 21.448) == pytest.approx(84381.448 / 3600.0, abs=1e-12)
    # the truncated value 23.4392911 is 1.11e-8 deg larger than the exact ratio
    assert abs(ss.dms_to_deg('+', 23, 26, 21.448) - 23.4392911) < 2e-8
    assert ss.deg_to_dms(23.4392911, 3) == ('+', 23, 26, 21, 448)


def test_published_meeus_13b_coordinates():
    # printed to 6 decimal places; tolerances taken from the FACTS
    assert ss.deg_to_hms(267.248917, 4) == ('+', 17, 48, 59, 7401)
    assert ss.deg_to_dms(-14.718944, 1) == ('-', 14, 43, 8, 2)
    # 17h 48m 59.74s = (17*3600 + 48*60 + 59.74)/240 deg
    assert abs(ss.hms_to_deg('+', 17, 48, 59.74) - 267.248917) < 5e-7
    # -14 deg 43' 08.2" = -(14*3600 + 43*60 + 8.2)/3600 deg
    assert abs(ss.dms_to_deg('-', 14, 43, 8.2) - (-14.718944)) < 5e-7


def test_hand_conversions_between_degrees_and_arcseconds():
    # 1.5 deg = 1 deg + 0.5*60'
    assert ss.deg_to_dms(1.5, 0) == ('+', 1, 30, 0, 0)
    # 0.0125 deg * 3600 = 45" exactly
    assert ss.deg_to_dms(0.0125, 0) == ('+', 0, 0, 45, 0)
    # 10.2625 deg = 10 + 15/60 + 45/3600 deg
    assert ss.deg_to_dms(10.2625, 0) == ('+', 10, 15, 45, 0)
    # one arcsecond is 1/3600 deg
    assert ss.dms_to_deg('+', 0, 0, 1) == 1.0 / 3600.0
    assert ss.deg_to_dms(1.0 / 3600.0, 0) == ('+', 0, 0, 1, 0)


def test_ties_round_away_from_zero_for_both_angle_systems():
    # 0.5/3600 deg = 0.5", so it is exactly halfway to 1" and rounds away from zero
    assert ss.deg_to_dms(0.5 / 3600.0, 0) == ('+', 0, 0, 1, 0)
    assert ss.deg_to_dms(-0.5 / 3600.0, 0) == ('-', 0, 0, 1, 0)
    # 0.5/240 deg = 0.5 s of time, the same halfway case in HMS
    assert ss.deg_to_hms(0.5 / 240.0, 0) == ('+', 0, 0, 1, 0)
    assert ss.deg_to_hms(-0.5 / 240.0, 0) == ('-', 0, 0, 1, 0)


def test_a_field_never_shows_sixty_and_there_is_no_wrapping():
    # 59.9996" rounds to the next arcminute: total units = floor(59.9996*1000 + 0.5) = 60000
    assert ss.deg_to_dms(59.9996 / 3600.0, 3) == ('+', 0, 1, 0, 0)
    # 0.9999999 deg * 3600 = 3599.99964", rounding gives 3600" = 1 deg
    assert ss.deg_to_dms(0.9999999, 3) == ('+', 1, 0, 0, 0)
    # extremes are stored as given, not wrapped modulo 360
    assert ss.deg_to_dms(360.0, 3) == ('+', 360, 0, 0, 0)
    assert ss.deg_to_hms(360.0, 4) == ('+', 24, 0, 0, 0)
    assert ss.deg_to_hms(-180.0, 0) == ('-', 12, 0, 0, 0)


def test_sign_rules_for_zero_and_small_negative_angles():
    # an angle that rounds to zero must carry the '+' sign
    assert ss.deg_to_dms(-1e-9, 3) == ('+', 0, 0, 0, 0)
    assert ss.deg_to_dms(0.0, 5) == ('+', 0, 0, 0, 0)
    # between 0 and -1 deg the sign is kept even though the degree field is zero
    assert ss.deg_to_dms(-0.5, 0) == ('-', 0, 30, 0, 0)


def test_hours_minutes_seconds_scale_by_fifteen_degrees_per_hour():
    assert ss.deg_to_hms(15.0, 0) == ('+', 1, 0, 0, 0)
    assert ss.hms_to_deg('+', 1, 0, 0) == 15.0
    assert ss.hms_to_deg('-', 12, 0, 0) == -180.0


def test_split_then_join_is_exact_for_integer_total_units():
    # choose an integer number of 1e-3 arcsec so the multiplication by 3600*1000 is exact
    total_dms = 123_456_789
    deg = total_dms / (3600.0 * 1000.0)
    sign, d, m, s, frac = ss.deg_to_dms(deg, 3)
    # 123456.789" = 34 deg 17' 36.789"
    assert (sign, d, m, s, frac) == ('+', 34, 17, 36, 789)
    assert ss.dms_to_deg(sign, d, m, s + frac / 1000.0) == pytest.approx(deg, abs=1e-12)                # 360 deg carries 6e-14 of rounding

    # choose an integer number of 1e-4 s of time; 1 deg = 240 s of time
    total_hms = 123_456_789
    deg2 = total_hms / (240.0 * 10000.0)
    sign2, h, mi, se, frac2 = ss.deg_to_hms(deg2, 4)
    # 12345.6789 s = 3 h 25 m 45.6789 s
    assert (sign2, h, mi, se, frac2) == ('+', 3, 25, 45, 6789)
    assert ss.hms_to_deg(sign2, h, mi, se + frac2 / 10000.0) == pytest.approx(deg2, abs=1e-12)


def test_split_then_join_is_within_one_rounding_unit_for_arbitrary_angles():
    half_dms = 0.5 / (3600.0 * 1000.0)    # deg, one half of the 1e-3" unit
    for deg in (-359.9999, -0.123456789, 0.0, 0.000123, 123.456789, 359.9999):
        sign, d, m, s, frac = ss.deg_to_dms(deg, 3)
        reconstructed = ss.dms_to_deg(sign, d, m, s + frac / 1000.0)
        assert abs(reconstructed - deg) <= half_dms + 1e-15

    half_hms = 0.5 / (240.0 * 10000.0)    # deg, one half of the 1e-4 s unit
    for deg in (-359.9999, -15.0, 0.0, 15.0, 267.248917, 359.9999):
        sign, h, mi, s, frac = ss.deg_to_hms(deg, 4)
        reconstructed = ss.hms_to_deg(sign, h, mi, s + frac / 10000.0)
        assert abs(reconstructed - deg) <= half_hms + 1e-15


def test_seconds_are_converted_by_the_documented_constants():
    # dms_to_deg returns degrees, so multiplying by 3600 gives the original arcseconds
    assert ss.dms_to_deg('+', 12, 34, 56.789) * 3600.0 == pytest.approx(
        12 * 3600.0 + 34 * 60.0 + 56.789, abs=1e-12
    )
    assert ss.dms_to_deg('-', 0, 30, 0.0) * 3600.0 == pytest.approx(-1800.0, abs=1e-12)
    # hms_to_deg returns degrees, so multiplying by 240 gives the original seconds of time
    assert ss.hms_to_deg('+', 5, 27, 36.0) * 240.0 == pytest.approx(
        5 * 3600.0 + 27 * 60.0 + 36.0, abs=1e-12
    )


def test_default_decimal_places_match_the_documented_signatures():
    assert ss.deg_to_dms(1.5) == ss.deg_to_dms(1.5, 3)
    assert ss.deg_to_hms(15.0) == ss.deg_to_hms(15.0, 4)


def test_allowed_decimal_places_are_zero_through_six():
    for d in (0, 1, 3, 6):
        assert isinstance(ss.deg_to_dms(0.0, d), tuple)
        assert isinstance(ss.deg_to_hms(0.0, d), tuple)

    # fraction counts units of 10**-decimals: 1.0005 deg = 1 deg 0' 1.800"
    assert ss.deg_to_dms(1.0005, 3) == ('+', 1, 0, 1, 800)
    assert ss.dms_to_deg('+', 1, 0, 1 + 800 / 1000.0) == pytest.approx(1.0005, abs=1e-15)
