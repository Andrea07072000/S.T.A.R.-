"""star_sun against a published example, the calendar of the seasons and geometry that can be checked by hand.
Verifies: R1, R2, R3, R4 (README).

Published: Vallado, Fundamentals of Astrodynamics and Applications, Example 5-1 (Sun position vector): 2006 April 2,
0h UTC (JD 2453827.5) -> 0.9771945, 0.1924424, 0.0834308 AU in the mean equator and equinox of date.
Seasons: the equinoxes and solstices of 2000 and 2024 at the instants published by the USNO; the tolerance used
(0.012 deg in right ascension) corresponds to about 17 minutes of solar motion, so the test checks the series, not the minute.
The comparison with JPL DE440 (SPICE), astropy and PyEphem on 402 dates is in crosscheck_sun.py."""
import math

import pytest

import star_sun as s

VALLADO_JD, VALLADO = 2453827.5, (0.9771945, 0.1924424, 0.0834308)


def jd(y, mo, d, h=0, mi=0):
    """Julian date of a Gregorian calendar date (Fliegel-Van Flandern integer formula), independent of the module."""
    a = (14 - mo) // 12
    yy, mm = y + 4800 - a, mo + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045 - 0.5 + (h + mi / 60) / 24


def test_vallado_example_5_1():
    v = s.sun_vector_au(VALLADO_JD)
    assert all(abs(a - b) < 1.2e-6 for a, b in zip(v, VALLADO)) and jd(2006, 4, 2) == VALLADO_JD
    assert s.sun_vector_au(2453827.0, 0.5) == v and s.sun_vector_au(2453828, -0.5) == v             # day + fraction
    ra, dec = s.sun_ra_dec_deg(VALLADO_JD)
    assert abs(ra - math.degrees(math.atan2(VALLADO[1], VALLADO[0]))) < 1e-4
    assert abs(dec - math.degrees(math.asin(VALLADO[2] / math.sqrt(sum(c * c for c in VALLADO))))) < 1e-4


@pytest.mark.parametrize("when, ra_expected, dec_expected", [
    ((2000, 3, 20, 7, 35), 0.0, 0.0), ((2000, 6, 21, 1, 48), 90.0, 23.439), ((2000, 9, 22, 17, 27), 180.0, 0.0),
    ((2000, 12, 21, 13, 37), 270.0, -23.439), ((2024, 3, 20, 3, 6), 0.0, 0.0), ((2024, 6, 20, 20, 51), 90.0, 23.436),
    ((2024, 9, 22, 12, 44), 180.0, 0.0), ((2024, 12, 21, 9, 21), 270.0, -23.436)])
def test_published_equinoxes_and_solstices(when, ra_expected, dec_expected):
    ra, dec = s.sun_ra_dec_deg(jd(*when))
    assert abs((ra - ra_expected + 180) % 360 - 180) < 0.012 and abs(dec - dec_expected) < 0.006
    assert 0.0 <= ra < 360.0


def test_distance_follows_the_earth_orbit():
    r = lambda *d: math.sqrt(sum(c * c for c in s.sun_vector_au(jd(*d))))
    assert abs(r(2024, 1, 3, 0, 39) - 0.98331) < 1e-4            # perihelion 2024 (USNO: 0.9833070 AU)
    assert abs(r(2024, 7, 5, 5, 6) - 1.01673) < 1e-4             # aphelion 2024 (USNO: 1.0167255 AU)
    assert all(0.9832 < r(2010, m, 15) < 1.0168 for m in range(1, 13))


def test_valid_range_is_1950_to_2050_inclusive():
    assert s.JD_1950 == jd(1950, 1, 1) == 2433282.5 and s.JD_2050 == jd(2050, 1, 1) == 2469807.5 and s.J2000 == jd(2000, 1, 1, 12)
    for ok in (s.JD_1950, s.JD_2050):
        assert len(s.sun_vector_au(ok)) == 3 and len(s.sun_ra_dec_deg(ok)) == 2
    assert s.sun_vector_au(2469807.0, 0.5) == s.sun_vector_au(s.JD_2050)


@pytest.mark.parametrize("sun, inc, raan, beta", [
    ((1, 0, 0), 90, 90, 90.0), ((1, 0, 0), 90, -90, -90.0), ((1, 0, 0), 90, 0, 0.0), ((0, 0, 1), 0, 0, 90.0),
    ((0, 0, 1), 180, 0, -90.0), ((0, 0, 5), 60, 123, 30.0), ((0, -3, 0), 90, 0, 90.0), ((0, -3, 0), 30, 0, 30.0),
    ((0, 1, 0), 30, 0, -30.0), ((1, 0, 0), 30, 90, 30.0), ((1, 1, 0), 90, 90, 45.0), ((1, 0, 0), 51.6, 0, 0.0),
    ((1, 0, 0), 90, 360, 0.0), ((2, 0, 0), 90, -270, 90.0)])
def test_beta_angle_by_hand(sun, inc, raan, beta):
    assert abs(s.beta_angle_deg(sun, inc, raan) - beta) < 1e-9


def test_beta_is_the_complement_of_the_angle_to_the_orbit_normal_and_ignores_the_sun_distance():
    sun = s.sun_vector_au(VALLADO_JD)
    inc, raan = math.radians(97.8), math.radians(250.0)
    h = (math.sin(inc) * math.sin(raan), -math.sin(inc) * math.cos(raan), math.cos(inc))
    node = (math.cos(raan), math.sin(raan), 0.0)                                        # the node direction lies in the orbit
    assert abs(sum(a * b for a, b in zip(h, node))) < 1e-15
    expected = 90.0 - math.degrees(math.acos(sum(a * b for a, b in zip(sun, h)) / math.sqrt(sum(c * c for c in sun))))
    assert abs(s.beta_angle_deg(sun, 97.8, 250.0) - expected) < 1e-9
    assert s.beta_angle_deg([c * 1e-200 for c in sun], 97.8, 250.0) == pytest.approx(expected, abs=1e-9)
    assert s.beta_angle_deg([c * 1e200 for c in sun], 97.8, 250.0) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("r_sat, sun, expected", [
    ((-7000, 0, 0), (1, 0, 0), True), ((7000, 0, 0), (1, 0, 0), False), ((0, 7000, 0), (1, 0, 0), False),
    ((-7000, 6378.1, 0), (1, 0, 0), True), ((-7000, 6378.2, 0), (1, 0, 0), False), ((-1, 6378.2, 0), (1, 0, 0), False),
    ((-7000, 0, -6378.1), (1, 0, 0), True), ((-7000, 4600, 4600), (1, 0, 0), False), ((-7000, 4500, 4500), (1, 0, 0), True),
    ((0, 0, -42164), (0, 0, 9), True), ((0, 0, 42164), (0, 0, 9), False), ((-42164, 0, 0), (1, 1, 0), False),
    ((-30000, -30000, 0), (1, 1, 0), True), ((-6378.137, 0, 0), (1, 0, 0), True), ((0, 6378.137, 0), (1, 0, 0), False)])
def test_cylindrical_shadow_by_hand(r_sat, sun, expected):
    assert s.in_shadow(r_sat, sun) is expected
    assert s.in_shadow(list(r_sat), [c * 1.495978707e8 for c in sun]) is expected       # only the direction of the Sun counts


def test_shadow_scales_with_the_body_and_the_unit():
    assert s.EARTH_RADIUS_KM == 6378.137
    assert s.in_shadow((-3000, 1700, 0), (1, 0, 0), 1737.4) is True and s.in_shadow((-3000, 1800, 0), (1, 0, 0), 1737.4) is False
    assert s.in_shadow((-7.0e6, 6.3e6, 0), (1, 0, 0), 6378137.0) is True                # metres
    assert s.in_shadow((-7000, 0, 0), s.sun_vector_au(VALLADO_JD)) is True              # anti-Sun side of the X axis in April


def test_array_like_vectors_are_accepted():
    class Arr:                                               # behaves like a numeric array without being a Sequence
        def __init__(self, v): self.v = v
        def __len__(self): return len(self.v)
        def __getitem__(self, i): return self.v[i]
    assert s.in_shadow(Arr([-7000.0, 0, 0]), Arr([1, 0, 0])) is True and s.beta_angle_deg(Arr([1, 0, 0]), 90, 90) == 90.0
