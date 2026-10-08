"""Regression tests of 2026-10-08: long hyperbolic arcs (they raised OverflowError) and the limits of stumpff."""
import math

import pytest

import star_kepler as sk

MU = sk.MU_EARTH


def energy(r, v):
    return sum(c * c for c in v) / 2.0 - MU / math.sqrt(sum(c * c for c in r))


def momentum(r, v):
    return r[0] * v[1] - r[1] * v[0]


@pytest.mark.parametrize("r0, v0", [((7000.0, 0.0, 0.0), (0.0, 20.0, 0.0)), ((7000.0, 100.0, 0.0), (3.0, 12.0, 0.0)),
                                    ((42000.0, 0.0, 0.0), (0.0, 4.4, 0.0)), ((7000.0, 0.0, 0.0), (0.0, 10.68, 0.0))])
@pytest.mark.parametrize("tof", [1e6, 1e7, 1e9, -1e6, -1e7])
def test_long_hyperbolic_arcs_conserve_energy_and_angular_momentum(r0, v0, tof):
    # 0.1.0 raised OverflowError here (first seen: a 20 km/s flyby after 1e6 s)
    r, v = sk.propagate(r0, v0, tof)
    assert energy(r, v) == pytest.approx(energy(r0, v0), rel=1e-11, abs=0)
    assert momentum(r, v) == pytest.approx(momentum(r0, v0), rel=1e-8, abs=0)
    assert math.sqrt(sum(c * c for c in r)) > 1e6          # every case is more than a million km away by then


def test_hyperbolic_arc_matches_the_asymptote():
    # far along a hyperbola the speed tends to v_inf = sqrt(2 E) and the distance grows by v_inf per second
    r0, v0 = (7000.0, 0.0, 0.0), (0.0, 20.0, 0.0)
    v_inf = math.sqrt(2.0 * energy(r0, v0))
    r1, v1 = sk.propagate(r0, v0, 1e8)
    r2, _ = sk.propagate(r0, v0, 2e8)
    assert math.sqrt(sum(c * c for c in v1)) == pytest.approx(v_inf, rel=1e-6, abs=0)
    d1, d2 = (math.sqrt(sum(c * c for c in r)) for r in (r1, r2))
    assert (d2 - d1) / 1e8 == pytest.approx(v_inf, rel=1e-6, abs=0)


def test_short_hyperbolic_arc_is_unchanged():
    # value of release 0.1.0 for an arc that already worked
    r, _ = sk.propagate((7000.0, 0.0, 0.0), (0.0, 20.0, 0.0), 1e5)
    assert r == pytest.approx((-273763.7258212451, 1676275.0551394694, 0.0), rel=1e-12, abs=1e-9)


def test_forward_then_backward_returns_to_the_start():
    r0, v0 = (7000.0, 0.0, 0.0), (0.0, 20.0, 0.0)
    r, v = sk.propagate(r0, v0, 1e6)
    back, _ = sk.propagate(r, v, -1e6)
    assert back == pytest.approx(r0, rel=0, abs=1e-5)


def test_an_arc_too_long_to_bracket_is_refused_not_overflowed():
    with pytest.raises((RuntimeError, ValueError)):
        sk.propagate((7000.0, 0.0, 0.0), (0.0, 20.0, 0.0), 1e300)


def test_stumpff_values():
    assert sk.stumpff(0.0) == (0.5, 1.0 / 6.0)
    # z = pi^2: C = 2 / pi^2, S = 1 / pi^2
    c, s = sk.stumpff(math.pi ** 2)
    assert c == pytest.approx(2.0 / math.pi ** 2, rel=1e-15, abs=0)
    assert s == pytest.approx(1.0 / math.pi ** 2, rel=1e-15, abs=0)
    # z = -1: C = cosh(1) - 1, S = sinh(1) - 1
    c, s = sk.stumpff(-1.0)
    assert c == pytest.approx(math.cosh(1.0) - 1.0, rel=1e-15, abs=0)
    assert s == pytest.approx(math.sinh(1.0) - 1.0, rel=1e-15, abs=0)
    assert sk.stumpff(1) == sk.stumpff(1.0)


def test_stumpff_limit():
    assert sk.STUMPFF_MIN_Z == -4.9e5
    c, s = sk.stumpff(-4.9e5)
    assert math.isfinite(c) and math.isfinite(s) and c > 1e290
    with pytest.raises(ValueError, match="overflow"):
        sk.stumpff(-4.9e5 - 1e-3)
    with pytest.raises(ValueError, match="overflow"):
        sk.stumpff(-1.7e308)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), None, "1", True, False, 1j, [1.0]])
def test_stumpff_refuses(bad):
    with pytest.raises(ValueError, match="finite real number"):
        sk.stumpff(bad)


def test_stumpff_series_and_its_two_seams():
    # inside |z| <= 1e-6 the series 1/2 - z/24 + z^2/720 and 1/6 - z/120 + z^2/5040 is used
    for z in (1e-6, -1e-6, 5e-7, -5e-7):
        c, s = sk.stumpff(z)
        assert c == pytest.approx(0.5 - z / 24.0 + z * z / 720.0, rel=1e-16, abs=0)
        assert s == pytest.approx(1.0 / 6.0 - z / 120.0 + z * z / 5040.0, rel=1e-16, abs=0)
    # series terms have these signs and sizes: at z = 1e-6 the linear term is visible in the 8th digit
    c, s = sk.stumpff(1e-6)
    assert 0.5 - c == pytest.approx(1e-6 / 24.0, rel=1e-6, abs=0)
    assert 1.0 / 6.0 - s == pytest.approx(1e-6 / 120.0, rel=1e-6, abs=0)
    # just outside, the closed forms take over: they lose digits to cancellation (about 1e-10 here) but must agree to that
    for z in (1.0000001e-6, -1.0000001e-6, 1e-3, -1e-3):
        c, s = sk.stumpff(z)
        assert c == pytest.approx(0.5 - z / 24.0 + z * z / 720.0 - z ** 3 / 40320.0, rel=1e-9, abs=0)
        assert s == pytest.approx(1.0 / 6.0 - z / 120.0 + z * z / 5040.0 - z ** 3 / 362880.0, rel=1e-6, abs=0)
    # closed forms, both branches, at values where they are exact enough to pin the formula
    c, s = sk.stumpff(4.0)
    assert c == pytest.approx((1.0 - math.cos(2.0)) / 4.0, rel=1e-15, abs=0)
    assert s == pytest.approx((2.0 - math.sin(2.0)) / 8.0, rel=1e-15, abs=0)
    c, s = sk.stumpff(-4.0)
    assert c == pytest.approx((math.cosh(2.0) - 1.0) / 4.0, rel=1e-15, abs=0)
    assert s == pytest.approx((math.sinh(2.0) - 2.0) / 8.0, rel=1e-15, abs=0)
