"""star_geodesic against a published line and against lengths that can be checked by hand.
Verifies: R1, R2, R3 (README).

Published: the line Flinders Peak - Buninyong of the Australian geodetic manuals (Geoscience Australia / ICSM GDA
technical manual): Flinders Peak 37 57 03.72030 S, 144 25 29.52440 E; Buninyong 37 39 10.15610 S, 143 55 35.38390 E;
ellipsoidal distance 54972.271 m, forward azimuth 306 52 05.37, reverse azimuth 127 10 25.07 (GRS80: its flattening
differs from WGS-84 in the tenth digit, less than 0.1 mm on this line).
The comparison with PROJ, GeographicLib and PyGeodesy on 840 problems is in crosscheck_geodesic.py."""
import math
import random

import pytest

import star_geodesic as g


def dms(d, m, s):
    return (abs(d) + m / 60 + s / 3600) * (1 if d >= 0 else -1)


FLINDERS = (dms(-37, 57, 3.72030), dms(144, 25, 29.52440))
BUNINYONG = (dms(-37, 39, 10.15610), dms(143, 55, 35.38390))
DIST, AZ12, AZ21 = 54972.271, dms(306, 52, 5.37), dms(127, 10, 25.07)


def ang(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def test_published_line_inverse():
    s, a1, a2 = g.inverse(*FLINDERS, *BUNINYONG)
    assert abs(s - DIST) < 5e-4 and ang(a1, AZ12) * 3600 < 0.006 and ang(a2, AZ21 + 180.0) * 3600 < 0.006
    s, a1, a2 = g.inverse(*BUNINYONG, *FLINDERS)                           # the same line walked backwards
    assert abs(s - DIST) < 5e-4 and ang(a1, AZ21) * 3600 < 0.006 and ang(a2, AZ12 + 180.0) * 3600 < 0.006


def test_published_line_direct():
    lat, lon, a2 = g.direct(*FLINDERS, AZ12, DIST)
    # the published azimuth is rounded to 0.01 arcsec: over 55 km that is 2.7 mm, i.e. about 1e-4 arcsec of position
    assert abs(lat - BUNINYONG[0]) * 3600 < 1.2e-4 and abs(lon - BUNINYONG[1]) * 3600 < 1.2e-4
    assert ang(a2, AZ21 + 180.0) * 3600 < 0.006


def test_equator_and_meridian_lengths_by_hand():
    a, f = 6378137.0, 1 / 298.257223563
    assert g.inverse(0, 0, 0, 1) == pytest.approx((a * math.radians(1), 90.0, 90.0), abs=1e-9)    # the equator is a circle
    assert g.inverse(0, 10, 0, -80)[0] == pytest.approx(a * math.pi / 2, abs=1e-8)
    assert g.inverse(0, 10, 0, -80)[1:] == (270.0, 270.0)
    # meridian quadrant of the ellipsoid from its series in the third flattening n (Helmert), independent of Vincenty
    n = f / (2 - f)
    quadrant = math.pi * a / (2 * (1 + n)) * (1 + n ** 2 / 4 + n ** 4 / 64 + n ** 6 / 256)
    s, a1, a2 = g.inverse(0, 25, 90, 25)
    assert abs(s - quadrant) < 1e-6 and abs(quadrant - 10001965.729) < 1e-3 and (a1, a2) == (0.0, 0.0)
    assert g.inverse(-90, 0, 0, 0)[0] == pytest.approx(quadrant, abs=1e-6)
    assert g.inverse(45, 7, -45, 7)[1:] == (180.0, 180.0)
    lat, lon, az = g.direct(0, 25, 0, quadrant)
    assert abs(lat - 90.0) < 1e-9
    lat, lon, az = g.direct(0, 170, 90, a * math.radians(20))
    assert abs(lat) < 1e-12 and abs(lon - (-170.0)) < 1e-9 and az == pytest.approx(90.0, abs=1e-9)   # across the antimeridian


def test_longitude_wraps_and_results_are_in_range():
    assert g.inverse(10, 179, 12, -179) == pytest.approx(g.inverse(10, -181, 12, -179), abs=1e-6)
    assert g.inverse(10, 179, 12, -179)[0] == pytest.approx(g.inverse(10, -1, 12, 1)[0], abs=1e-6)
    assert g.inverse(10, 360, 12, 2) == pytest.approx(g.inverse(10, 0, 12, 2), abs=1e-6)
    rnd = random.Random(3)
    for _ in range(200):
        lat, lon, az, s = rnd.uniform(-90, 90), rnd.uniform(-360, 360), rnd.uniform(-360, 360), rnd.uniform(0, 2e7)
        la2, lo2, az2 = g.direct(lat, lon, az, s)
        assert -90.0 <= la2 <= 90.0 and -180.0 <= lo2 < 180.0 and 0.0 <= az2 < 360.0


def test_direct_and_inverse_are_consistent_over_the_globe():
    rnd = random.Random(11)
    for _ in range(300):
        lat, lon = math.degrees(math.asin(rnd.uniform(-0.999, 0.999))), rnd.uniform(-180, 180)
        az, s = rnd.uniform(0, 360), 10 ** rnd.uniform(0, 7.2)
        la2, lo2, az2 = g.direct(lat, lon, az, s)
        s_back, az_back, az2_back = g.inverse(lat, lon, la2, lo2)
        assert abs(s_back - s) < 2e-6 + 1e-11 * s
        lateral = math.radians(ang(az_back, az)) * min(s, 6.4e6)          # azimuth error as metres at the far end
        assert lateral < 5e-6 and math.radians(ang(az2_back, az2)) * min(s, 6.4e6) < 5e-6


def test_short_baselines_keep_micrometre_precision():
    # found by the cross-check: with the plain 1e-12 rad tolerance a 0.7 m line was 2.7 micrometres off
    north = g.inverse(18.5, -160.5, 18.5 + 1e-5, -160.5)
    e2 = g.F * (2 - g.F)
    radius = g.A * (1 - e2) / (1 - e2 * math.sin(math.radians(18.500005)) ** 2) ** 1.5     # meridian radius of curvature
    assert north[0] == pytest.approx(radius * math.radians(1e-5), abs=2e-8) and north[1:] == (0.0, 0.0)
    for az in (0.0, 37.0, 90.0, 201.5, 333.0):
        la2, lo2, _ = g.direct(48.7, -25.9, az, 1.0)
        s, a1, _ = g.inverse(48.7, -25.9, la2, lo2)
        assert abs(s - 1.0) < 2e-8 and ang(a1, az) * 3600 < 0.02           # float spacing of a latitude in degrees is 1.6 nm


def test_coincident_points_and_poles():
    assert g.inverse(10, 20, 10, 20) == (0.0, 0.0, 0.0) and g.inverse(-90, 5, -90, 77) == (0.0, 0.0, 0.0)
    assert g.inverse(90, -180, 90, 180) == (0.0, 0.0, 0.0) and g.inverse(10, 20, 10, 380 - 360) == (0.0, 0.0, 0.0)
    assert g.direct(10, 20, 123, 0) == pytest.approx((10.0, 20.0, 123.0), abs=1e-12)
    s, a1, a2 = g.inverse(90, 0, 89, 180)
    assert abs(s - 111693.865) < 1e-3 and a2 == 180.0                     # leaving the pole towards 180 E
    la, lo, az = g.direct(89, 0, 0, 2 * 111693.86491426684)
    assert abs(la - 89.0) < 1e-9 and abs(abs(lo) - 180.0) < 1e-6 and az == pytest.approx(180.0, abs=1e-6)   # over the pole


def test_nearly_antipodal_points_raise_and_never_return_an_unconverged_value():
    for case in ((0, 0, 0, 180), (0, 0, 0.5, 179.7), (30, 10, -30, -170), (0, 0, 0.2, 179.9), (90, 0, -90, 0), (-90, 33, 90, -12)):
        with pytest.raises(RuntimeError, match="antipodal"):
            g.inverse(*case)
    # one degree away along the equator the iteration converges again
    assert g.inverse(0, 0, 0, 179)[0] == pytest.approx(6378137.0 * math.radians(179), abs=1e-6)
