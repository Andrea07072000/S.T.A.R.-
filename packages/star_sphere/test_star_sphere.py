"""star_sphere against a published example and spherical triangles that can be solved by hand.
Verifies: R1, R2, R3 (README).

Published: Meeus, Astronomical Algorithms, Example 17.a: Arcturus (alpha 213.9154, delta +19.1825) and Spica
(201.2983, -11.1614) are 32.7930 deg apart. By hand: quarter circles between the pole and the equator, right-angled
triangles on the equator, the antipode. The comparison with ERFA and astropy on 600 pairs is in crosscheck_sphere.py."""
import math
import random

import pytest

import star_sphere as s

ARCTURUS, SPICA = (213.9154, 19.1825), (201.2983, -11.1614)


def test_meeus_example_17a():
    assert abs(s.separation_deg(*ARCTURUS, *SPICA) - 32.7930) < 5e-5
    assert s.separation_deg(*SPICA, *ARCTURUS) == pytest.approx(s.separation_deg(*ARCTURUS, *SPICA), abs=1e-13)


@pytest.mark.parametrize("p1, p2, sep, pa", [
    ((0, 0), (90, 0), 90.0, 90.0), ((0, 0), (270, 0), 90.0, 270.0), ((10, 0), (10, 35), 35.0, 0.0), ((10, 35), (10, 0), 35.0, 180.0),
    ((0, 0), (180, 0), 180.0, None), ((123, 45), (303, -45), 180.0, None), ((0, 90), (77, 0), 90.0, None),
    ((350, 0), (10, 0), 20.0, 90.0), ((10, 0), (-10, 0), 20.0, 270.0), ((0, 0), (0, 0), 0.0, 0.0), ((45, 60), (405 - 360, 60), 0.0, 0.0)])
def test_separations_and_position_angles_by_hand(p1, p2, sep, pa):
    assert s.separation_deg(*p1, *p2) == pytest.approx(sep, abs=1e-12)
    if pa is not None:
        assert s.position_angle_deg(*p1, *p2) == pytest.approx(pa, abs=1e-12)


def test_small_and_nearly_antipodal_separations_keep_their_digits():
    # the arc-cosine formula returns 0 for directions closer than 1e-6 deg and loses digits near 180 deg
    for d in (1e-3, 1e-6, 1e-9, 1e-12):
        assert s.separation_deg(40.0, 0.0, 40.0 + d, 0.0) == pytest.approx(d, rel=1e-6)
        assert s.separation_deg(40.0, 30.0, 40.0, 30.0 + d) == pytest.approx(d, rel=1e-3 if d < 1e-10 else 1e-6)
        assert 180.0 - s.separation_deg(40.0, 0.0, 220.0 + d, 0.0) == pytest.approx(d, rel=1e-3 if d < 1e-10 else 1e-6)
    lon, lat = 200.0, 55.0
    assert s.separation_deg(lon, lat, lon + 1e-6, lat) == pytest.approx(1e-6 * math.cos(math.radians(lat)), rel=1e-6)   # parallels shrink


def test_right_angled_triangle_on_the_equator():
    # from (0, 0): a point 30 deg East on the equator and a point 40 deg North; hypotenuse by Napier's rule
    hyp = s.separation_deg(30.0, 0.0, 0.0, 40.0)
    assert math.cos(math.radians(hyp)) == pytest.approx(math.cos(math.radians(30)) * math.cos(math.radians(40)), rel=1e-14)
    pa = s.position_angle_deg(30.0, 0.0, 0.0, 40.0)                       # looking back West-North-West
    assert 270.0 < pa < 360.0 and math.tan(math.radians(360 - pa)) == pytest.approx(math.sin(math.radians(30)) / math.tan(math.radians(40)), rel=1e-13)


def test_offset_is_the_inverse_of_separation_and_position_angle():
    rnd = random.Random(6)
    for _ in range(400):
        lon, lat = rnd.uniform(0, 360), math.degrees(math.asin(rnd.uniform(-0.99, 0.99)))
        pa, d = rnd.uniform(0, 360), rnd.uniform(1e-3, 179.9)
        lon2, lat2 = s.offset(lon, lat, pa, d)
        assert 0.0 <= lon2 < 360.0 and -90.0 <= lat2 <= 90.0
        assert s.separation_deg(lon, lat, lon2, lat2) == pytest.approx(d, abs=1e-10)
        assert abs((s.position_angle_deg(lon, lat, lon2, lat2) - pa + 180) % 360 - 180) * math.sin(math.radians(d)) < 1e-9


def test_offsets_by_hand():
    assert s.offset(10.0, 0.0, 90.0, 25.0) == pytest.approx((35.0, 0.0), abs=1e-12)        # East along the equator
    assert s.offset(10.0, 0.0, 270.0, 25.0) == pytest.approx((345.0, 0.0), abs=1e-12)
    assert s.offset(10.0, 20.0, 0.0, 30.0) == pytest.approx((10.0, 50.0), abs=1e-12)       # due North
    assert s.offset(10.0, 20.0, 180.0, 30.0) == pytest.approx((10.0, -10.0), abs=1e-12)
    assert s.offset(10.0, 20.0, 37.0, 0.0) == pytest.approx((10.0, 20.0), abs=1e-12)
    assert s.offset(10.0, 80.0, 0.0, 20.0) == pytest.approx((190.0, 80.0), abs=1e-10)      # over the pole
    lon, lat = s.offset(10.0, 20.0, 123.0, 180.0)
    assert (lon, lat) == pytest.approx((190.0, -20.0), abs=1e-9)                           # the antipode, whatever the direction
    assert s.offset(-10.0, 0.0, -90.0, 5.0) == pytest.approx((345.0, 0.0), abs=1e-12)      # negative longitude and angle accepted
