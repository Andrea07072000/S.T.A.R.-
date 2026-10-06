"""star_utm against the supplied numerical example, hand-derived series and projection identities.
Standard library only.

Published: Snyder, Map Projections - A Working Manual, p. 269: Clarke 1866, latitude 40.5 N, longitude
73.5 W, central meridian 75 W, k0 = 0.9996 gives x = 127106.5 m, y = 4484124.4 m; tolerance 0.06 m.
Other checks use the stated facts, spherical closed forms, rational evaluation of the specified n^4
series, symmetries, scale invariance and inverses. Longitude errors near a pole are displacements.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release."""
import math
from fractions import Fraction

import pytest

import star_utm as st

A = 6378137.0
F = 1 / 298.257223563
K = 0.9996

# Rows are coefficients of n, n^2, n^3, n^4 in the specified series, not additional published data.
ALPHA = (
    ((1, 2), (-2, 3), (5, 16), (41, 180)),
    ((0, 1), (13, 48), (-3, 5), (557, 1440)),
    ((0, 1), (0, 1), (61, 240), (-103, 140)),
    ((0, 1), (0, 1), (0, 1), (49561, 161280)),
)
BETA = (
    ((1, 2), (-2, 3), (37, 96), (-1, 360)),
    ((0, 1), (1, 48), (1, 15), (-437, 1440)),
    ((0, 1), (0, 1), (17, 480), (-37, 840)),
    ((0, 1), (0, 1), (0, 1), (4397, 161280)),
)


def series_by_hand(a, f, k):
    # n = f/(2-f). Sum each rational polynomial exactly before rounding to a float.
    # R/(ak) = (1 + n^2/4 + n^4/64)/(1+n); e^2 = f(2-f).
    af, ff, kf = map(Fraction, (a, f, k))
    n = ff / (2 - ff)
    radius = af * kf * (1 + n ** 2 / 4 + n ** 4 / 64) / (1 + n)
    rows = []
    for table in (ALPHA, BETA):
        rows.append(tuple(float(sum(Fraction(p, q) * n ** j
                                    for j, (p, q) in enumerate(row, 1)))
                          for row in table))
    return math.sqrt(float(ff * (2 - ff))), float(radius), rows[0], rows[1]


def forward_by_hand(lat, dlon, a, f, k):
    # psi = asinh(tan(phi)) - e atanh(e sin(phi)); tan(chi) = sinh(psi).
    # The spherical TM of chi is eta = atanh(cos(chi) sin(lambda)),
    # xi = atan2(tan(chi), cos(lambda)); then add the four specified alpha harmonics.
    e, radius, alpha, _ = series_by_hand(a, f, k)
    phi, lam = map(math.radians, (lat, dlon))
    psi = math.asinh(math.tan(phi)) - e * math.atanh(e * math.sin(phi))
    xi = math.atan2(math.sinh(psi), math.cos(lam))
    eta = math.atanh(math.sin(lam) / math.cosh(psi))
    x = math.fsum([eta] + [c * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
                          for j, c in enumerate(alpha, 1)])
    y = math.fsum([xi] + [c * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
                         for j, c in enumerate(alpha, 1)])
    return radius * x, radius * y


def inverse_by_hand(x, y, lon0, a, f, k):
    # Subtract the beta harmonics. Recover lambda and conformal latitude by spherical TM.
    # Invert psi(phi) by bisection, independently of the implementation's Newton iteration.
    e, radius, _, beta = series_by_hand(a, f, k)
    xi, eta = y / radius, x / radius
    u = math.fsum([xi] + [-c * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
                         for j, c in enumerate(beta, 1)])
    v = math.fsum([eta] + [-c * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
                          for j, c in enumerate(beta, 1)])
    lam = math.atan2(math.sinh(v), math.cos(u))
    psi = math.asinh(math.sin(u) / math.hypot(math.sinh(v), math.cos(u)))
    lo, hi = -math.pi / 2, math.pi / 2
    for _ in range(100):
        mid = (lo + hi) / 2
        value = math.asinh(math.tan(mid)) - e * math.atanh(e * math.sin(mid))
        if value < psi:
            lo = mid
        else:
            hi = mid
    return math.degrees((lo + hi) / 2), (lon0 + math.degrees(lam) + 180) % 360 - 180


def assert_position(actual, lat, lon, tol):
    got_lat, got_lon = actual
    assert got_lat == pytest.approx(lat, rel=0, abs=tol)
    error = (got_lon - lon + 180) % 360 - 180
    assert abs(error * math.cos(math.radians(lat))) <= tol
    assert -180 <= got_lon < 180


def test_snyder_example_both_ways():
    args = (40.5, -73.5, -75.0, 6378206.4, 1 / 294.978698214)
    xy = st.tm_forward(*args)
    assert xy == pytest.approx((127106.5, 4484124.4), rel=0, abs=0.06)
    assert_position(st.tm_inverse(*xy, *args[2:]), 40.5, -73.5, 1e-9)


@pytest.mark.parametrize("f", [0.0, F, 1 / 32, 1 / 16, 0.1])
@pytest.mark.parametrize("a,k", [(1000.0, 0.5), (A, K), (1e9, 2.0)])
def test_each_ellipsoid_series_coefficient_by_rational_arithmetic(f, a, k):
    e, radius, alpha, beta, scale = st._ellipsoid(a, f, k)
    expected_e, expected_radius, expected_alpha, expected_beta = series_by_hand(a, f, k)
    assert e == pytest.approx(expected_e, rel=4e-16, abs=0)
    assert radius == pytest.approx(expected_radius, rel=5e-16, abs=0)
    assert alpha == pytest.approx(expected_alpha, rel=3e-15, abs=0)
    assert beta == pytest.approx(expected_beta, rel=3e-15, abs=0)
    assert scale == a * k


@pytest.mark.parametrize("tau", [-10.0, -1.0, -0.25, 0.0, 0.25, 1.0, 10.0])
@pytest.mark.parametrize("f", [0.0, F, 0.1])
def test_conformal_latitude_as_a_hyperbolic_difference(tau, f):
    # sinh(u-v) = sinh(u) cosh(v) - cosh(u) sinh(v), with u = asinh(tau).
    e = math.sqrt(f * (2 - f))
    expected = math.sinh(math.asinh(tau) - e * math.atanh(e * tau / math.hypot(1, tau)))
    assert st._conformal_tan(tau, e) == pytest.approx(expected, rel=2e-15, abs=1e-15)


@pytest.mark.parametrize("sign", [-1, 1])
def test_conformal_pole_limit_does_not_overflow(sign):
    # tau/hypot(1,tau) -> sign(tau); tan(chi)/tau -> exp(-e atanh(e)).
    e = math.sqrt(F * (2 - F))
    assert st._conformal_tan(sign * 1e300, e) / (sign * 1e300) == pytest.approx(
        math.exp(-e * math.atanh(e)), rel=3e-16, abs=0)


@pytest.mark.parametrize("lat,dlon", [(0, 0), (45, 0), (0, 1), (30, 7), (-60, -11), (89, 3)])
def test_spherical_closed_forms(lat, dlon):
    # For f=0, all alpha and beta vanish and R=a:
    # x/a = atanh(cos(phi) sin(lambda)); y/a = atan2(tan(phi), cos(lambda)).
    phi, lam = map(math.radians, (lat, dlon))
    expected = (A * math.atanh(math.cos(phi) * math.sin(lam)),
                A * math.atan2(math.tan(phi), math.cos(lam)))
    xy = st.tm_forward(lat, dlon, 0, A, 0, 1)
    assert xy == pytest.approx(expected, rel=0, abs=1e-8)
    assert_position(st.tm_inverse(*expected, 0, A, 0, 1), lat, dlon, 1e-12)


@pytest.mark.parametrize("f", [F, 1 / 32, 0.1])
@pytest.mark.parametrize("lat,dlon", [(0, 9), (17, 0), (23, 7), (-41, -11), (71, -5)])
def test_forward_harmonics_and_conformal_latitude_by_hand(f, lat, dlon):
    # The equator isolates the x harmonics, the central meridian the y harmonics;
    # mixed points exercise both hyperbolic factors, all four frequencies and both signs.
    a, k = 1000.0, 1.0
    got = st.tm_forward(lat, dlon, 0, a, f, k)
    expected = forward_by_hand(lat, dlon, a, f, k)
    assert tuple(v / a for v in got) == pytest.approx(
        tuple(v / a for v in expected), rel=0, abs=3e-15)


@pytest.mark.parametrize("f", [0.0, F, 1 / 32, 0.1])
@pytest.mark.parametrize("eta,xi", [(0, 0), (0.1, 0), (0, 0.7), (0.08, 0.4), (-0.06, -1.0)])
def test_inverse_beta_series_and_newton_against_bisection(f, eta, xi):
    # Prescribe rectifying coordinates, not a forward result: no cancellation between
    # matching forward/inverse mutations, and no assumption of exact inversion at large f.
    a, k = 1000.0, 1.0
    _, radius, _, _ = series_by_hand(a, f, k)
    x, y = radius * eta, radius * xi
    expected = inverse_by_hand(x, y, 179, a, f, k)
    assert_position(st.tm_inverse(x, y, 179, a, f, k), *expected, 2e-13)


def test_origin_and_defaults():
    # phi=lambda=0 makes every base coordinate and every sine/sinh correction zero.
    assert st.tm_forward(0, 3, 3) == (0.0, 0.0)
    assert st.tm_inverse(0, 0, 3) == (0.0, 3.0)
    assert st.tm_forward(37, 8, 3) == st.tm_forward(37, 8, 3, A, F, K)
    xy = st.tm_forward(37, 8, 3)
    assert st.tm_inverse(*xy, 3) == st.tm_inverse(*xy, 3, A, F, K)


@pytest.mark.parametrize("lat,dlon", [(13, 2), (43, 9), (78, 11)])
def test_parities_and_linear_scales(lat, dlon):
    # cos is even and sin is odd: lambda reversal changes x only; phi reversal changes y only.
    x, y = st.tm_forward(lat, dlon, 0)
    assert st.tm_forward(lat, -dlon, 0) == pytest.approx((-x, y), rel=0, abs=1e-9)
    assert st.tm_forward(-lat, dlon, 0) == pytest.approx((x, -y), rel=0, abs=1e-9)
    # R is linear in a and k; the dimensionless coordinates do not depend on either.
    assert st.tm_forward(lat, dlon, 0, 2 * A, F, K) == (2 * x, 2 * y)
    assert st.tm_forward(lat, dlon, 0, A, F, 2 * K) == (2 * x, 2 * y)
    assert st.tm_inverse(2 * x, 2 * y, 0, 2 * A, F, K) == st.tm_inverse(x, y, 0)
    assert st.tm_inverse(2 * x, 2 * y, 0, A, F, 2 * K) == st.tm_inverse(x, y, 0)


@pytest.mark.parametrize("sign", [-1, 1])
def test_poles_and_quarter_meridian(sign):
    # At a pole eta=0, xi=sign*pi/2; every sine harmonic vanishes, hence y=sign*R*pi/2.
    _, radius, _, _ = series_by_hand(A, F, K)
    x, y = st.tm_forward(sign * 90, 10, 3)
    assert abs(x) < 1e-6
    assert y == pytest.approx(sign * radius * math.pi / 2, rel=0, abs=2e-9)
    # The supplied rounded quarter-meridian length times k0 gives the supplied metre value.
    assert y == pytest.approx(sign * 9997964.943, rel=0, abs=1e-3)
    lat, lon = st.tm_inverse(0, sign * 9997964.943021, 3)
    assert lat == pytest.approx(sign * 90, rel=0, abs=1e-6)
    assert -180 <= lon < 180


@pytest.mark.parametrize("lat", [-89.999999, -80, -37, 0, 42, 84, 89.999999])
@pytest.mark.parametrize("dlon", [-11.5, -3, 0, 3, 11.5])
def test_wgs84_inverse_displacement(lat, dlon):
    # An inverse recovers the input; the longitude metric degenerates as cos(phi) at a pole.
    xy = st.tm_forward(lat, dlon, 0)
    assert_position(st.tm_inverse(*xy, 0), lat, dlon, 1e-9)


@pytest.mark.parametrize("lat,lon,lon0,dlon", [
    (10, -179, 179, 2), (-10, 179, -179, -2),
    (0, 180, -180, 0), (0, -180, 180, 0),
    (20, -178, 178, 4), (20, 178, -178, -4),
])
def test_date_line_differences_and_half_open_inverse(lat, lon, lon0, dlon):
    # Adding/subtracting 360 degrees does not change a longitude difference.
    xy = st.tm_forward(lat, lon, lon0)
    assert xy == st.tm_forward(lat, dlon, 0)
    assert_position(st.tm_inverse(*xy, lon0), lat, lon, 1e-9)
    if abs(lon) == 180:
        assert st.tm_inverse(*xy, lon0)[1] == -180.0


def test_all_zone_boundaries_and_centres():
    # Six-degree intervals starting at -180: boundary -180+6*j belongs to j+1.
    assert st.utm_zone(-180) == 1
    assert st.utm_zone(180) == 60
    for j in range(1, 60):
        boundary = -180 + 6 * j
        assert st.utm_zone(boundary - 1e-7) == j
        assert st.utm_zone(boundary) == j + 1
        assert st.utm_zone(boundary + 1e-7) == j + 1
    for z in range(1, 61):
        centre = 6 * z - 183
        assert st.utm_zone(centre) == z
        # At the central-meridian equator TM is zero, leaving only the false easting.
        assert st.utm_forward(0, centre) == (z, "N", 500000.0, 0.0)
        assert st.utm_inverse(z, "N", 500000, 0) == (0.0, float(centre))
        assert st.utm_inverse(z, "S", 500000, 10000000) == (0.0, float(centre))


def test_utm_supplied_values_and_equator_hemisphere():
    z, h, e, n = st.utm_forward(0, 0)
    assert (z, h) == (31, "N")
    assert e == pytest.approx(166021.443, rel=0, abs=1e-3)
    assert n == 0
    z, h, e, n = st.utm_forward(60, 9, 31)
    assert (z, h) == (31, "N")
    assert e == pytest.approx(834359.668, rel=0, abs=1e-3)
    # Zone 31 has central meridian 3; forced-zone coordinates are TM plus the false origin.
    x, y = st.tm_forward(60, 9, 3)
    assert (e, n) == (500000 + x, y)
    assert st.utm_forward(60, 9)[0] == 32
    z, h, e, n = st.utm_forward(-1e-9, 3)
    assert (z, h, e) == (31, "S", 500000.0)
    assert 9999999.9998 < n < 10000000
    assert st.utm_forward(-0.0, 3) == (31, "N", 500000.0, 0.0)


@pytest.mark.parametrize("z", [1, 2, 30, 31, 59, 60])
@pytest.mark.parametrize("lat", [-80, -47, -1e-9, 0, 31, 84])
@pytest.mark.parametrize("offset", [-3, -1, 0, 2.999999])
def test_utm_offsets_hemispheres_and_inverse(z, lat, offset):
    # UTM translates TM by 500000 east and, only in the south, 10000000 north.
    lon0 = 6 * z - 183
    lon = lon0 + offset
    x, y = st.tm_forward(lat, lon, lon0)
    result = st.utm_forward(lat, lon, z)
    expected_h = "S" if lat < 0 else "N"
    expected_n = y + 10000000 if lat < 0 else y
    assert result == (z, expected_h, 500000 + x, expected_n)
    assert_position(st.utm_inverse(*result), lat, lon, 1e-9)
