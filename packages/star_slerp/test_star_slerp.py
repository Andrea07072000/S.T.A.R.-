"""star_slerp against published values and hand-derivable identities/invariants.
Verifies shortest-arc behaviour, endpoints, symmetry, constant angular rate and table interpolation.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_slerp as ss


def identity():
    return (1.0, 0.0, 0.0, 0.0)


def Rz(a):
    return (math.cos(a / 2.0), 0.0, 0.0, math.sin(a / 2.0))


def Rx(a):
    return (math.cos(a / 2.0), math.sin(a / 2.0), 0.0, 0.0)


def test_published_axis_fractions_and_endpoints():
    q = ss.slerp(identity(), Rz(math.pi / 2.0), 0.5)
    assert q == pytest.approx((0.9238795325112867, 0.0, 0.0, 0.3826834323650898), abs=1e-15)

    q = ss.slerp(identity(), Rx(1.0), 0.25)
    assert q == pytest.approx((math.cos(0.125), math.sin(0.125), 0.0, 0.0), abs=1e-15)

    q = ss.slerp(Rz(math.radians(30.0)), Rz(math.radians(90.0)), 1.0 / 3.0)
    assert q == pytest.approx(Rz(math.radians(50.0)), abs=1e-15)

    q = ss.slerp(Rx(0.2), Rx(1.0), 0.5)
    assert q == pytest.approx(Rx(0.6), abs=1e-15)

    q0, q1 = Rx(0.3), Rx(0.9)
    assert ss.slerp(q0, q1, 0.0) == pytest.approx(q0, abs=2e-16)
    assert ss.slerp(q0, q1, 1.0) == pytest.approx(q1, abs=2e-16)


def test_shorter_way_negation_and_180_degree_case():
    q = ss.slerp(identity(), (-math.cos(0.5), -math.sin(0.5), 0.0, 0.0), 0.25)
    assert q == pytest.approx((math.cos(0.125), math.sin(0.125), 0.0, 0.0), abs=1e-15)
    q1 = ss.slerp(identity(), (-math.cos(0.5), -math.sin(0.5), 0.0, 0.0), 1.0)
    assert q1 == pytest.approx((math.cos(0.5), math.sin(0.5), 0.0, 0.0), abs=1e-15)

    q = ss.slerp(identity(), Rz(3.0 * math.pi / 2.0), 0.5)
    assert q == pytest.approx((math.cos(math.radians(22.5)), 0.0, 0.0, -math.sin(math.radians(22.5))), abs=1e-15)

    # dot == 0 exactly: not negated, path follows passed q1 sign
    s2 = math.sqrt(0.5)
    assert ss.slerp(identity(), (0.0, 0.0, 0.0, 1.0), 0.5) == pytest.approx((s2, 0.0, 0.0, s2), abs=1e-15)
    assert ss.slerp(identity(), (0.0, 0.0, 0.0, -1.0), 0.5) == pytest.approx((s2, 0.0, 0.0, -s2), abs=1e-15)


def test_equal_attitudes_and_tiny_rotation_branch():
    for t in (0.0, 0.25, 0.5, 1.0):
        assert ss.slerp(identity(), identity(), t) == (1.0, 0.0, 0.0, 0.0)
        assert ss.slerp(identity(), (-1.0, 0.0, 0.0, 0.0), t) == (1.0, 0.0, 0.0, 0.0)

    q = ss.slerp(identity(), (math.cos(1e-10), 0.0, math.sin(1e-10), 0.0), 0.5)
    assert q[2] == pytest.approx(5e-11, abs=1e-25)
    assert q[0] == 1.0


def test_unit_length_symmetry_and_constant_rate():
    q0, q1, t = Rx(0.31), Rz(1.11), 0.37  # no zero/symmetry to exercise all terms
    a = ss.slerp(q0, q1, t)
    b = ss.slerp(q1, q0, 1.0 - t)
    # up to global sign
    if sum(ai * bi for ai, bi in zip(a, b)) < 0:
        b = tuple(-x for x in b)
    assert a == pytest.approx(b, abs=1e-15)

    assert math.hypot(*a) == pytest.approx(1.0, abs=4e-16)

    # constant-rate invariant using published formula 2*acos(|dot|)
    total = 2.0 * math.acos(abs(sum(x * y for x, y in zip(q0, q1))))
    part = 2.0 * math.acos(abs(sum(x * y for x, y in zip(q0, a))))
    assert part == pytest.approx(t * total, abs=1e-12)


def test_interpolate_published_values_and_equivalence_with_two_rows():
    times = [0.0, 10.0, 20.0]
    rows = [identity(), Rx(1.0), Rx(2.0)]
    assert ss.interpolate(times, rows, 15.0) == pytest.approx((math.cos(0.75), math.sin(0.75), 0.0, 0.0), abs=1e-15)
    assert ss.interpolate(times, rows, 10.0) == pytest.approx(Rx(1.0), abs=2e-16)
    assert ss.interpolate(times, rows, 0.0) == pytest.approx(identity(), abs=2e-16)
    assert ss.interpolate(times, rows, 20.0) == pytest.approx(Rx(2.0), abs=2e-16)
    assert ss.interpolate(times, rows, 5.0) == pytest.approx(Rx(0.5), abs=1e-15)

    rows2 = [identity(), Rx(1.0), identity()]
    assert ss.interpolate(times, rows2, 15.0) == pytest.approx(Rx(0.5), abs=1e-15)

    q0, q1, t = Rx(0.41), Rz(0.77), 0.23
    assert ss.interpolate([0.0, 1.0], [q0, q1], t) == ss.slerp(q0, q1, t)

    assert ss.interpolate([0.0, 1.0, 5.0], [identity(), Rx(1.0), Rx(2.0)], 3.0) == pytest.approx(Rx(1.5), abs=1e-15)
