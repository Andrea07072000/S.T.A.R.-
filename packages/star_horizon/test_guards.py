"""star_horizon: the parallactic angle off the meridian and the guards of the undefined and wrapped angles.
Verifies: R2, R4 (README).
Written by the reviewer after the first mutation run (0.81): the drafted tests left these lines unguarded.

Meeus, Astronomical Algorithms, eq. 14.1: tan q = sin H / (tan phi cos delta - sin delta cos H)."""
import math
import random

import pytest

import star_horizon as sh


def test_parallactic_angle_by_hand():
    # H = 90: tan q = 1 / (tan phi cos delta); on the equator of the sky (delta = 0) q = 90 - phi
    assert sh.parallactic_angle_deg(90.0, 0.0, 45.0) == pytest.approx(45.0, abs=1e-13)
    assert sh.parallactic_angle_deg(90.0, 0.0, 0.0) == pytest.approx(90.0, abs=1e-13)
    assert sh.parallactic_angle_deg(-90.0, 0.0, 0.0) == pytest.approx(-90.0, abs=1e-13)
    # phi = 30, delta = 60, H = 90: tan q = 1 / (tan 30 * cos 60) = 2 sqrt(3)
    assert sh.parallactic_angle_deg(90.0, 60.0, 30.0) == pytest.approx(math.degrees(math.atan(2.0 * math.sqrt(3.0))), abs=1e-13)


def test_parallactic_angle_follows_meeus_14_1():
    rnd = random.Random(141)
    for _ in range(300):
        ha, dec, lat = rnd.uniform(-179.0, 179.0), rnd.uniform(-85.0, 85.0), rnd.uniform(-85.0, 85.0)
        h, d, p = map(math.radians, (ha, dec, lat))
        den = math.tan(p) * math.cos(d) - math.sin(d) * math.cos(h)
        q = sh.parallactic_angle_deg(ha, dec, lat)
        assert -180.0 < q <= 180.0
        assert math.tan(math.radians(q)) * den == pytest.approx(math.sin(h), abs=1e-9 * max(1.0, abs(math.tan(math.radians(q)))))
        assert (q > 0.0) == (ha > 0.0) or abs(q) in (0.0, 180.0)             # West of the meridian the zenith is on the West side


def test_undefined_angles_are_returned_as_zero_even_with_rounding():
    # an observer at the pole looking at the celestial pole: the zenith, reached through rounded sines and cosines
    assert sh.hadec_to_azel(77.0, 90.0, 90.0) == (0.0, 90.0)
    assert sh.azel_to_hadec(123.0, 90.0, 90.0) == (0.0, 90.0)
    assert sh.hadec_to_azel(0.0, 30.0, 30.0)[0] == 0.0 and sh.azel_to_hadec(0.0, 40.0, 40.0)[0] == 0.0
    assert sh.parallactic_angle_deg(0.0, 30.0, 30.0) == 0.0 and sh.parallactic_angle_deg(33.0, 90.0, 90.0) == 0.0
    # one micro-degree away the angles are defined again
    assert sh.hadec_to_azel(0.0, 30.0 - 1e-6, 30.0)[0] == pytest.approx(180.0, abs=1e-6)
    assert sh.parallactic_angle_deg(0.0, 30.0 + 1e-6, 30.0) == pytest.approx(180.0, abs=1e-6)


def test_wrapped_ends_of_the_ranges():
    # due North below the pole: the hour angle is 12 h, returned as +180 and never as -180
    assert sh.azel_to_hadec(0.0, -45.0, 45.0) == (180.0, pytest.approx(0.0, abs=1e-13))
    assert sh.azel_to_hadec(-0.0, 10.0, 45.0)[0] == 180.0 and sh.azel_to_hadec(360.0, 10.0, 45.0)[0] == pytest.approx(180.0, abs=1e-12)
    # between the zenith and the pole, on the meridian: q = 180, whichever side the rounding comes from
    assert sh.parallactic_angle_deg(-0.0, 60.0, 40.0) == 180.0 and sh.parallactic_angle_deg(0.0, 60.0, 40.0) == 180.0
    # an hour angle of 1e-16 deg West puts the azimuth 1e-18 rad short of North: 0, never 360
    az, el = sh.hadec_to_azel(1e-16, 60.0, 50.0)
    assert az == 0.0 and el == pytest.approx(80.0, abs=1e-12)
    assert sh.hadec_to_azel(-1e-16, 60.0, 50.0)[0] == pytest.approx(0.0, abs=1e-12)
    assert sh.TINY == 1e-15
