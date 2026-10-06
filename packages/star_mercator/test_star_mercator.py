"""Published Mercator values, hand-derived projections, inverses and invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release."""
import math

import pytest

import star_mercator as sm


def test_snyder_clarke_1866_example():
    # Snyder, Map Projections: A Working Manual, p. 266. The printed x is
    # rounded to 0.1 m; the printed scale has seven decimal places.
    x, _ = sm.mercator_forward(35, -75, 180, 0, 6378206.4, 1 / 294.978698214)
    assert x == pytest.approx(11688673.7, abs=0.06)
    assert sm.mercator_scale(35, 0, 1 / 294.978698214) == pytest.approx(
        1.2194146, abs=6e-8
    )


def test_epsg_3857_square_and_origin():
    # EPSG:3857's published half-width is pi times its spherical radius.
    edge = 20037508.342789244
    assert sm.web_mercator_forward(0, -180) == pytest.approx((-edge, 0), abs=1e-8)
    assert sm.web_mercator_forward(0, 180) == pytest.approx((edge, 0), abs=1e-8)
    assert sm.web_mercator_forward(85.0511287798066, 0)[1] == pytest.approx(
        edge, abs=1e-7
    )
    # At the origin both the longitude difference and isometric latitude vanish.
    assert sm.web_mercator_forward(0, 0) == (0.0, 0.0)
    assert sm.mercator_forward(0, 37, 37) == (0.0, 0.0)
    assert sm.web_mercator_inverse(0, 0) == (0.0, 0.0)
    assert sm.mercator_inverse(0, 0) == (0.0, 0.0)


def test_sphere_coordinates_scale_and_true_scale():
    a = 6378137.0
    # At 45 degrees, tan(phi)=1; a quarter-turn has dlon=pi/2.
    assert sm.mercator_forward(45, 90, 0, 0, a, 0) == pytest.approx(
        (a * math.pi / 2, a * math.asinh(1)), abs=1e-8
    )
    # On a sphere k=cos(t)/cos(phi): cos(60)=1/2.
    assert sm.mercator_scale(60, 0, 0) == pytest.approx(2.0, abs=1e-14)
    assert sm.mercator_scale(0, 60, 0) == pytest.approx(0.5, abs=1e-14)
    for phi in (-60, 60):
        assert sm.mercator_scale(phi, 60, 0) == pytest.approx(1.0, abs=1e-14)
    # With t=60, both coordinates at 45 are half their t=0 values.
    x, y = sm.mercator_forward(45, 90, 0, 60, a, 0)
    assert (x, y) == pytest.approx(
        (a * math.pi / 4, a * math.asinh(1) / 2), abs=1e-8
    )
    assert sm.mercator_inverse(x, y, 0, 60, a, 0) == pytest.approx(
        (45, 90), abs=1e-12
    )


def test_ellipsoid_terms_by_hand():
    a, f, t, phi = 7000000.0, 0.02, 40.0, 30.0
    # e²=f(2-f); k0=cos(t)/sqrt(1-e² sin²(t)).
    # psi=asinh(tan(phi))-e atanh(e sin(phi)); x=a k0 dlon,
    # y=a k0 psi; point scale=k0 sqrt(1-e² sin²(phi))/cos(phi).
    e2 = f * (2 - f)
    e = math.sqrt(e2)
    tr, pr = math.radians(t), math.radians(phi)
    k0 = math.cos(tr) / math.sqrt(1 - e2 * math.sin(tr) ** 2)
    psi = math.asinh(math.tan(pr)) - e * math.atanh(e * math.sin(pr))
    xy = (a * k0 * math.pi / 3, a * k0 * psi)
    assert sm.mercator_forward(phi, 80, 20, t, a, f) == pytest.approx(
        xy, abs=1e-8
    )
    assert sm.mercator_scale(phi, t, f) == pytest.approx(
        k0 * math.sqrt(1 - e2 * math.sin(pr) ** 2) / math.cos(pr),
        abs=1e-14,
    )
    assert sm.mercator_inverse(*xy, 20, t, a, f) == pytest.approx(
        (phi, 80), abs=1e-11
    )


def test_true_scale_parallels_and_equatorial_scale():
    # k0 is chosen to cancel the parallel scale at either signed true-scale
    # latitude. Between those parallels the scale falls below one.
    assert sm.mercator_scale(0, 0) == pytest.approx(1.0, abs=1e-14)
    for phi in (-45, 45):
        assert sm.mercator_scale(phi, 45) == pytest.approx(1.0, abs=1e-14)
    assert sm.mercator_scale(0, 45) < 1
    assert sm.mercator_scale(60, 45) > 1
    assert sm.mercator_scale(-60, 45) > 1
    assert sm.mercator_scale(30, -45) == pytest.approx(
        sm.mercator_scale(30, 45), abs=1e-14
    )


def test_web_is_spherical_not_ellipsoidal():
    # at longitude 180 exactly the two differ by a full turn: Web Mercator keeps +180 (the edge of the EPSG:3857 square),
    # the ellipsoidal function reduces the difference from its central meridian to [-180, 180)
    assert sm.web_mercator_forward(0, 180)[0] == -sm.mercator_forward(0, 180, 0, 0, 6378137.0, 0)[0] > 0
    for lat, lon in ((0, 0), (48.86, 23), (-60, -130), (89.5, 179.999)):
        web = sm.web_mercator_forward(lat, lon)
        sphere = sm.mercator_forward(lat, lon, 0, 0, 6378137.0, 0)
        assert web == pytest.approx(sphere, abs=1e-8)       # one unit in the last place of 2e7 m is 4e-9 m
    web_x, web_y = sm.web_mercator_forward(48.86, 23)
    ell_x, ell_y = sm.mercator_forward(48.86, 23)
    assert web_x == ell_x
    # The sphere omits the positive e*atanh(e*sin(phi)) subtraction.
    assert 30000 < web_y - ell_y < 40000


@pytest.mark.parametrize("f,t", [(0.0, 0.0), (0.0, 60.0),
                                  (sm.WGS84_F, 0.0), (0.02, -40.0)])
def test_symmetry_radius_and_axes(f, t):
    for lat in (0, 17, 70, 89.5):
        positive = sm.mercator_forward(lat, 31, 11, t, 7000000, f)
        negative = sm.mercator_forward(-lat, 31, 11, t, 7000000, f)
        assert negative[0] == positive[0]
        assert negative[1] == -positive[1]
        # Both coordinates contain one multiplicative factor of a.
        doubled = sm.mercator_forward(lat, 31, 11, t, 14000000, f)
        assert doubled == pytest.approx(
            (2 * positive[0], 2 * positive[1]), abs=1e-8
        )
        # Longitude affects x alone; latitude affects y alone.
        assert sm.mercator_forward(lat, -41, -61, t, 7000000, f) == (
            positive
        )
        assert sm.mercator_forward(lat, 11, 11, t, 7000000, f)[0] == 0.0
        assert sm.mercator_forward(0, 31, 11, t, 7000000, f)[1] == 0.0


def test_wrapping_half_turn_and_inverse_image():
    assert sm.mercator_forward(10, -179, 179) == pytest.approx(
        sm.mercator_forward(10, 2, 0), abs=1e-9
    )
    # Half a turn is represented by -180 degrees in [-180, 180).
    for f, t in ((0.0, 0.0), (sm.WGS84_F, 45.0)):
        e2 = f * (2 - f)
        tr = math.radians(t)
        ak0 = 6378137.0 * math.cos(tr) / math.sqrt(
            1 - e2 * math.sin(tr) ** 2
        )
        x, y = sm.mercator_forward(0, 180, 0, t, 6378137, f)
        assert x == pytest.approx(-math.pi * ak0, abs=1e-8)
        assert y == 0.0
        assert sm.mercator_inverse(x, y, 0, t, 6378137, f) == (
            0.0, -180.0
        )
    assert sm.web_mercator_inverse(*sm.web_mercator_forward(0, 180)) == (
        0.0, -180.0
    )
    # Rounding just below -180 can produce +180 in the modulo expression;
    # the wrapper must still return the negative endpoint.
    assert sm._wrap180(-180.0 - math.ulp(180.0)) == -180.0
    assert sm._wrap180(181.0) == -179.0


@pytest.mark.parametrize("lat,lon,lon0", [
    (-89.5, -180, 0), (89.5, 180, 37), (-75, 179, -179),
    (-30, -120, 25), (0, 0, 0), (48.86, 75, -40),
    (75, -179, 179),
])
@pytest.mark.parametrize("f,t", [(0.0, 0.0), (0.0, 60.0),
                                  (sm.WGS84_F, 0.0), (0.02, 45.0)])
def test_ellipsoidal_and_spherical_round_trips(lat, lon, lon0, f, t):
    x, y = sm.mercator_forward(lat, lon, lon0, t, 6378137, f)
    recovered_lat, recovered_lon = sm.mercator_inverse(
        x, y, lon0, t, 6378137, f
    )
    displacement = (recovered_lon - lon + 180) % 360 - 180
    assert abs(recovered_lat - lat) < 1e-9
    assert abs(displacement) * math.cos(math.radians(lat)) < 1e-9
    assert -180 <= recovered_lon < 180


@pytest.mark.parametrize("lat,lon", [
    (-89.5, -180), (89.5, 180), (-60, -95),
    (0, 0), (48.86, 75), (85.0511287798066, 30),
])
def test_web_round_trips(lat, lon):
    recovered_lat, recovered_lon = sm.web_mercator_inverse(
        *sm.web_mercator_forward(lat, lon)
    )
    displacement = (recovered_lon - lon + 180) % 360 - 180
    assert abs(recovered_lat - lat) < 1e-9
    assert abs(displacement) * math.cos(math.radians(lat)) < 1e-9
    assert -180 <= recovered_lon < 180


def test_rhumb_straightness_and_monotonic_y():
    # Choose latitudes first and use their projected y as the equally spaced
    # isometric-latitude coordinate. A fixed x/y ratio defines a rhumb line.
    a, f, t = 6378137.0, sm.WGS84_F, 25.0
    ys = [sm.mercator_forward(lat, 0, 0, t, a, f)[1]
          for lat in (-30, 0, 30)]
    assert ys[0] < ys[1] < ys[2]
    points = []
    for y in ys:
        # x=y/4, so dlon=x/(a*k0), derived from the forward x formula.
        e2 = f * (2 - f)
        tr = math.radians(t)
        ak0 = a * math.cos(tr) / math.sqrt(1 - e2 * math.sin(tr) ** 2)
        lon = math.degrees(y / (4 * ak0))
        lat = (-30, 0, 30)[len(points)]
        points.append(sm.mercator_forward(lat, lon, 0, t, a, f))
    for x, y in points:
        assert x == pytest.approx(y / 4, abs=1e-9)
    assert points[0][0] < points[1][0] < points[2][0]


def test_isometric_latitude_derivative():
    a, f, t, phi = 6378137.0, 0.02, 35.0, math.radians(40.0)
    h = 1e-5  # radians; centered difference has O(h²) truncation error
    e2 = f * (2 - f)
    tr = math.radians(t)
    ak0 = a * math.cos(tr) / math.sqrt(1 - e2 * math.sin(tr) ** 2)
    # Differentiate asinh(tan(phi))-e*atanh(e*sin(phi)):
    # dy/dphi=a*k0*(1-e²)/((1-e² sin²(phi))*cos(phi)).
    expected = ak0 * (1 - e2) / (
        (1 - e2 * math.sin(phi) ** 2) * math.cos(phi)
    )
    upper = sm.mercator_forward(math.degrees(phi + h), 0, 0, t, a, f)[1]
    lower = sm.mercator_forward(math.degrees(phi - h), 0, 0, t, a, f)[1]
    assert (upper - lower) / (2 * h) == pytest.approx(expected, rel=2e-10)
