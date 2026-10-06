"""star_moon against a published example and the known shape of the lunar orbit.
Verifies: R1, R2, R3 (README).

Published: Vallado, Fundamentals of Astrodynamics and Applications, Example 5-3 (Moon position vector): 1994 April 28,
0h TDB (JD 2449470.5) -> (-134240.626, -311571.590, -126693.785) km in the mean equator and equinox of date.
Known facts about the orbit (any astronomy text): distance between about 356 400 km and 406 700 km; inclination to the
ecliptic 5.1 deg, so the declination never exceeds 23.44 + 5.15 = 28.6 deg; sidereal month 27.32 days.
The comparison with JPL DE440, astropy and PyEphem on 2002 dates is in crosscheck_moon.py."""
import math

import pytest

import star_moon as m

JD, PUBLISHED = 2449470.5, (-134240.626, -311571.590, -126693.785)


def test_vallado_example_5_3():
    v = m.moon_vector_km(JD)
    assert len(v) == 3 and all(abs(a - b) < 1e-3 for a, b in zip(v, PUBLISHED))            # printed to the metre
    assert m.moon_vector_km(2449470.0, 0.5) == v and m.moon_vector_km(2449471, -0.5) == v
    assert m.moon_distance_km(JD) == pytest.approx(math.hypot(*PUBLISHED), abs=1e-3)
    ra, dec = m.moon_ra_dec_deg(JD)
    assert ra == pytest.approx(math.degrees(math.atan2(PUBLISHED[1], PUBLISHED[0])) % 360, abs=1e-7)
    assert dec == pytest.approx(math.degrees(math.asin(PUBLISHED[2] / math.hypot(*PUBLISHED))), abs=1e-7)


def test_distance_and_declination_stay_in_the_known_ranges_for_a_century():
    lo, hi, dec_max = math.inf, 0.0, 0.0
    for k in range(0, 36525, 3):
        jd = m.JD_1950 + k
        r = m.moon_distance_km(jd)
        ra, dec = m.moon_ra_dec_deg(jd)
        lo, hi, dec_max = min(lo, r), max(hi, r), max(dec_max, abs(dec))
        assert 0.0 <= ra < 360.0 and r == pytest.approx(math.hypot(*m.moon_vector_km(jd)), rel=1e-14)
    assert 355000 < lo < 358500 and 405000 < hi < 407500 and 28.0 < dec_max < 28.9


def test_the_moon_goes_round_in_a_sidereal_month():
    ra0 = m.moon_ra_dec_deg(2460000.5)[0]
    turned, prev = 0.0, ra0
    for k in range(1, 2733):                                   # 27.32 days in steps of 0.01 day
        ra = m.moon_ra_dec_deg(2460000.5, k * 0.01)[0]
        turned += (ra - prev + 180) % 360 - 180
        prev = ra
    assert turned == pytest.approx(360.0, abs=4.0)             # one turn in right ascension, within the series' own accuracy
    a, b = m.moon_vector_km(2460000.5), m.moon_vector_km(2460000.5, 1.0)
    cosang = sum(x * y for x, y in zip(a, b)) / (math.hypot(*a) * math.hypot(*b))
    assert 11.0 < math.degrees(math.acos(cosang)) < 15.5       # about 13.2 deg per day, faster at perigee


def test_series_constants_are_the_published_ones():
    assert m.LONGITUDE[0] == (6.29, 134.9, 477198.85) and m.LATITUDE[0] == (5.13, 93.3, 483202.03) and m.PARALLAX[0] == (0.0518, 134.9, 477198.85)
    assert [t[0] for t in m.LONGITUDE] == [6.29, -1.27, 0.66, 0.21, -0.19, -0.11] and [t[0] for t in m.LATITUDE] == [5.13, 0.28, -0.28, -0.17]
    assert [t[0] for t in m.PARALLAX] == [0.0518, 0.0095, 0.0078, 0.0028] and m.EARTH_RADIUS_KM == 6378.137
    assert [t[1:] for t in m.LONGITUDE] == [(134.9, 477198.85), (259.2, -413335.38), (235.7, 890534.23), (269.9, 954397.70),
                                            (357.5, 35999.05), (186.6, 966404.05)]
    assert [t[1:] for t in m.LATITUDE] == [(93.3, 483202.03), (228.2, 960400.87), (318.3, 6003.18), (217.6, -407332.20)]
    assert [t[1:] for t in m.PARALLAX] == [t[1:] for t in m.LONGITUDE[:4]]                # the parallax terms share the first four arguments
    # mean distance from the mean parallax 0.9508 deg
    assert m.EARTH_RADIUS_KM / math.sin(math.radians(0.9508)) == pytest.approx(384360, abs=10)
