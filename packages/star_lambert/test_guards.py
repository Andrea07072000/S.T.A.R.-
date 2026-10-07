"""Guard tests of star_lambert added by the reviewer on 2026-10-07, after the corrected mutation runner measured the
package at 0.84, below the present 0.85 gate. Every expected value comes from a circular orbit, for which the answer
is known in closed form: speed sqrt(mu / r), tangential, and time of flight = angle / sqrt(mu / r^3)."""
import math

import pytest

import star_lambert as sl


def circular(r, mu, angle, plane="xy", retrograde=False):
    """r1, r2, time of flight, v1 and v2 for a body on a circular orbit of radius r swept through `angle` (rad)."""
    n = math.sqrt(mu / r ** 3)
    vc = math.sqrt(mu / r)
    s = -1.0 if retrograde else 1.0
    c1, s1 = 1.0, 0.0
    c2, s2 = math.cos(s * angle), math.sin(s * angle)

    def place(c, sn):
        return (r * c, r * sn, 0.0) if plane == "xy" else (r * c, 0.0, r * sn)

    def speed(c, sn):
        return (-s * vc * sn, s * vc * c, 0.0) if plane == "xy" else (-s * vc * sn, 0.0, s * vc * c)

    return place(c1, s1), place(c2, s2), angle / n, speed(c1, s1), speed(c2, s2)


def close(a, b, tol):
    return max(abs(x - y) for x, y in zip(a, b)) <= tol


@pytest.mark.parametrize("r,mu", [(7000.0, sl.MU_EARTH), (1.0, 1.0), (0.1, 1e-3), (1.0, 0.5), (1.0, 16.0), (42164.0, sl.MU_EARTH), (1.5e8, 1.32712440018e11)])
@pytest.mark.parametrize("degrees", [10.0, 30.0, 90.0, 150.0, 170.0])
def test_short_way_on_a_circular_orbit(r, mu, degrees):
    r1, r2, tof, v1, v2 = circular(r, mu, math.radians(degrees))
    got1, got2 = sl.lambert(r1, r2, tof, mu=mu, prograde=True)
    vc = math.sqrt(mu / r)
    assert close(got1, v1, 1e-7 * vc) and close(got2, v2, 1e-7 * vc)      # mu 0.5 and tof below 1 s are valid inputs; so is a small radius


@pytest.mark.parametrize("r,mu", [(7000.0, sl.MU_EARTH), (1.0, 1.0), (0.1, 1e-3)])
@pytest.mark.parametrize("degrees", [200.0, 270.0, 330.0])
def test_long_way_is_taken_when_the_direction_asks_for_it(r, mu, degrees):
    """The same two positions reached by going the other way round: a retrograde circular orbit through 360 - angle."""
    r1, r2, tof, v1, v2 = circular(r, mu, math.radians(degrees), retrograde=True)      # r2 is at -degrees: seen prograde, a transfer of 360 - degrees
    got1, got2 = sl.lambert(r1, r2, tof, mu=mu, prograde=False)
    vc = math.sqrt(mu / r)
    assert close(got1, v1, 1e-7 * vc) and close(got2, v2, 1e-7 * vc)
    # and prograde through the long way: a prograde circular orbit through `degrees` (r2 is then at +degrees, below the x axis for angles above 180)
    r1, r2, tof, v1, v2 = circular(r, mu, math.radians(degrees))
    got1, got2 = sl.lambert(r1, r2, tof, mu=mu, prograde=True)
    assert close(got1, v1, 1e-7 * vc) and close(got2, v2, 1e-7 * vc)


@pytest.mark.parametrize("degrees", [30.0, 90.0, 150.0])
def test_a_polar_transfer_has_no_z_component_of_the_cross_product(degrees):
    """In the x-z plane r1 x r2 has no z component: `prograde` then means the short way, and its negation the long way."""
    r, mu = 7000.0, sl.MU_EARTH
    vc = math.sqrt(mu / r)
    r1, r2, tof, v1, v2 = circular(r, mu, math.radians(degrees), plane="xz")
    got1, got2 = sl.lambert(r1, r2, tof, mu=mu, prograde=True)
    assert close(got1, v1, 1e-7 * vc) and close(got2, v2, 1e-7 * vc)
    long_way = math.radians(360.0 - degrees)                                           # the same end points, the other way round
    back1, back2, tof_long, w1, w2 = circular(r, mu, long_way, plane="xz", retrograde=True)
    assert close(back2, r2, 1e-9 * r)
    got1, got2 = sl.lambert(r1, r2, tof_long, mu=mu, prograde=False)
    assert close(got1, w1, 1e-7 * vc) and close(got2, w2, 1e-7 * vc)


def test_small_positive_cross_product_is_still_prograde():
    """Unit radius: the z component of r1 x r2 is 0.5, below 1; it is its SIGN that chooses the way."""
    r1, r2, tof, v1, v2 = circular(1.0, 1.0, math.radians(30.0))
    assert r1[0] * r2[1] - r1[1] * r2[0] == pytest.approx(0.5)
    got1, _ = sl.lambert(r1, r2, tof, mu=1.0, prograde=True)
    assert close(got1, v1, 1e-9)
    r1, r2, tof, v1, v2 = circular(1.0, 1.0, math.radians(30.0), retrograde=True)       # r2 at -30 degrees: cross product -0.5, short way for a retrograde body
    got1, _ = sl.lambert(r1, r2, tof, mu=1.0, prograde=False)
    assert close(got1, v1, 1e-9)


def test_stumpff_functions_at_the_edges_of_their_series():
    for z in (1e-8, -1e-8, 5e-9, -5e-9, 0.0):                # at and inside the threshold the series is used: accurate to rounding
        assert sl._stumpff_c(z) == pytest.approx(0.5 - z / 24, abs=2e-16)
        assert sl._stumpff_s(z) == pytest.approx(1 / 6 - z / 120, abs=2e-16)
    for z in (1e-4, 0.5, 2.0, 30.0):                         # outside: the closed forms, checked against their definitions
        s = math.sqrt(z)
        assert sl._stumpff_c(z) == pytest.approx((1 - math.cos(s)) / z, rel=1e-15) and sl._stumpff_s(z) == pytest.approx((s - math.sin(s)) / s ** 3, rel=1e-15)
        assert sl._stumpff_c(-z) == pytest.approx((math.cosh(s) - 1) / z, rel=1e-15) and sl._stumpff_s(-z) == pytest.approx((math.sinh(s) - s) / s ** 3, rel=1e-15)
    assert sl._stumpff_c(4 * math.pi ** 2) == pytest.approx(0.0, abs=1e-17) and sl._stumpff_c(math.pi ** 2) == pytest.approx(2 / math.pi ** 2, rel=1e-15)
    assert sl._stumpff_s(math.pi ** 2) == pytest.approx(1 / math.pi ** 2, rel=1e-15)
    assert sl._stumpff_c(1e-6) == pytest.approx(0.5 - 1e-6 / 24, rel=1e-9) and sl._stumpff_c(-1e-6) == pytest.approx(0.5 + 1e-6 / 24, rel=1e-9)   # the two branches join


def test_parallel_and_opposite_positions_are_refused_as_degenerate():
    found_above = found_below = 0
    for k in range(1, 400):                                  # positions whose computed cosine leaves [-1, 1] by rounding
        a = (0.1 * k, 0.3 * k + 0.7, 1.1 * k)
        na = math.sqrt(sum(x * x for x in a))
        cosine = sum(x * x for x in a) / (na * na)
        b = tuple(3.0 * x for x in a)
        nb = math.sqrt(sum(x * x for x in b))
        cosine = sum(x * y for x, y in zip(a, b)) / (na * nb)
        found_above += cosine > 1.0
        with pytest.raises(ValueError, match="degenerate geometry"):
            sl.lambert(a, b, 1000.0)
        c = tuple(-2.0 * x for x in a)
        nc = math.sqrt(sum(x * x for x in c))
        found_below += sum(x * y for x, y in zip(a, c)) / (na * nc) < -1.0
        with pytest.raises(ValueError, match="degenerate geometry"):
            sl.lambert(a, c, 1000.0)
    assert found_above > 0 and found_below > 0                # the clamp was really needed for some of them


def test_limits_of_the_inputs():
    r1, r2, tof, v1, _ = circular(7000.0, sl.MU_EARTH, math.radians(60.0))
    for bad in (0.0, -1.0, -1e-300):
        with pytest.raises(ValueError, match="mu must be positive"):
            sl.lambert(r1, r2, tof, mu=bad)
        with pytest.raises(ValueError, match="time of flight must be positive"):
            sl.lambert(r1, r2, bad)
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite"):
            sl.lambert(r1, r2, bad)
        with pytest.raises(ValueError, match="finite"):
            sl.lambert((bad, 0.0, 0.0), r2, tof)
    with pytest.raises(ValueError, match="non-zero"):
        sl.lambert((0.0, 0.0, 0.0), r2, tof)
    with pytest.raises(ValueError, match="non-zero"):
        sl.lambert(r1, (0.0, 0.0, 0.0), tof)
