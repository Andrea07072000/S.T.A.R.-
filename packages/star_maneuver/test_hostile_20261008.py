"""Regression tests of 2026-10-08: huge finite inputs gave OverflowError and non-numbers gave TypeError (R3 says ValueError)."""
import math

import pytest

import star_maneuver as sm

BAD = [None, "1", True, False, 1j, [1.0], (1.0,)]
HUGE = [1.7e308, -1.7e308, 1.0001e100, -1.0001e100]


def test_limit_is_pinned_and_accepted():
    assert sm.LIMIT == 1e100
    # the limit itself is accepted and the answers are finite
    assert math.isfinite(sm.hohmann(1e100, 1e100)["tof_s"])
    assert sm.hohmann(1e100, 1e100)["dv_total"] == 0.0
    assert sm.combined_dv(1e100, 1e100, math.pi) == pytest.approx(2e100, rel=1e-15, abs=0)
    assert math.isfinite(sm.bielliptic(1e99, 1e99, 1e100)["tof_s"])
    assert sm.plane_change(1e100, math.pi) == pytest.approx(2e100, rel=1e-15, abs=0)
    assert sm.vis_viva(1e100, 1e100, 1e100) == pytest.approx(1.0, rel=1e-15, abs=0)


@pytest.mark.parametrize("bad", BAD + HUGE + [float("nan"), float("inf")])
def test_every_argument_of_every_function_is_checked(bad):
    calls = [(sm.vis_viva, (7000.0, 7000.0, 398600.0)), (sm.hohmann, (7000.0, 42000.0, 398600.0)), (sm.plane_change, (7.5, 0.1)),
             (sm.combined_dv, (7.5, 7.0, 0.1)), (sm.bielliptic, (7000.0, 42000.0, 100000.0, 398600.0))]
    for f, good in calls:
        f(*good)
        for i in range(len(good)):
            args = list(good)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


def test_messages_tell_the_three_refusals_apart():
    with pytest.raises(ValueError, match="real numbers"):
        sm.plane_change(None, 0.1)
    with pytest.raises(ValueError, match="real numbers"):
        sm.plane_change(True, 0.1)
    with pytest.raises(ValueError, match="finite"):
        sm.plane_change(float("nan"), 0.1)
    with pytest.raises(ValueError, match="1e100"):
        sm.plane_change(2e100, 0.1)
    with pytest.raises(ValueError, match="1e100"):
        sm.plane_change(-2e100, 0.1)


def test_integers_are_still_accepted():
    assert sm.hohmann(7000, 42000) == sm.hohmann(7000.0, 42000.0)
    assert sm.plane_change(7, 0) == 0.0


def test_zero_is_refused_and_small_positive_values_are_accepted():
    # the boundary is zero itself: 0 is refused, 0.5 is a valid radius, speed or mu
    for args in ((0.0, 7000.0), (7000.0, 0.0)):
        with pytest.raises(ValueError, match="radii must be positive"):
            sm.vis_viva(*args)
        with pytest.raises(ValueError, match="radii must be positive"):
            sm.hohmann(*args)
    for args in ((0.0, 2.0, 3.0), (1.0, 0.0, 3.0), (1.0, 2.0, 0.0)):
        with pytest.raises(ValueError, match="radii must be positive"):
            sm.bielliptic(*args)
    for f, args in ((sm.vis_viva, (1.0, 1.0, 0.0)), (sm.hohmann, (1.0, 2.0, 0.0)), (sm.bielliptic, (1.0, 2.0, 3.0, 0.0))):
        with pytest.raises(ValueError, match="mu must be positive"):
            f(*args)
    # mu = 0.5, r = a = 0.5: v = sqrt(0.5 * (4 - 2)) = 1
    assert sm.vis_viva(0.5, 0.5, 0.5) == 1.0
    assert sm.hohmann(0.5, 0.5, 0.5)["dv_total"] == 0.0
    # r1 = r2 = rb: nothing to do
    assert sm.bielliptic(0.5, 0.5, 0.5, 0.5)["dv_total"] == 0.0
    # tof of a Hohmann transfer between equal radii is half the circular period: pi sqrt(r^3 / mu)
    assert sm.hohmann(0.5, 0.5, 0.5)["tof_s"] == pytest.approx(math.pi * 0.5, rel=1e-15, abs=0)
    assert sm.bielliptic(0.5, 0.5, 0.5, 0.5)["tof_s"] == pytest.approx(math.pi, rel=1e-15, abs=0)
    assert sm.plane_change(0.0, 1.0) == 0.0 and sm.combined_dv(0.0, 0.0, 1.0) == 0.0
    assert sm.combined_dv(0.5, 0.0, 1.0) == 0.5


def test_limit_plus_one_would_change_nothing_visible_but_the_next_float_is_refused():
    assert sm.plane_change(1e100, 0.0) == 0.0
    with pytest.raises(ValueError, match="1e100"):
        sm.plane_change(math.nextafter(1e100, math.inf), 0.0)
