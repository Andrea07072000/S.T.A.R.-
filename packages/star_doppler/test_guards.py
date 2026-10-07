"""Guard tests of star_doppler written by the reviewer: every sign and every component by hand, the exact limits, and
the cases where a floating-point shortcut would overflow or cancel."""
import math

import pytest

import star_doppler as dp

C = dp.C_KM_S
ZERO = (0.0, 0.0, 0.0)


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_each_axis_and_each_direction(axis, sign):
    r = [0.0, 0.0, 0.0]
    r[axis] = sign * 8.0
    for speed in (3.0, -3.0):
        v = [0.0, 0.0, 0.0]
        v[axis] = speed
        assert dp.range_and_rate(ZERO, ZERO, r, v) == (8.0, sign * speed)                 # along the line of sight: the whole speed, signed
        assert dp.range_and_rate(r, v, ZERO, ZERO) == (8.0, sign * speed)                 # seen from the other end: the same range and rate
        other = [0.0, 0.0, 0.0]
        other[(axis + 1) % 3] = speed
        assert dp.range_and_rate(ZERO, ZERO, r, other) == (8.0, 0.0)                      # across the line of sight: nothing
        assert math.copysign(1.0, dp.range_and_rate(ZERO, ZERO, r, other)[1]) == 1.0      # and a positive zero


def test_differences_of_both_ends_are_used():
    assert dp.range_and_rate((1, 2, 3), (10, 20, 30), (4, 6, 3), (11, 20, 30)) == (5.0, 0.6)       # dr = (3, 4, 0), dv = (1, 0, 0)
    assert dp.range_and_rate((1, 2, 3), (11, 20, 30), (4, 6, 3), (10, 20, 30)) == (5.0, -0.6)      # the observer chases the target
    assert dp.range_and_rate((4, 6, 3), (10, 20, 30), (1, 2, 3), (11, 20, 30)) == (5.0, -0.6)      # dr = (-3, -4, 0), dv = (1, 0, 0)
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (3, 4, 0), (0, 1, 0)) == (5.0, 0.8)
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (0, 3, 4), (0, 0, 1)) == (5.0, 0.8)
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (4, 0, 3), (0, 0, 1)) == (5.0, 0.6)
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (2, 3, 6), (7, 0, 0)) == (7.0, 2.0)             # 2*7/7
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (2, 3, 6), (0, 7, 0)) == (7.0, 3.0)
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (2, 3, 6), (0, 0, 7)) == (7.0, 6.0)
    assert dp.range_and_rate((0, 0, 0), (0, 0, 0), (2, 3, 6), (7, 7, 7)) == pytest.approx((7.0, 11.0), abs=1e-14)
    got = dp.range_and_rate([1, 2, 3], [0, 0, 0], [4, 6, 3], [1, 0, 0])
    assert got == (5.0, 0.6) and type(got) is tuple and all(type(k) is float for k in got)


def test_sizes_that_would_overflow_or_vanish():
    assert dp.range_and_rate((-1e15, 0, 0), ZERO, (1e15, 0, 0), (1e15, 0, 0)) == (2e15, 1e15)
    assert dp.range_and_rate((-1e15, -1e15, -1e15), (-1e15, -1e15, -1e15), (1e15, 1e15, 1e15), (1e15, 1e15, 1e15)) == pytest.approx((2e15 * math.sqrt(3), 2e15 * math.sqrt(3)), rel=1e-15)
    assert dp.range_and_rate(ZERO, ZERO, (5e-324, 0, 0), (1.0, 0, 0)) == (5e-324, 1.0)             # the smallest separation still has a direction
    assert dp.range_and_rate(ZERO, ZERO, (3e-200, 4e-200, 0), (1.0, 0, 0)) == pytest.approx((5e-200, 0.6), rel=1e-15)
    with pytest.raises(ValueError, match="coincide"):
        dp.range_and_rate((1.5, -2.0, 3.25), (1, 0, 0), (1.5, -2.0, 3.25), (0, 1, 0))
    with pytest.raises(ValueError, match="coincide"):
        dp.range_and_rate((0.0, 0.0, 0.0), ZERO, (-0.0, 0.0, -0.0), ZERO)


def test_frequency_factors_by_hand():
    assert dp.C_KM_S == 299792.458
    assert dp.received_frequency(1000.0, 0.6 * C) == 500.0 and dp.received_frequency(1000.0, -0.6 * C) == 2000.0
    assert dp.received_frequency(1000.0, 0.6 * C, False) == 400.0 and dp.received_frequency(1000.0, -0.6 * C, False) == 1600.0
    assert dp.received_frequency(1000.0, 0.8 * C) == pytest.approx(1000.0 / 3.0, rel=1e-15)        # sqrt(0.2 / 1.8) = 1/3
    assert dp.received_frequency(1000.0, -0.8 * C) == pytest.approx(3000.0, rel=1e-15)
    assert dp.received_frequency(1000.0, 0.8 * C, relativistic=False) == pytest.approx(200.0, rel=1e-15)
    assert dp.received_frequency(1000.0, 0.0) == 1000.0 and dp.received_frequency(1000.0, 0, False) == 1000.0 and dp.received_frequency(7, 0) == 7.0
    assert dp.received_frequency(1000.0, 0.6 * C, True) == dp.received_frequency(1000.0, 0.6 * C)   # the default is the relativistic formula
    assert dp.received_frequency(2.0, 0.5 * C, False) == 1.0 and dp.received_frequency(2.0, -0.5 * C, False) == 3.0
    low, first = dp.received_frequency(2.2e9, 7.5), dp.received_frequency(2.2e9, 7.5, False)
    assert first == 2.2e9 * (1.0 - 7.5 / C) and low - first == pytest.approx(2.2e9 * (7.5 / C) ** 2 / 2, rel=1e-3) and first < low < 2.2e9


def test_limits_at_their_exact_values():
    assert dp.BIG == 1e15 and dp.MAX_FREQUENCY == 1e30
    just_below = math.nextafter(C, 0.0)
    assert 0.0 < dp.received_frequency(1.0, just_below) < 1e-7 and dp.received_frequency(1.0, -just_below) > 1e7    # sqrt(1.1e-16 / 2) = 1.05e-8 and its inverse
    assert dp.received_frequency(1.0, just_below, False) == pytest.approx(0.0, abs=1e-15) and dp.received_frequency(1.0, -just_below, False) == pytest.approx(2.0, rel=1e-15)
    for bad in (C, -C, math.nextafter(C, math.inf), 3e5, -3e5, 1e15):
        for flag in (True, False):
            with pytest.raises(ValueError, match="smaller than the speed of light"):
                dp.received_frequency(1e9, bad, flag)
    assert dp.received_frequency(1e30, 0.0) == 1e30 and dp.received_frequency(5e-324, 0.0) == 5e-324
    for bad in (0, 0.0, -0.0, -1.0, -5e-324, math.nextafter(1e30, math.inf), float("nan"), float("inf"), True, "1", None, 1j):
        with pytest.raises(ValueError, match="frequency"):
            dp.received_frequency(bad, 1.0)
    for bad in (float("nan"), float("inf"), -float("inf"), True, "1", None, math.nextafter(1e15, math.inf)):
        with pytest.raises(ValueError, match="range_rate"):
            dp.received_frequency(1e9, bad)
    for bad in (0, 1, None, "yes", 1.0):
        with pytest.raises(ValueError, match="relativistic must be True or False"):
            dp.received_frequency(1e9, 1.0, bad)
    names = ("r_observer", "v_observer", "r_target", "v_target")
    good = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (3.0, 4.0, 0.0), (1.0, 0.0, 0.0)]
    for k, name in enumerate(names):
        for bad in ((1.0, 2.0), (1.0, 2.0, 3.0, 4.0), "123", None, 5.0):
            args = list(good)
            args[k] = bad
            with pytest.raises(ValueError, match=f"{name} must be a list or tuple of 3 numbers"):
                dp.range_and_rate(*args)
        for bad in (True, "1", None, float("nan"), float("inf"), 1j, math.nextafter(1e15, math.inf), -math.nextafter(1e15, math.inf)):
            for j in range(3):
                vec = list(good[k])
                vec[j] = bad
                args = list(good)
                args[k] = vec
                with pytest.raises(ValueError, match=f"a component of {name}"):
                    dp.range_and_rate(*args)
