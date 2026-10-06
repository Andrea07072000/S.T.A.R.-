"""star_galactic against published examples, the IAU/Hipparcos definitions and the spherical geometry that follows.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release: an assertion on the
undefined longitude at the pole removed, a wrong wrap expectation replaced.

Published: Meeus, Astronomical Algorithms, Example 13.b: Nova Serpentis 1978, B1950.0 equatorial
alpha = 267.248917 deg, delta = -14.718944 deg, has galactic l = 12.9593 deg, b = +6.0463 deg in the
IAU 1958 (b1950) system. Tolerance 6e-5 deg per coordinate."""
# ruff: noqa: E741  (l is the standard symbol of galactic longitude)
import math
import random

import pytest

import star_galactic as sg


def test_meeus_example_13b_b1950_nova_serpentis():
    l, b = sg.equatorial_to_galactic(267.248917, -14.718944, "b1950")
    assert abs(l - 12.9593) < 6e-5 and abs(b - 6.0463) < 6e-5
    # The full-precision computed galactic coordinates must round-trip exactly.
    ra, dec = sg.galactic_to_equatorial(l, b, "b1950")
    assert ra == pytest.approx(267.248917, abs=1e-12)
    assert dec == pytest.approx(-14.718944, abs=1e-12)


@pytest.mark.parametrize("system, ra_p, dec_p, l_ncp", [
    ("b1950", 192.25, 27.4, 123.0),
    ("icrs", 192.85948, 27.12825, 122.93192),
], ids=["b1950", "icrs"])
def test_definitions_map_poles(system, ra_p, dec_p, l_ncp):
    # The galactic pole is the pole of the new frame, so its galactic latitude is +90.
    l, b = sg.equatorial_to_galactic(ra_p, dec_p, system)
    assert b == pytest.approx(90.0, abs=1e-12) and 0.0 <= l < 360.0           # the longitude is undefined there
    # The north celestial pole is the reference point of galactic longitude; its galactic longitude is
    # l_ncp and its angular distance from the galactic pole is 90 deg - dec_p, so its latitude is dec_p.
    l, b = sg.equatorial_to_galactic(0.0, 90.0, system)  # right ascension is irrelevant at the celestial pole
    assert l == pytest.approx(l_ncp, abs=1e-12) and b == pytest.approx(dec_p, abs=1e-12)
    # Conversely, the north celestial pole in galactic coordinates is (l_ncp, dec_p).
    ra, dec = sg.galactic_to_equatorial(l_ncp, dec_p, system)
    assert dec == pytest.approx(90.0, abs=1e-12) and 0.0 <= ra < 360.0


@pytest.mark.parametrize("system, ra_p, dec_p, l_ncp", [
    ("b1950", 192.25, 27.4, 123.0),
    ("icrs", 192.85948, 27.12825, 122.93192),
], ids=["b1950", "icrs"])
def test_south_poles_are_antipodal(system, ra_p, dec_p, l_ncp):
    # The south galactic pole is the antipode of the north galactic pole.
    l, b = sg.equatorial_to_galactic(sg._wrap360(ra_p + 180.0), -dec_p, system)
    assert b == pytest.approx(-90.0, abs=1e-12) and 0.0 <= l < 360.0
    # The south celestial pole is the antipode of the north celestial pole in galactic coordinates.
    ra, dec = sg.galactic_to_equatorial(sg._wrap360(l_ncp + 180.0), -dec_p, system)
    assert dec == pytest.approx(-90.0, abs=1e-12) and 0.0 <= ra < 360.0


def test_galactic_centre_is_ninety_degrees_from_the_pole():
    for system, ra_p, dec_p in (("b1950", 192.25, 27.4), ("icrs", 192.85948, 27.12825)):
        ra, dec = sg.galactic_to_equatorial(0.0, 0.0, system)
        # b = 0 means the point lies on the galactic equator, 90 deg from the galactic pole.
        # For unit vectors the cosine of the separation is the dot product, which must vanish.
        dot = (math.sin(math.radians(dec)) * math.sin(math.radians(dec_p)) +
               math.cos(math.radians(dec)) * math.cos(math.radians(dec_p)) *
               math.cos(math.radians(ra - ra_p)))
        assert abs(dot) < 1e-14
        # It must map back to the origin of the galactic frame.
        l, b = sg.equatorial_to_galactic(ra, dec, system)
        assert l == pytest.approx(0.0, abs=1e-12) and b == pytest.approx(0.0, abs=1e-12)


def test_negative_longitudes_and_full_circles_are_wrapped():
    l1, b1 = sg.equatorial_to_galactic(-90.0, 0.0, "icrs")
    l2, b2 = sg.equatorial_to_galactic(270.0, 0.0, "icrs")
    assert l1 == pytest.approx(l2, abs=1e-12) and b1 == pytest.approx(b2, abs=1e-12)
    l3, b3 = sg.galactic_to_equatorial(-90.0, 0.0, "icrs")
    l4, b4 = sg.galactic_to_equatorial(270.0, 0.0, "icrs")
    assert l3 == pytest.approx(l4, abs=1e-12) and b3 == pytest.approx(b4, abs=1e-12)
    assert sg.equatorial_to_galactic(360.0, 0.0, "icrs") == pytest.approx(sg.equatorial_to_galactic(0.0, 0.0, "icrs"), abs=1e-12)
    assert sg.equatorial_to_galactic(-360.0, 10.0, "b1950") == pytest.approx(sg.equatorial_to_galactic(0.0, 10.0, "b1950"), abs=1e-12)
    assert sg._wrap360(-1e-20) == 0.0 and sg._wrap360(360.0) == 0.0
    assert sg._wrap360(-90.0) == 270.0 and sg._wrap360(725.0) == 5.0


@pytest.mark.parametrize("system, ra_p, dec_p, l_ncp", [
    ("b1950", 192.25, 27.4, 123.0),
    ("icrs", 192.85948, 27.12825, 122.93192),
], ids=["b1950", "icrs"])
def test_at_a_target_pole_the_longitude_is_arbitrary_and_the_coordinate_is_exact(system, ra_p, dec_p, l_ncp):
    # Pole of the target (galactic) frame: longitude is arbitrary, latitude must be exact.
    l, b = sg.equatorial_to_galactic(ra_p, dec_p, system)
    assert b == pytest.approx(90.0, abs=1e-12) and 0.0 <= l < 360.0
    # Pole of the target (equatorial) frame: right ascension is arbitrary, declination must be exact.
    ra, dec = sg.galactic_to_equatorial(l_ncp, dec_p, system)
    assert dec == pytest.approx(90.0, abs=1e-12) and 0.0 <= ra < 360.0


def test_the_two_conversions_are_inverse():
    rnd = random.Random(42)
    for system in ("icrs", "b1950"):
        for _ in range(400):
            ra = rnd.uniform(0.0, 360.0)
            dec = math.degrees(math.asin(rnd.uniform(-0.999, 0.999)))
            l, b = sg.equatorial_to_galactic(ra, dec, system)
            ra2, dec2 = sg.galactic_to_equatorial(l, b, system)
            # Near a pole the longitude is ill-conditioned: scale by cos(latitude).
            dra = abs((ra2 - ra + 180.0) % 360.0 - 180.0) * abs(math.cos(math.radians(dec)))
            assert dra < 1e-12 and abs(dec2 - dec) < 1e-12

            lon = rnd.uniform(0.0, 360.0)
            lat = math.degrees(math.asin(rnd.uniform(-0.999, 0.999)))
            ra3, dec3 = sg.galactic_to_equatorial(lon, lat, system)
            lon2, lat2 = sg.equatorial_to_galactic(ra3, dec3, system)
            dlon = abs((lon2 - lon + 180.0) % 360.0 - 180.0) * abs(math.cos(math.radians(lat)))
            assert dlon < 1e-12 and abs(lat2 - lat) < 1e-12


def test_a_rotation_preserves_the_angle_between_two_directions():
    rnd = random.Random(7)

    def xyz(a, d):
        return (math.cos(math.radians(d)) * math.cos(math.radians(a)),
                math.cos(math.radians(d)) * math.sin(math.radians(a)),
                math.sin(math.radians(d)))

    for system in ("icrs", "b1950"):
        for _ in range(200):
            ra1 = rnd.uniform(0.0, 360.0)
            dec1 = math.degrees(math.asin(rnd.uniform(-0.999, 0.999)))
            ra2 = rnd.uniform(0.0, 360.0)
            dec2 = math.degrees(math.asin(rnd.uniform(-0.999, 0.999)))
            l1, b1 = sg.equatorial_to_galactic(ra1, dec1, system)
            l2, b2 = sg.equatorial_to_galactic(ra2, dec2, system)
            x1, y1, z1 = xyz(ra1, dec1)
            x2, y2, z2 = xyz(ra2, dec2)
            u1, v1, w1 = xyz(l1, b1)
            u2, v2, w2 = xyz(l2, b2)
            dot_eq = x1 * x2 + y1 * y2 + z1 * z2
            dot_gl = u1 * u2 + v1 * v2 + w1 * w2
            # A rotation is an orthogonal transformation: it preserves dot products.
            assert dot_eq == pytest.approx(dot_gl, abs=1e-14)
