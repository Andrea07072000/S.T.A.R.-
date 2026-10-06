"""Published polar-stereographic examples, hand-derived geometry, inverses and invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release."""
import math

import pytest

import star_polar as sp


def angle_error(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def assert_position(actual, latitude, longitude, tolerance=1e-9):
    lat, lon = actual
    assert abs(lat - latitude) < tolerance
    # Longitude becomes ill-conditioned at a pole; compare its ground displacement.
    assert abs(angle_error(lon, longitude)) * abs(math.cos(math.radians(latitude))) < tolerance


def test_snyder_south_polar_example_and_inverse():
    # Snyder, Map Projections - A Working Manual, USGS PP 1395, p. 314:
    # International ellipsoid, true scale at 71 S, central meridian 100 W.
    args = ("S", -100, -71, 1.0, 6378388.0, 1 / 297)
    x, y = sp.ps_forward(-75, 150, *args)
    assert x == pytest.approx(-1540033.6, rel=0, abs=0.06)
    assert y == pytest.approx(-560526.4, rel=0, abs=0.06)
    assert_position(sp.ps_inverse(x, y, *args), -75, 150)


def test_spherical_axes_and_scale_by_hand():
    a = 6378137.0
    # At 60 degrees, rho = 2 a tan(45 - 60/2) = 2 a tan(15 degrees).
    rho = 2 * a * math.tan(math.radians(15))
    for pole, latitude, expected in (
        ("N", 60, ((0, -rho), (rho, 0))),
        ("S", -60, ((0, rho), (rho, 0))),
    ):
        for longitude, xy in zip((0, 90), expected):
            assert sp.ps_forward(latitude, longitude, pole, 0, None, 1, a, 0) == pytest.approx(
                xy, rel=0, abs=1e-8
            )
    # Spherical scale = 1/cos²(45 - |latitude|/2).
    assert sp.ps_scale(60, "N", None, 1, a, 0) == pytest.approx(
        1 / math.cos(math.radians(15)) ** 2, rel=0, abs=1e-14
    )
    assert sp.ps_scale(0, "N", None, 1, a, 0) == pytest.approx(2, rel=0, abs=1e-14)
    assert sp.ps_scale(-60, "S", None, 1, a, 0) == pytest.approx(
        1 / math.cos(math.radians(15)) ** 2, rel=0, abs=1e-14
    )


def test_true_scale_parallel_and_its_two_sides():
    for pole, sign in (("N", 1), ("S", -1)):
        assert sp.ps_scale(sign * 71, pole, sign * 71) == pytest.approx(
            1, rel=0, abs=1e-14
        )
        assert sp.ps_scale(sign * 80, pole, sign * 71) < 1
        assert sp.ps_scale(sign * 60, pole, sign * 71) > 1
        assert sp.ps_scale(sign * 90, pole, sign * 71) < 1
    assert sp.ps_scale(90, "N") == pytest.approx(1, rel=0, abs=1e-14)
    assert sp.ps_scale(-90, "S", None, 0.994) == pytest.approx(
        0.994, rel=0, abs=1e-14
    )


def test_spherical_true_scale_formula_including_pole_limit():
    a = 6378137.0
    # On a sphere, t(phi) = tan(45 - phi/2). True scale at 60 gives
    # C = a cos(60)/t(60); hence rho(phi) = C t(phi) and
    # k(phi) = rho(phi)/(a cos(phi)).
    t60 = math.tan(math.radians(15))
    c = a * math.cos(math.radians(60)) / t60
    for latitude in (0, 30, 60, 80):
        rho = c * math.tan(math.radians(45 - latitude / 2))
        x, y = sp.ps_forward(latitude, 0, "N", 0, 60, 1, a, 0)
        assert (x, y) == pytest.approx((0, -rho), rel=0, abs=1e-8)
        assert sp.ps_scale(latitude, "N", 60, 1, a, 0) == pytest.approx(
            rho / (a * math.cos(math.radians(latitude))), rel=0, abs=1e-14
        )
    # As phi tends to 90, t(phi)/cos(phi) tends to 1/2.
    assert sp.ps_scale(90, "N", 60, 1, a, 0) == pytest.approx(
        c / (2 * a), rel=0, abs=1e-14
    )


def test_ellipsoidal_formula_at_an_oblique_meridian():
    a, f, k0 = 6378137.0, 0.1, 0.8
    phi, ts, dlon = 30, 60, 40
    e = math.sqrt(f * (2 - f))

    def t(degrees):
        p = math.radians(degrees)
        v = e * math.sin(p)
        # exp(-psi) = tan(45 - phi/2) [(1+e sin(phi))/(1-e sin(phi))]^(e/2).
        return math.tan(math.radians(45 - degrees / 2)) * (
            (1 + v) / (1 - v)
        ) ** (e / 2)

    # True scale fixes C = a cos(ts)/(sqrt(1-e² sin²(ts)) t(ts)).
    c = a * math.cos(math.radians(ts)) / (
        math.sqrt(1 - (e * math.sin(math.radians(ts))) ** 2) * t(ts)
    )
    rho = k0 * c * t(phi)
    bearing = math.radians(dlon)
    assert sp.ps_forward(phi, 25, "N", -15, ts, k0, a, f) == pytest.approx(
        (rho * math.sin(bearing), -rho * math.cos(bearing)), rel=0, abs=1e-8
    )
    # Point scale is rho times the meridional ellipsoid factor, divided
    # by a cos(phi); both the eccentricity and k0 contribute.
    scale = rho * math.sqrt(1 - (e * math.sin(math.radians(phi))) ** 2) / (
        a * math.cos(math.radians(phi))
    )
    assert sp.ps_scale(phi, "N", ts, k0, a, f) == pytest.approx(
        scale, rel=0, abs=1e-14
    )
    assert sp.ps_scale(ts, "N", ts, k0, a, f) == pytest.approx(
        k0, rel=0, abs=1e-14
    )
    assert_position(sp.ps_inverse(*sp.ps_forward(phi, 25, "N", -15, ts, k0, a, f),
                                  "N", -15, ts, k0, a, f), phi, 25)


def test_mirror_rotation_and_linear_parameters():
    north = sp.ps_forward(42, 37, "N", -23, 71)
    south = sp.ps_forward(-42, 37, "S", -23, -71)
    assert south == pytest.approx((north[0], -north[1]), rel=0, abs=1e-8)
    assert sp.ps_scale(-42, "S", -71) == pytest.approx(
        sp.ps_scale(42, "N", 71), rel=0, abs=1e-14
    )
    assert sp.ps_forward(42, 137, "N", 77, 71) == pytest.approx(
        north, rel=0, abs=1e-8
    )
    x, y = sp.ps_forward(42, 37, "N", -23, None, 1, 6378137, 0)
    assert sp.ps_forward(42, 37, "N", -23, None, 0.5, 6378137, 0) == pytest.approx(
        (x / 2, y / 2), rel=0, abs=1e-8
    )
    assert sp.ps_forward(42, 37, "N", -23, None, 1, 2 * 6378137, 0) == pytest.approx(
        (2 * x, 2 * y), rel=0, abs=1e-8
    )
    assert sp.ps_scale(42, "N", None, 0.5, 6378137, 0) == pytest.approx(
        sp.ps_scale(42, "N", None, 1, 6378137, 0) / 2, rel=0, abs=1e-14
    )
    assert sp.ps_scale(42, "N", None, 1, 2 * 6378137, 0) == pytest.approx(
        sp.ps_scale(42, "N", None, 1, 6378137, 0), rel=0, abs=1e-14
    )


def test_poles_and_longitude_wrapping():
    for pole, latitude in (("N", 90), ("S", -90)):
        for longitude in (-180, -35, 0, 77, 180):
            assert sp.ps_forward(latitude, longitude, pole) == (0.0, 0.0)
        assert sp.ps_inverse(0, 0, pole, 45) == (latitude, 45.0)
    for pole, latitude in (("N", 60), ("S", -60)):
        for longitude in (-180, -179.999, -30, 0, 90, 179.999, 180):
            xy = sp.ps_forward(latitude, longitude, pole)
            result = sp.ps_inverse(*xy, pole)
            assert_position(result, latitude, longitude)
            assert -180 <= result[1] < 180
    assert sp.ps_inverse(*sp.ps_forward(60, 180, "N"), "N")[1] == -180.0
    assert sp.ps_inverse(*sp.ps_forward(60, -180, "N"), "N")[1] == -180.0


def test_inverse_over_both_hemispheres_and_near_the_pole():
    for pole, sign in (("N", 1), ("S", -1)):
        for ts in (None, sign * 71):
            for latitude in (sign * 20, sign * 45, sign * 80, sign * 89.999999, sign * 90):
                for longitude in (-157, -11, 0, 83, 170):
                    lon0 = -35
                    xy = sp.ps_forward(latitude, longitude, pole, lon0, ts)
                    result = sp.ps_inverse(*xy, pole, lon0, ts)
                    if abs(latitude) == 90:
                        assert result == (latitude, float(lon0))
                    else:
                        assert_position(result, latitude, longitude)


def test_ups_published_poles_and_hand_derived_offsets():
    # DMA TM 8358.2 defines k0 = 0.994, false coordinates 2,000,000 m
    # and central meridian zero; rho is zero at either pole.
    assert sp.ups_forward(90, 77) == ("N", 2000000.0, 2000000.0)
    assert sp.ups_forward(-90, 5) == ("S", 2000000.0, 2000000.0)
    # At longitude zero on the north map y = -rho; at longitude 180
    # on the south map y = -rho. Adding the false northing gives these
    # values from the WGS-84 ellipsoidal rho formula.
    assert sp.ups_forward(84, 0) == pytest.approx(
        ("N", 2000000.0, 1333272.296), rel=0, abs=1e-3
    )
    assert sp.ups_forward(-80, 180) == pytest.approx(
        ("S", 2000000.0, 887048.863), rel=0, abs=1e-3
    )


def test_ups_selection_offsets_and_inverse():
    assert sp.ups_forward(0, 0)[0] == "N"
    assert sp.ups_forward(-0.001, 0)[0] == "S"
    for latitude, longitude in ((84, 0), (70, 65), (0, -40), (-0.001, 80),
                                (-70, -95), (-80, 180)):
        pole, east, north = sp.ups_forward(latitude, longitude)
        assert pole == ("N" if latitude >= 0 else "S")
        # UPS is the pole-centred projection with k0 = 0.994 and
        # 2,000,000 m added to each planar coordinate.
        x, y = sp.ps_forward(latitude, longitude, pole, 0, None, 0.994)
        assert (east, north) == pytest.approx(
            (2000000 + x, 2000000 + y), rel=0, abs=1e-9
        )
        assert_position(sp.ups_inverse(pole, east, north), latitude, longitude)
