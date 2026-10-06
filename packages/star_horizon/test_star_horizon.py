"""star_horizon against Meeus' published Venus example, geometric cases derivable by hand,
and the inverse relationship between the two horizon conversions.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release."""
import math
import random

import pytest

import star_horizon as sh


def test_meeus_example_13b_venus():
    # Meeus, Astronomical Algorithms (2nd ed.), Example 13.b
    az, el = sh.hadec_to_azel(64.352133, -6.719892, 38.921389)
    assert abs(az - 248.0337) < 6e-5 and abs(el - 15.1249) < 6e-5


def test_on_the_meridian_azimuth_and_elevation_by_hand():
    # For an object on the meridian (H = 0) the local spherical triangle collapses.
    # South of the zenith (delta < phi): A = 180 deg, h = 90 - phi + delta.
    # North of the zenith (delta > phi): A = 0 deg,   h = 90 + phi - delta.
    assert sh.hadec_to_azel(0.0, 20.0, 50.0) == pytest.approx((180.0, 60.0), abs=1e-13)
    assert sh.hadec_to_azel(0.0, 60.0, 50.0) == pytest.approx((0.0, 80.0), abs=1e-13)


def test_celestial_pole_and_equator_by_hand():
    # North celestial pole (delta = +90) is phi deg above the northern horizon.
    assert sh.hadec_to_azel(0.0, 90.0, 40.0) == pytest.approx((0.0, 40.0), abs=1e-13)
    # Object on celestial equator (delta = 0) due West (H = +90) or East (H = -90), on the horizon.
    assert sh.hadec_to_azel(90.0, 0.0, 30.0) == pytest.approx((270.0, 0.0), abs=1e-13)
    assert sh.hadec_to_azel(-90.0, 0.0, 30.0) == pytest.approx((90.0, 0.0), abs=1e-13)


def test_at_the_zenith_by_hand():
    # Zenith: H = 0, delta = phi. Elevation is exactly 90 deg; azimuth is conventionally 0.
    assert sh.hadec_to_azel(0.0, 30.0, 30.0) == pytest.approx((0.0, 90.0), abs=1e-13)


def test_parallactic_angle_on_the_meridian_by_hand():
    # On the meridian the great-circle through the object, zenith and pole lies in the meridian:
    # object south of zenith -> q = 0; object between zenith and pole -> q = 180.
    assert sh.parallactic_angle_deg(0.0, 20.0, 40.0) == pytest.approx(0.0, abs=1e-13)
    assert sh.parallactic_angle_deg(0.0, 60.0, 40.0) == pytest.approx(180.0, abs=1e-13)


def test_parallactic_angle_is_odd_in_hour_angle():
    # The spherical triangle is reflected in the meridian when H changes sign.
    q_pos = sh.parallactic_angle_deg(35.0, 20.0, 40.0)
    q_neg = sh.parallactic_angle_deg(-35.0, 20.0, 40.0)
    assert q_pos == pytest.approx(-q_neg, abs=1e-13)


def test_parallactic_angle_at_the_zenith_is_zero():
    # At the zenith the construction is degenerate and the function conventionally returns 0.
    assert sh.parallactic_angle_deg(0.0, 30.0, 30.0) == pytest.approx(0.0, abs=1e-13)


def test_sine_of_elevation_identity():
    # From the rotation underlying _turn: sin h = sin phi sin delta + cos phi cos delta cos H.
    phi, delta, H = 55.0, -13.0, 27.0
    _, el = sh.hadec_to_azel(H, delta, phi)
    s_el = math.sin(math.radians(el))
    s_rhs = (math.sin(math.radians(phi)) * math.sin(math.radians(delta)) +
             math.cos(math.radians(phi)) * math.cos(math.radians(delta)) * math.cos(math.radians(H)))
    assert abs(s_el - s_rhs) < 1e-14


def _norm_diff(a, b):
    """Shortest signed difference between two angles in degrees."""
    return ((a - b + 180.0) % 360.0) - 180.0


def test_the_two_conversions_are_mutually_inverse():
    # Hand-picked non-singular case.
    ha, dec = 30.0, 40.0
    lat = 50.0
    az, el = sh.hadec_to_azel(ha, dec, lat)
    ha2, dec2 = sh.azel_to_hadec(az, el, lat)
    assert abs(_norm_diff(ha2, ha)) * math.cos(math.radians(dec)) < 1e-12
    assert abs(dec2 - dec) < 1e-12

    az0, el0 = 123.0, 45.0
    ha3, dec3 = sh.azel_to_hadec(az0, el0, lat)
    az1, el1 = sh.hadec_to_azel(ha3, dec3, lat)
    assert abs(_norm_diff(az1, az0)) * math.cos(math.radians(el0)) < 1e-12
    assert abs(el1 - el0) < 1e-12


def test_random_round_trips_keep_angles():
    rnd = random.Random(42)
    for _ in range(400):
        ha = rnd.uniform(-180.0, 180.0)
        dec = math.degrees(math.asin(rnd.uniform(-0.95, 0.95)))
        lat = rnd.uniform(-75.0, 75.0)

        az, el = sh.hadec_to_azel(ha, dec, lat)
        assert 0.0 <= az < 360.0 and -90.0 <= el <= 90.0
        ha2, dec2 = sh.azel_to_hadec(az, el, lat)
        assert -180.0 < ha2 <= 180.0 and -90.0 <= dec2 <= 90.0
        assert abs(_norm_diff(ha2, ha)) * math.cos(math.radians(dec)) < 1e-11
        assert abs(dec2 - dec) < 1e-11

        az_b = rnd.uniform(0.0, 360.0)
        el_b = math.degrees(math.asin(rnd.uniform(-0.95, 0.95)))
        ha_b, dec_b = sh.azel_to_hadec(az_b, el_b, lat)
        az_c, el_c = sh.hadec_to_azel(ha_b, dec_b, lat)
        assert abs(_norm_diff(az_c, az_b)) * math.cos(math.radians(el_b)) < 1e-11
        assert abs(el_c - el_b) < 1e-11
