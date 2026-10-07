"""Guard tests of star_slerp written by the reviewer: rotations about a fixed axis for which the answer is known in
closed form, each branch at its boundary, and the choice of the table row at every kind of time."""
import math

import pytest

import star_slerp as sl

IDENTITY = (1.0, 0.0, 0.0, 0.0)


def about(axis, angle):
    """Rotation by `angle` (rad) about a unit axis, scalar first."""
    s = math.sin(angle / 2)
    return (math.cos(angle / 2), axis[0] * s, axis[1] * s, axis[2] * s)


def gap(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


AXES = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.6, 0.0, 0.8), (2 / 7, -3 / 7, 6 / 7)]


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("start,end", [(0.0, 1.0), (0.3, 2.9), (-1.0, 1.5), (0.5, 0.5 + 1e-3), (2.0, 2.0 + 3.0), (0.0, 1e-6), (1.0, 1.0 + 1e-10), (0.2, 0.2 + 2e-8)])
@pytest.mark.parametrize("t", [0.0, 0.125, 0.5, 0.9, 1.0])
def test_fraction_of_a_rotation_about_a_fixed_axis(axis, start, end, t):
    got = sl.slerp(about(axis, start), about(axis, end), t)
    assert gap(got, about(axis, start + t * (end - start))) < 3e-16
    assert abs(math.hypot(*got) - 1.0) < 4e-16 and all(type(c) is float for c in got) and type(got) is tuple


@pytest.mark.parametrize("axis", AXES)
def test_the_shorter_way_and_the_hemisphere_of_the_start(axis):
    a, b = about(axis, 0.4), about(axis, 1.6)
    flipped = tuple(-c for c in b)
    for t in (0.0, 0.3, 1.0):
        assert gap(sl.slerp(a, flipped, t), about(axis, 0.4 + 1.2 * t)) < 3e-16       # -b is the same attitude
        assert sl.slerp(a, flipped, t) == sl.slerp(a, b, t)
        assert gap(sl.slerp(tuple(-c for c in a), b, t), tuple(-c for c in about(axis, 0.4 + 1.2 * t))) < 3e-16   # the result follows the sign of q0
    far = about(axis, 0.4 + 4.0)                              # 4 rad apart: the short way is 4 - 2 pi = -2.28 rad, through -far
    assert gap(sl.slerp(a, far, 0.5), tuple(-c for c in about(axis, 0.4 + (4.0 - 2 * math.pi) / 2 + 2 * math.pi))) < 4e-16
    half_turn = about(axis, 0.4 + math.pi)                    # exactly orthogonal quaternions up to rounding: either arc, both valid
    mid = sl.slerp(a, half_turn, 0.5)
    assert min(gap(mid, about(axis, 0.4 + math.pi / 2)), gap(mid, about(axis, 0.4 - math.pi / 2))) < 4e-16


def test_orthogonal_quaternions_follow_the_sign_given():
    r = math.sqrt(0.5)
    assert gap(sl.slerp(IDENTITY, (0.0, 0.0, 0.0, 1.0), 0.5), (r, 0.0, 0.0, r)) < 2e-16
    assert gap(sl.slerp(IDENTITY, (0.0, 0.0, 0.0, -1.0), 0.5), (r, 0.0, 0.0, -r)) < 2e-16
    assert gap(sl.slerp(IDENTITY, (0.0, 1.0, 0.0, 0.0), 1.0), (0.0, 1.0, 0.0, 0.0)) < 2e-16
    assert gap(sl.slerp(IDENTITY, (0.0, 1.0, 0.0, 0.0), 1 / 3), (math.cos(math.pi / 6), 0.5, 0.0, 0.0)) < 2e-16


def test_equal_and_nearly_equal_attitudes():
    for q in (IDENTITY, (0.5, 0.5, 0.5, 0.5), about((0.6, 0.0, 0.8), 2.0)):
        for t in (0.0, 0.37, 1.0):
            assert gap(sl.slerp(q, q, t), q) < 2e-16 and gap(sl.slerp(q, tuple(-c for c in q), t), q) < 2e-16
    assert sl.slerp(IDENTITY, IDENTITY, 0.5) == (1.0, 0.0, 0.0, 0.0) and sl.slerp(IDENTITY, (-1.0, 0.0, 0.0, 0.0), 0.5) == (1.0, 0.0, 0.0, 0.0)
    assert all(math.copysign(1.0, c) == 1.0 for c in sl.slerp(IDENTITY, (-1.0, -0.0, 0.0, -0.0), 0.5))      # zeros come out positive
    for q0, q1 in (((1.0, -0.0, -0.0, -0.0), (1.0, -0.0, -0.0, -0.0)), ((math.cos(0.3), -0.0, math.sin(0.3), -0.0), (math.cos(0.9), -0.0, math.sin(0.9), -0.0))):
        got = sl.slerp(q0, q1, 0.5)                           # negative zeros in, on both branches: positive zeros out
        assert got[1] == 0.0 and got[3] == 0.0 and math.copysign(1.0, got[1]) == 1.0 and math.copysign(1.0, got[3]) == 1.0
    assert math.copysign(1.0, sl.slerp((1.0, -0.0, -0.0, -0.0), (1.0, -0.0, -0.0, -0.0), 0.5)[2]) == 1.0
    assert math.copysign(1.0, sl.slerp((-0.0, 1.0, 0.0, 0.0), (-0.0, math.cos(0.5), math.sin(0.5), 0.0), 0.5)[0]) == 1.0
    for half in (1e-12, 0.9e-8, 1.1e-8, 1e-7, 1e-5):          # the half-angle on both sides of SMALL_ANGLE: the two branches agree
        got = sl.slerp(IDENTITY, (math.cos(half), 0.0, math.sin(half), 0.0), 0.25)
        assert got[2] == pytest.approx(math.sin(0.25 * half), rel=1e-12) and got[0] == pytest.approx(math.cos(0.25 * half), abs=1e-15) and got[1] == 0.0 and got[3] == 0.0
    assert sl.SMALL_ANGLE == 1e-8 and sl.UNIT_TOLERANCE == 1e-9 and sl.BIG_TIME == 1e15 and sl.MAX_ROWS == 100000


def test_table_rows_are_chosen_correctly():
    x = (1.0, 0.0, 0.0)
    times = [0.0, 10.0, 20.0, 50.0]
    rows = [about(x, 0.0), about(x, 1.0), about(x, 3.0), about(x, 2.0)]
    for t, angle in ((0.0, 0.0), (5.0, 0.5), (10.0, 1.0), (12.5, 1.5), (20.0, 3.0), (35.0, 2.5), (50.0, 2.0), (math.nextafter(10.0, 0.0), 1.0), (math.nextafter(10.0, 20.0), 1.0),
                     (49.999, 2.0 + 0.001 / 30)):
        assert gap(sl.interpolate(times, rows, t), about(x, angle)) < 1e-14, t
    assert sl.interpolate(times, rows, 10.0) == sl.slerp(rows[1], rows[2], 0.0) and sl.interpolate(times, rows, 50.0) == sl.slerp(rows[2], rows[3], 1.0)
    assert sl.interpolate([0.0, 1.0], [rows[1], rows[2]], 0.3) == sl.slerp(rows[1], rows[2], 0.3)
    assert sl.interpolate((3, 7), (rows[0], rows[1]), 5) == sl.slerp(rows[0], rows[1], 0.5)       # tuples and integers
    assert gap(sl.interpolate([-1e15, 1e15], [rows[0], rows[1]], 0.0), about(x, 0.5)) < 2e-16     # the widest table allowed


def test_refusals():
    good = about((0.0, 0.0, 1.0), 0.7)
    for bad in ((1.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0, 0.0), "1000", None, 1.0, iter(IDENTITY)):
        with pytest.raises(ValueError, match="must be a list or tuple of 4 numbers"):
            sl.slerp(bad, good, 0.5)
        with pytest.raises(ValueError, match="must be a list or tuple of 4 numbers"):
            sl.slerp(good, bad, 0.5)
    for bad in (True, "1", None, float("nan"), float("inf"), 1j, 2.5, -2.5):
        for k in range(4):
            q = list(IDENTITY)
            q[k] = bad
            with pytest.raises(ValueError, match="a component of"):
                sl.slerp(q, good, 0.5)
    for bad in ((1.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0), (1.0 + 2e-9, 0.0, 0.0, 0.0), (1.0 - 2e-9, 0.0, 0.0, 0.0), (0.5, 0.5, 0.5, 0.5001)):
        with pytest.raises(ValueError, match="unit length"):
            sl.slerp(bad, good, 0.5)
        with pytest.raises(ValueError, match="unit length"):
            sl.slerp(good, bad, 0.5)
    assert sl.slerp((1.0 + 5e-10, 0.0, 0.0, 0.0), IDENTITY, 0.5) == (1.0, 0.0, 0.0, 0.0) and sl.slerp((1.0 - 5e-10, 0.0, 0.0, 0.0), IDENTITY, 0.5) == (1.0, 0.0, 0.0, 0.0)
    for bad in (-0.1, -5e-324, math.nextafter(1.0, 2.0), 2, float("nan"), float("inf"), True, "0.5", None):
        with pytest.raises(ValueError, match="t must be a finite real number from 0 to 1"):
            sl.slerp(IDENTITY, good, bad)
    rows = [IDENTITY, good, IDENTITY]
    for bad in ([0.0], [], "012", None, iter([0.0, 1.0, 2.0])):
        with pytest.raises(ValueError, match="times must be a list or tuple"):
            sl.interpolate(bad, rows, 0.0)
    for bad in ([0.0, 1.0, 1.0], [0.0, 2.0, 1.0], [1.0, 0.0, 2.0]):
        with pytest.raises(ValueError, match="strictly increasing"):
            sl.interpolate(bad, rows, 0.5)
    for bad in (float("nan"), float("inf"), True, "1", None, math.nextafter(1e15, math.inf)):
        with pytest.raises(ValueError, match="a time"):
            sl.interpolate([0.0, 1.0, bad], rows, 0.5)
    for bad in ([IDENTITY, good], [IDENTITY, good, IDENTITY, good], "abc", None):
        with pytest.raises(ValueError, match="one quaternion for each time"):
            sl.interpolate([0.0, 1.0, 2.0], bad, 0.5)
    with pytest.raises(ValueError, match="a quaternion of the table must be of unit length"):
        sl.interpolate([0.0, 1.0, 2.0], [IDENTITY, (1.0, 1.0, 0.0, 0.0), IDENTITY], 0.5)
    for bad in (math.nextafter(0.0, -1.0), math.nextafter(2.0, 3.0), -1.0, 3.0, float("nan"), True, None):
        with pytest.raises(ValueError, match="t must be a finite real number from"):
            sl.interpolate([0.0, 1.0, 2.0], rows, bad)
