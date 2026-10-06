"""star_lcc against Snyder's printed example and independently computed cone geometry.

All other expectations follow from the formulas or symmetries stated beside the tests.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (one refusal message expectation)."""
import math
import random

import pytest

import star_lcc as sl


def test_snyder_clarke_1866_example():
    # Snyder, USGS Professional Paper 1395, p. 296; printed x and y have 0.1 m precision.
    args = (35, -75, 33, 45, 23, -96, 6378206.4, 1 / 294.978698214)
    x, y = sl.lcc_forward(*args)
    assert x == pytest.approx(1894410.9, abs=0.06, rel=0)
    assert y == pytest.approx(1564649.5, abs=0.06, rel=0)
    assert sl.lcc_scale(35, 33, 45, args[6], args[7]) == pytest.approx(
        0.9970171, abs=6e-8, rel=0
    )
    assert sl.lcc_inverse(x, y, *args[2:]) == pytest.approx((35, -75), abs=1e-9, rel=0)


@pytest.mark.parametrize("parallels,origin", [
    ((33, 45), (23, -96)),
    ((40, 40), (40, 179)),
    ((-33, -45), (-23, -96)),
])
def test_origin_is_exactly_zero(parallels, origin):
    # At the origin theta = 0 and rho = rho0, so x = rho sin(0) and y = rho0 - rho.
    p1, p2 = parallels
    lat0, lon0 = origin
    assert sl.lcc_forward(lat0, lon0, p1, p2, lat0, lon0) == (0.0, 0.0)


def test_standard_parallels_and_scale_shape():
    # Each standard parallel is tangent to the developed cone; between two
    # intersections the cone lies inside the surface, and outside them it lies above.
    for lat in (33, 45):
        assert sl.lcc_scale(lat, 33, 45) == pytest.approx(1.0, abs=1e-14, rel=0)
    assert sl.lcc_scale(39, 33, 45) < 1.0
    for lat in (20, 60):
        assert sl.lcc_scale(lat, 33, 45) > 1.0
    assert sl.lcc_scale(40, 40, 40) == pytest.approx(1.0, abs=1e-14, rel=0)
    for lat in (30, 50):
        assert sl.lcc_scale(lat, 40, 40) > 1.0


def test_meridian_symmetry_order_and_southern_mirror():
    east = sl.lcc_forward(35, -75, 33, 45, 23, -96)
    west = sl.lcc_forward(35, -117, 33, 45, 23, -96)
    # theta changes sign with dlon; sin is odd and cos is even.
    assert west == pytest.approx((-east[0], east[1]), abs=1e-9, rel=0)
    assert sl.lcc_forward(35, -75, 45, 33, 23, -96) == pytest.approx(
        east, abs=1e-8, rel=0
    )
    # Reversing all latitudes reverses n and rho, leaving x unchanged and negating y.
    assert sl.lcc_forward(-35, -75, -33, -45, -23, -96) == pytest.approx(
        (east[0], -east[1]), abs=1e-8, rel=0
    )
    lower = sl.lcc_forward(20, -96, 33, 45, 23, -96)
    upper = sl.lcc_forward(50, -96, 33, 45, 23, -96)
    assert abs(lower[0]) < 1e-9 and abs(upper[0]) < 1e-9
    assert lower[1] < 0 < upper[1]


def test_radius_scales_coordinates_but_not_point_scale():
    a = 6378137.0
    first = sl.lcc_forward(35, -75, 33, 45, 23, -96, a)
    twice = sl.lcc_forward(35, -75, 33, 45, 23, -96, 2 * a)
    # rho and rho0 each contain exactly one factor of a; their ratio in k cancels it.
    assert twice == pytest.approx(tuple(2 * v for v in first), rel=1e-14, abs=1e-9)
    assert sl.lcc_scale(35, 33, 45, a) == pytest.approx(
        sl.lcc_scale(35, 33, 45, 2 * a), abs=1e-14, rel=0
    )


@pytest.mark.parametrize("lat,dlon", [(40, 0), (50, 0), (50, 20), (30, -25)])
def test_spherical_tangent_cone_computed_by_hand(lat, dlon):
    p, a = 40, 6378137.0
    n = math.sin(math.radians(p))

    def rho(degrees):
        # f = 0: psi = asinh(tan(phi)); F is fixed by rho(p) = a / tan(p).
        psi_p = math.asinh(math.tan(math.radians(p)))
        psi = math.asinh(math.tan(math.radians(degrees)))
        return a / math.tan(math.radians(p)) * math.exp(n * (psi_p - psi))

    theta = n * math.radians(dlon)
    expected = (rho(lat) * math.sin(theta), rho(p) - rho(lat) * math.cos(theta))
    assert sl.lcc_forward(lat, dlon, p, p, p, 0, a, 0) == pytest.approx(
        expected, abs=1e-8, rel=0
    )
    # k = rho*n/(a*cos(phi)) on a sphere; this also checks the off-parallel scale.
    expected_k = rho(lat) * n / (a * math.cos(math.radians(lat)))
    assert sl.lcc_scale(lat, p, p, a, 0) == pytest.approx(
        expected_k, abs=2e-14, rel=0
    )


def test_ellipsoidal_cone_computed_independently():
    # Snyder's definitions: e²=f(2-f), m=cos(phi)/sqrt(1-e²sin²(phi)),
    # psi=asinh(tan(phi))-e*atanh(e*sin(phi)), n=log(m1/m2)/(psi2-psi1).
    # rho=a*m1*exp(n*(psi1-psi))/n; x=rho*sin(n*dlon),
    # y=rho0-rho*cos(n*dlon), and k=rho*n/(a*m).
    a, f = 6378137.0, 0.1
    e = math.sqrt(f * (2 - f))

    def psi(deg):
        phi = math.radians(deg)
        return math.asinh(math.tan(phi)) - e * math.atanh(e * math.sin(phi))

    def m(deg):
        phi = math.radians(deg)
        return math.cos(phi) / math.sqrt(1 - (e * math.sin(phi)) ** 2)

    n = math.log(m(20) / m(60)) / (psi(60) - psi(20))

    def rho(deg):
        return a * m(20) / n * math.exp(n * (psi(20) - psi(deg)))

    theta = n * math.radians(-25)
    expected = (rho(-40) * math.sin(theta), rho(10) - rho(-40) * math.cos(theta))
    assert sl.lcc_forward(-40, -25, 20, 60, 10, 0, a, f) == pytest.approx(
        expected, abs=1e-8, rel=0
    )
    assert sl.lcc_scale(-40, 20, 60, a, f) == pytest.approx(
        rho(-40) * n / (a * m(-40)), abs=2e-14, rel=0
    )


def test_date_line_difference_and_inverse_wrap():
    # -179 - 179 wraps to +2 degrees, the same difference as 2 - 0.
    across = sl.lcc_forward(10, -179, 33, 45, 23, 179)
    ordinary = sl.lcc_forward(10, 2, 33, 45, 23, 0)
    assert across == pytest.approx(ordinary, abs=1e-9, rel=0)
    lat, lon = sl.lcc_inverse(*across, 33, 45, 23, 179)
    assert lat == pytest.approx(10, abs=1e-9, rel=0)
    assert -180 <= lon < 180
    assert lon == pytest.approx(-179, abs=1e-9, rel=0)


@pytest.mark.parametrize("parallels,origin", [
    ((33, 45), (23, -96)),
    ((33, 33), (23, 179)),
    ((-33, -45), (-23, -96)),
    ((-40, -40), (-23, 179)),
])
@pytest.mark.parametrize("f", [0.0, sl.WGS84_F, 0.1])
def test_inverse_round_trips_both_hemispheres(parallels, origin, f):
    rnd = random.Random(1395)
    p1, p2 = parallels
    lat0, lon0 = origin
    near_sign = 1 if p1 > 0 else -1
    for lat_near in (-60, -20, 0, 35, 85):
        lat = near_sign * lat_near
        for dlon in (-60, -20, 0, 20, 60, rnd.uniform(-60, 60)):
            lon = (lon0 + dlon + 180) % 360 - 180
            x, y = sl.lcc_forward(lat, lon, p1, p2, lat0, lon0, f=f)
            got_lat, got_lon = sl.lcc_inverse(x, y, p1, p2, lat0, lon0, f=f)
            assert abs(got_lat - lat) < 1e-9
            # Near a pole, longitude error represents only cos(latitude) times
            # that angular displacement on the surface.
            displacement = (got_lon - lon + 180) % 360 - 180
            assert abs(displacement * math.cos(math.radians(lat))) < 1e-9
            assert -180 <= got_lon < 180


def test_inverse_refuses_apex_behind_cone_and_latitude_past_limit():
    a, p = 6378137.0, 30
    # On a spherical tangent cone, rho(p)=a/tan(p); y=rho0 is its apex.
    rho0 = a / math.tan(math.radians(p))
    # the apex computed in floating point is a hair off: refused either as the pole or as a latitude beyond 89 deg
    with pytest.raises(ValueError, match="pole|latitude"):
        sl.lcc_inverse(0, rho0, p, p, p, 0, a, 0)
    # twice as far North as the apex: behind the cone, where the longitude would exceed 180 deg from the central meridian
    with pytest.raises(ValueError, match="pole"):
        sl.lcc_inverse(0.0, 2.0 * rho0, p, p, p, 0, a, 0)
    with pytest.raises(ValueError, match="pole"):
        sl.lcc_inverse(0, 1e8, 33, 45, 23, -96)
    # South of the apex, atan2 gives theta=pi; theta/n exceeds pi.
    with pytest.raises(ValueError, match="pole"):
        sl.lcc_inverse(0, rho0 + 1, p, p, p, 0, a, 0)
    # Halving rho(89) moves beyond the permitted 89-degree latitude.
    _, y89 = sl.lcc_forward(89, 0, p, p, p, 0, a, 0)
    rho89 = rho0 - y89
    with pytest.raises(ValueError, match="latitude"):
        sl.lcc_inverse(0, rho0 - rho89 / 2, p, p, p, 0, a, 0)
