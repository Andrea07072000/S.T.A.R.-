"""star_ellipsoid against the published constants of WGS-84 and independent numerical work.
Verifies: R1, R2, R3 (README).

Published (NIMA TR8350.2, WGS-84 defining and derived constants): a = 6 378 137 m, 1/f = 298.257223563,
b = 6 356 752.3142 m, e^2 = 0.00669437999014, polar radius of curvature a^2/b = 6 399 593.6258 m, meridian quadrant
10 001 965.729 m. Independent method: the meridian arc is integrated numerically here from the meridian radius
(Simpson's rule), without the series. The comparison with pymap3d and PyGeodesy is in crosscheck_ellipsoid.py."""
import math

import pytest

import star_ellipsoid as e


def test_published_wgs84_constants():
    assert e.A == 6378137.0 and e.F == 1 / 298.257223563
    assert abs(e.B - 6356752.3142) < 5e-5 and abs(e.E2 - 0.00669437999014) < 5e-15
    assert abs(e.prime_vertical_radius(90) - 6399593.6258) < 5e-5 and abs(e.meridian_radius(90) - 6399593.6258) < 5e-5
    assert abs(e.MERIDIAN_QUADRANT - 10001965.729) < 5e-4 and e.meridian_arc(90) == pytest.approx(e.MERIDIAN_QUADRANT, rel=1e-15)


def test_radii_at_the_equator_and_at_the_poles_by_hand():
    assert e.prime_vertical_radius(0) == e.A and e.meridian_radius(0) == pytest.approx(e.A * (1 - e.E2), rel=1e-15)
    assert e.meridian_radius(0) == pytest.approx(e.B ** 2 / e.A, rel=1e-15)
    for lat in (90, -90):
        assert e.meridian_radius(lat) == pytest.approx(e.A ** 2 / e.B, rel=1e-15) and e.prime_vertical_radius(lat) == pytest.approx(e.A ** 2 / e.B, rel=1e-15)
        assert e.geocentric_radius(lat) == pytest.approx(e.B, rel=1e-15)
    assert e.geocentric_radius(0) == e.A and e.gaussian_radius(0) == pytest.approx(e.B, rel=1e-15)
    for lat in (-77.0, -30.0, 12.5, 45.0, 89.0):
        m, n = e.meridian_radius(lat), e.prime_vertical_radius(lat)
        assert m < n and e.gaussian_radius(lat) == pytest.approx(math.sqrt(m * n), rel=1e-14)
        assert e.meridian_radius(-lat) == m and e.geocentric_radius(-lat) == e.geocentric_radius(lat)


def test_geocentric_radius_is_the_distance_of_the_surface_point():
    for lat in (0.0, 10.0, 33.3, 45.0, 60.0, 89.9, -52.0):
        phi = math.radians(lat)
        n = e.prime_vertical_radius(lat)
        x, z = n * math.cos(phi), n * (1 - e.E2) * math.sin(phi)                    # the point of the ellipsoid at this latitude
        assert e.geocentric_radius(lat) == pytest.approx(math.hypot(x, z), rel=1e-14)
        assert e.geocentric_latitude(lat) == pytest.approx(math.degrees(math.atan2(z, x)), abs=1e-12)
        assert x * x / e.A ** 2 + z * z / e.B ** 2 == pytest.approx(1.0, rel=1e-14)       # it is on the ellipse
        beta = math.radians(e.parametric_latitude(lat))
        assert e.A * math.cos(beta) == pytest.approx(x, rel=1e-13) and e.B * math.sin(beta) == pytest.approx(z, rel=1e-13, abs=1e-8)


def test_auxiliary_latitudes_order_and_limits():
    for f in (e.geocentric_latitude, e.parametric_latitude, e.rectifying_latitude):
        assert f(0) == 0.0 and f(90) == pytest.approx(90.0, abs=1e-12) and f(-90) == pytest.approx(-90.0, abs=1e-12)
        assert f(-37.0) == pytest.approx(-f(37.0), abs=1e-13)
    for lat in (5.0, 30.0, 45.0, 70.0, 88.0):
        assert e.geocentric_latitude(lat) < e.rectifying_latitude(lat) < e.parametric_latitude(lat) < lat
    assert lat - e.geocentric_latitude(45.0) > 0 and 45.0 - e.geocentric_latitude(45.0) == pytest.approx(0.19242, abs=5e-6)   # the 11.5 arcminute maximum


def _simpson(lat, steps=2000):
    h = math.radians(lat) / steps
    f = lambda k: e.A * (1 - e.E2) / (1 - e.E2 * math.sin(k * h) ** 2) ** 1.5
    return h / 3 * (f(0) + f(steps) + 4 * sum(f(k) for k in range(1, steps, 2)) + 2 * sum(f(k) for k in range(2, steps, 2)))


@pytest.mark.parametrize("lat", [1.0, 15.0, 30.0, 45.0, 60.0, 75.0, 89.0, 90.0, -45.0])
def test_meridian_arc_agrees_with_a_numerical_integration_of_the_meridian_radius(lat):
    # the first version scaled the sine terms by the wrong factor and was 1.1 cm off at 45 degrees
    assert e.meridian_arc(lat) == pytest.approx(_simpson(lat), abs=2e-6)


def test_meridian_arc_properties():
    assert e.meridian_arc(0) == 0.0 and e.meridian_arc(-30) == -e.meridian_arc(30)
    for lat in (0.0, 20.0, 45.0, 80.0):                                      # the derivative of the arc is the meridian radius
        d = (e.meridian_arc(lat + 1e-4) - e.meridian_arc(lat - 1e-4)) / math.radians(2e-4)
        assert d == pytest.approx(e.meridian_radius(lat), rel=1e-8)
    assert e.rectifying_latitude(45.0) == pytest.approx(90.0 * e.meridian_arc(45.0) / e.MERIDIAN_QUADRANT, rel=1e-15)
    assert abs(e.meridian_arc(1.0) - 110574.4) < 0.05 and abs(e.meridian_arc(90) - e.meridian_arc(89) - 111693.9) < 0.05   # length of a degree
