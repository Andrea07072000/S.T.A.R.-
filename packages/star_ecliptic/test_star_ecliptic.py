"""star_ecliptic against published examples, the polynomials summed by hand and rotations that can be done by hand.
Verifies: R1, R2, R3 (README).

Published: Meeus, Astronomical Algorithms, Example 13.a (Pollux: alpha 116.328942, delta 28.026183, epsilon 23.4392911
deg -> lambda 113.215630, beta 6.684170) and Example 22.a (1987 April 10, 0h TD, JD 2446895.5: mean obliquity
23 deg 26' 27.407" = 84387.407"). The comparison with ERFA, astropy, SPICE and skyfield is in crosscheck_ecliptic.py."""
import math
import random

import pytest

import star_ecliptic as se

EPS_MEEUS = 23.4392911 * 3600.0
J2000 = 2451545.0


def test_meeus_example_13a_both_ways():
    lon, lat = se.equatorial_to_ecliptic(116.328942, 28.026183, EPS_MEEUS)
    assert abs(lon - 113.215630) < 6e-7 and abs(lat - 6.684170) < 6e-7
    ra, dec = se.ecliptic_to_equatorial(113.215630, 6.684170, EPS_MEEUS)
    assert abs(ra - 116.328942) < 6e-7 and abs(dec - 28.026183) < 6e-7


def test_meeus_example_22a_mean_obliquity_iau1980():
    assert abs(se.mean_obliquity_arcsec(2446895.5, 0.0, "iau1980") - 84387.407) < 5e-4


def test_polynomials_summed_by_hand():
    assert se.mean_obliquity_arcsec(J2000, 0.0, "iau1980") == 84381.448 and se.mean_obliquity_arcsec(J2000) == 84381.406
    # T = +1: 84381.448 - 46.8150 - 0.00059 + 0.001813  and  84381.406 - 46.836769 - 0.0001831 + 0.00200340 - 0.000000576 - 0.0000000434
    assert se.mean_obliquity_arcsec(J2000 + 36525, 0.0, "iau1980") == pytest.approx(84334.634223, abs=1e-9)
    assert se.mean_obliquity_arcsec(J2000 + 36525, 0.0, "iau2006") == pytest.approx(84334.5710506806, abs=1e-9)
    # T = -2: 84381.448 + 93.63 - 0.00236 - 0.014504  and  84381.406 + 93.673538 - 0.0007324 - 0.0160272 - 0.000009216 + 0.0000013888
    assert se.mean_obliquity_arcsec(J2000 - 73050, 0.0, "iau1980") == pytest.approx(84475.061136, abs=1e-9)
    assert se.mean_obliquity_arcsec(J2000 - 73050, 0.0, "iau2006") == pytest.approx(84475.0627705728, abs=1e-9)
    assert se.mean_obliquity_arcsec(J2000, 0.0, model="iau2006") != se.mean_obliquity_arcsec(J2000, 0.0, model="iau1980")


def test_day_and_fraction_add_up_and_the_obliquity_decreases():
    whole = se.mean_obliquity_arcsec(2460000.5 + 0.25)
    assert se.mean_obliquity_arcsec(2460000.5, 0.25) == pytest.approx(whole, abs=1e-10)
    assert se.mean_obliquity_arcsec(2460000.5, -0.75) == pytest.approx(se.mean_obliquity_arcsec(2459999.75), abs=1e-10)
    per_day = se.mean_obliquity_arcsec(2460001.5) - se.mean_obliquity_arcsec(2460000.5)
    assert per_day == pytest.approx(-46.84 / 36525.0, rel=1e-3)             # 0.47 arcsec per year, decreasing
    assert se.mean_obliquity_arcsec(2460000.5, 1.0) == pytest.approx(se.mean_obliquity_arcsec(2460001.5), abs=1e-10)


@pytest.mark.parametrize("eps_deg", [0.0, 10.0, 23.4392911, 45.0, 60.0])
def test_rotations_by_hand(eps_deg):
    eps = eps_deg * 3600.0
    assert se.equatorial_to_ecliptic(0.0, 0.0, eps) == pytest.approx((0.0, 0.0), abs=1e-13)            # the equinox does not move
    assert se.equatorial_to_ecliptic(180.0, 0.0, eps) == pytest.approx((180.0, 0.0), abs=1e-13)
    assert se.equatorial_to_ecliptic(90.0, 0.0, eps) == pytest.approx((90.0, -eps_deg), abs=1e-13)     # the equator is below the ecliptic there
    assert se.equatorial_to_ecliptic(270.0, 0.0, eps) == pytest.approx((270.0, eps_deg), abs=1e-13)
    assert se.ecliptic_to_equatorial(90.0, 0.0, eps) == pytest.approx((90.0, eps_deg), abs=1e-13)      # the summer solstice point
    if eps_deg:
        assert se.equatorial_to_ecliptic(123.0, 90.0, eps) == pytest.approx((90.0, 90.0 - eps_deg), abs=1e-12)   # the celestial pole
        assert se.ecliptic_to_equatorial(55.0, 90.0, eps) == pytest.approx((270.0, 90.0 - eps_deg), abs=1e-12)   # the pole of the ecliptic
    else:
        assert se.equatorial_to_ecliptic(123.0, 45.0, eps) == pytest.approx((123.0, 45.0), abs=1e-13)


def test_the_two_conversions_are_inverse_and_keep_angles():
    rnd = random.Random(13)
    for _ in range(400):
        ra, dec = rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-0.999, 0.999)))
        eps = rnd.uniform(0.0, 324000.0)
        lon, lat = se.equatorial_to_ecliptic(ra, dec, eps)
        assert 0.0 <= lon < 360.0 and -90.0 <= lat <= 90.0
        ra2, dec2 = se.ecliptic_to_equatorial(lon, lat, eps)
        assert abs((ra2 - ra + 180.0) % 360.0 - 180.0) * math.cos(math.radians(dec)) < 1e-12 and abs(dec2 - dec) < 1e-12
        # a rotation keeps the angle to the axis: x = cos(lat) cos(lon) is the same in both frames
        assert math.cos(math.radians(lat)) * math.cos(math.radians(lon)) == pytest.approx(math.cos(math.radians(dec)) * math.cos(math.radians(ra)), abs=1e-15)


def test_negative_longitudes_are_accepted_and_wrapped():
    assert se.equatorial_to_ecliptic(-90.0, 0.0, 36000.0) == pytest.approx((270.0, 10.0), abs=1e-13)
    lon = se.equatorial_to_ecliptic(360.0, 0.0, 36000.0)[0]
    assert 0.0 <= lon < 360.0 and min(lon, 360.0 - lon) < 1e-13
    assert se._wrap360(-1e-20) == 0.0 and se._wrap360(360.0) == 0.0 and se._wrap360(-90.0) == 270.0 and se._wrap360(725.0) == 5.0


def test_at_a_pole_the_latitude_is_exact_and_the_longitude_is_in_range():
    # with an obliquity of 90 deg the point (90, 0) of the equator is the south pole of the ecliptic: its longitude is undefined
    lon, lat = se.equatorial_to_ecliptic(90.0, 0.0, 324000.0)
    assert lat == pytest.approx(-90.0, abs=1e-12) and 0.0 <= lon < 360.0
    lon, lat = se.ecliptic_to_equatorial(270.0, 0.0, 324000.0)
    assert lat == pytest.approx(-90.0, abs=1e-12) and 0.0 <= lon < 360.0
