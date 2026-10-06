"""star_coverage against textbook figures and plane trigonometry done independently.
Verifies: R1, R2, R3 (README).

Textbook (Wertz, Space Mission Analysis and Design; any satellite-communications text): from geostationary altitude
(35 786 km above a 6378.137 km sphere) the Earth-central angle to the horizon is 81.3 deg, the nadir angle 8.7 deg, the
slant range to the horizon 41 679 km, and 42.4 % of the surface is in view; at 5 deg of minimum elevation the central
angle is 76.3 deg. From 400 km the horizon is 2294 km away (sqrt(2 R h + h^2)).
Independent method: the triangle centre - ground point - satellite solved with the law of cosines and of sines.
The comparison with pymap3d and PROJ on a sphere (400 cases) is in crosscheck_coverage.py."""
import math
import random

import pytest

import star_coverage as c

R, GEO = 6378.137, 35786.0


def test_geostationary_textbook_figures():
    assert abs(c.central_angle_deg(GEO) - 81.3) < 0.005 and abs(c.nadir_angle_deg(GEO) - 8.7) < 0.005
    assert abs(c.slant_range(GEO) - 41679) < 0.5 and abs(c.coverage_fraction(GEO) - 0.424) < 0.0005
    assert abs(c.central_angle_deg(GEO, 5.0) - 76.3) < 0.05
    assert c.slant_range(GEO, 90.0) == pytest.approx(GEO, rel=1e-15) and c.central_angle_deg(GEO, 90.0) == pytest.approx(0.0, abs=1e-12)
    assert c.coverage_fraction(GEO, 90.0) == pytest.approx(0.0, abs=1e-25)


def test_low_orbit_horizon_distance():
    assert abs(c.slant_range(400.0) - math.sqrt(2 * R * 400.0 + 400.0 ** 2)) < 1e-9 and abs(c.slant_range(400.0) - 2294.0) < 0.05
    assert abs(c.central_angle_deg(400.0) - math.degrees(math.acos(R / (R + 400.0)))) < 1e-12


def test_the_three_angles_add_up_to_ninety_degrees():
    rnd = random.Random(1)
    for _ in range(300):
        h, e = 10 ** rnd.uniform(1, 6), rnd.uniform(0, 90)
        assert c.central_angle_deg(h, e) + c.nadir_angle_deg(h, e) + e == pytest.approx(90.0, abs=1e-11)


def test_triangle_solved_independently_with_the_law_of_cosines():
    rnd = random.Random(2)
    for _ in range(300):
        h, e = 10 ** rnd.uniform(2, 5.6), rnd.uniform(0, 89.9)
        lam, rho, r = math.radians(c.central_angle_deg(h, e)), c.slant_range(h, e), R + h
        assert rho == pytest.approx(math.sqrt(R * R + r * r - 2 * R * r * math.cos(lam)), rel=1e-12)      # side opposite the centre
        assert math.sin(math.radians(c.nadir_angle_deg(h, e))) == pytest.approx(R * math.sin(lam) / rho, rel=1e-9, abs=1e-12)
        # angle at the ground point is 90 + e: cosine rule on that vertex
        assert r * r == pytest.approx(R * R + rho * rho + 2 * R * rho * math.sin(math.radians(e)), rel=1e-12)


def test_elevation_is_the_inverse_of_central_angle():
    rnd = random.Random(3)
    for _ in range(300):
        h, e = 10 ** rnd.uniform(2, 5.6), rnd.uniform(0, 90)
        assert c.elevation_deg(h, c.central_angle_deg(h, e)) == pytest.approx(e, abs=1e-10)
    assert c.elevation_deg(400.0, 0.0) == 90.0 and c.elevation_deg(400.0, 180.0) == -90.0
    assert c.elevation_deg(GEO, c.central_angle_deg(GEO)) == pytest.approx(0.0, abs=1e-12)
    assert c.elevation_deg(GEO, 85.0) < 0 < c.elevation_deg(GEO, 80.0)                    # beyond the horizon: negative


def test_coverage_area_and_fraction():
    lam = math.radians(c.central_angle_deg(GEO, 10.0))
    assert c.coverage_fraction(GEO, 10.0) == pytest.approx((1 - math.cos(lam)) / 2, rel=1e-13)
    assert c.footprint_area(GEO, 10.0) == pytest.approx(2 * math.pi * R * R * (1 - math.cos(lam)), rel=1e-13)
    assert c.footprint_area(GEO) == pytest.approx(4 * math.pi * R * R * 0.42436537951672, rel=1e-9)
    assert 0.0 < c.coverage_fraction(1e9) < 0.5 and c.coverage_fraction(1e9) == pytest.approx(0.5, abs=1e-5)   # never more than half
    # a low satellite sees a small flat disc: area tends to pi * (horizon distance)^2
    # exact closed form at zero elevation: cos(lam) = R / (R + h), so the cap area is 2 pi R^2 h / (R + h)
    for h in (1e-3, 1.0, 400.0, GEO):
        assert c.footprint_area(h) == pytest.approx(2 * math.pi * R * R * h / (R + h), rel=1e-12)
    previous = 1.0
    for e in range(0, 91, 5):
        f = c.coverage_fraction(800.0, e)
        assert f < previous or e == 0
        previous = f


def test_another_body_and_units():
    moon = 1737.4
    assert c.central_angle_deg(100.0, radius=moon) == pytest.approx(math.degrees(math.acos(moon / (moon + 100.0))), rel=1e-13)
    assert c.slant_range(400e3, 10.0, radius=R * 1e3) == pytest.approx(1e3 * c.slant_range(400.0, 10.0), rel=1e-13)       # metres
    assert c.central_angle_deg(400e3, 10.0, radius=R * 1e3) == pytest.approx(c.central_angle_deg(400.0, 10.0), rel=1e-13)
    assert c.EARTH_RADIUS_KM == 6378.137 and c.central_angle_deg(400.0) == c.central_angle_deg(400.0, 0.0, radius=6378.137)
