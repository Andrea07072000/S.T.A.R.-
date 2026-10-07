"""Guard tests of star_rotframe written by the reviewer: every component of both functions against the formulas
written out here term by term, the signs of the transport term in each quadrant, and the limits at their values."""
import math

import pytest

import star_rotframe as rf

STATES = [((7000.0, -1200.0, 300.0), (1.5, 7.2, -0.4)), ((1.0, 0.0, 0.0), (0.0, 0.0, 0.0)), ((0.0, 1.0, 0.0), (0.0, 0.0, 0.0)), ((0.0, 0.0, 1.0), (0.0, 0.0, 1.0)),
          ((-3.0, 4.0, -5.0), (6.0, -7.0, 8.0)), ((1e15, -1e15, 1e15), (1e15, 1e15, -1e15)), ((1e-9, 2e-9, -3e-9), (4e3, -5e3, 6e3))]
ANGLES = [0.0, 0.3, math.pi / 2, 2.0, math.pi, -1.1, 4.0, 5.5, 1000.0, -1e9, 1e9]
RATES = [0.0, rf.EARTH_RATE, 2.0, -0.75, 1000.0, -1000.0]


@pytest.mark.parametrize("r,v", STATES)
@pytest.mark.parametrize("angle", ANGLES)
def test_every_component_term_by_term(r, v, angle):
    c, s = math.cos(angle), math.sin(angle)
    for rate in RATES:
        (x, y, z), (vx, vy, vz) = rf.to_rotating(r, v, angle, rate)
        ex, ey = c * r[0] + s * r[1], -s * r[0] + c * r[1]
        scale_r = math.hypot(*r)
        scale_v = math.hypot(*v) + abs(rate) * scale_r
        assert abs(x - ex) <= 2e-16 * scale_r and abs(y - ey) <= 2e-16 * scale_r and z == r[2]
        assert abs(vx - (c * v[0] + s * v[1] + rate * ey)) <= 4e-16 * scale_v            # -(w x r')_x = +rate y'
        assert abs(vy - (-s * v[0] + c * v[1] - rate * ex)) <= 4e-16 * scale_v           # -(w x r')_y = -rate x'
        assert vz == v[2]
        (ix, iy, iz), (ivx, ivy, ivz) = rf.to_inertial(r, v, angle, rate)
        assert abs(ix - (c * r[0] - s * r[1])) <= 2e-16 * scale_r and abs(iy - (s * r[0] + c * r[1])) <= 2e-16 * scale_r and iz == r[2]
        cx, cy = v[0] - rate * r[1], v[1] + rate * r[0]                                 # v + w x r, in rotating components
        assert abs(ivx - (c * cx - s * cy)) <= 4e-16 * scale_v and abs(ivy - (s * cx + c * cy)) <= 4e-16 * scale_v and ivz == v[2]
        for part in rf.to_rotating(r, v, angle, rate) + rf.to_inertial(r, v, angle, rate):
            assert type(part) is tuple and len(part) == 3 and all(type(k) is float for k in part)


def test_signs_by_hand_in_each_direction():
    assert rf.to_rotating((1, 2, 3), (4, 5, 6), 0, 0) == ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)) == rf.to_inertial((1, 2, 3), (4, 5, 6), 0, 0)
    assert rf.to_rotating((1, 0, 0), (0, 0, 0), 0, 2.0) == ((1.0, 0.0, 0.0), (0.0, -2.0, 0.0)) and rf.to_inertial((1, 0, 0), (0, 0, 0), 0, 2.0) == ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0))
    assert rf.to_rotating((0, 1, 0), (0, 0, 0), 0, 2.0) == ((0.0, 1.0, 0.0), (2.0, 0.0, 0.0)) and rf.to_inertial((0, 1, 0), (0, 0, 0), 0, 2.0) == ((0.0, 1.0, 0.0), (-2.0, 0.0, 0.0))
    assert rf.to_rotating((0, 0, 9), (0, 0, 0), 1.0, 2.0) == ((0.0, 0.0, 9.0), (0.0, 0.0, 0.0))        # a point on the axis does not move
    assert rf.to_rotating((3, 4, 5), (10, 20, 30), 0, 0.5) == ((3.0, 4.0, 5.0), (12.0, 18.5, 30.0))    # (10 + 0.5 * 4, 20 - 0.5 * 3, 30)
    assert rf.to_inertial((3, 4, 5), (10, 20, 30), 0, 0.5) == ((3.0, 4.0, 5.0), (8.0, 21.5, 30.0))     # (10 - 0.5 * 4, 20 + 0.5 * 3, 30)
    q = rf.to_rotating((2, 0, 0), (0, 3, 0), math.pi / 2, 0)                                           # quarter turn: x -> -y', y -> x'
    assert q[0] == pytest.approx((0.0, -2.0, 0.0), abs=3e-16) and q[1] == pytest.approx((3.0, 0.0, 0.0), abs=3e-16)
    q = rf.to_inertial((2, 0, 0), (0, 3, 0), math.pi / 2, 0)                                           # the other way: x' -> y, y' -> -x
    assert q[0] == pytest.approx((0.0, 2.0, 0.0), abs=3e-16) and q[1] == pytest.approx((-3.0, 0.0, 0.0), abs=3e-16)
    assert rf.to_rotating((7000, 0, 0), (0, 0, 0), 0) == ((7000.0, 0.0, 0.0), (0.0, -7000 * rf.EARTH_RATE, 0.0)) and rf.EARTH_RATE == 7.292115e-5
    assert rf.to_rotating((7000, 0, 0), (0, 0, 0), 0, rf.EARTH_RATE) == rf.to_rotating((7000, 0, 0), (0, 0, 0), 0)      # the default rate
    assert rf.to_inertial((7000, 0, 0), (0, 0, 0), 0) == ((7000.0, 0.0, 0.0), (0.0, 7000 * rf.EARTH_RATE, 0.0))


def test_zeros_are_positive():
    for out in (rf.to_rotating((-0.0, -0.0, -0.0), (-0.0, -0.0, -0.0), 0.0, 0.0), rf.to_inertial((-0.0, -0.0, -0.0), (-0.0, -0.0, -0.0), 0.0, 0.0),
                rf.to_rotating((-0.0, 0.0, -0.0), (0.0, -0.0, 0.0), -0.0, -0.0), rf.to_rotating((0.0, 0.0, -0.0), (0.0, 0.0, -0.0), 1.0, 2.0)):
        for part in out:
            assert part == (0.0, 0.0, 0.0) and all(math.copysign(1.0, k) == 1.0 for k in part)


def test_refusals_and_limits():
    assert rf.BIG == 1e15 and rf.MAX_ANGLE == 1e9 and rf.MAX_RATE == 1000.0
    good = (1.0, 2.0, 3.0)
    for f in (rf.to_rotating, rf.to_inertial):
        assert f((1e15, -1e15, 1e15), (-1e15, 1e15, 1e15), 1e9, 1000.0)[0][2] == 1e15 and f(good, good, -1e9, -1000.0)[1][2] == 3.0
        for bad in ((1.0, 2.0), (1.0, 2.0, 3.0, 4.0), "123", None, 5.0, iter(good)):
            with pytest.raises(ValueError, match="r must be a list or tuple of 3 numbers"):
                f(bad, good, 0.0)
            with pytest.raises(ValueError, match="v must be a list or tuple of 3 numbers"):
                f(good, bad, 0.0)
        for bad in (True, "1", None, float("nan"), float("inf"), -float("inf"), 1j, math.nextafter(1e15, math.inf), -math.nextafter(1e15, math.inf)):
            for k in range(3):
                vec = list(good)
                vec[k] = bad
                with pytest.raises(ValueError, match="a component of r"):
                    f(vec, good, 0.0)
                with pytest.raises(ValueError, match="a component of v"):
                    f(good, vec, 0.0)
        for bad in (True, "1", None, float("nan"), float("inf"), math.nextafter(1e9, math.inf), -math.nextafter(1e9, math.inf)):
            with pytest.raises(ValueError, match="angle"):
                f(good, good, bad)
        for bad in (True, "1", None, float("nan"), float("inf"), math.nextafter(1000.0, math.inf), -math.nextafter(1000.0, math.inf)):
            with pytest.raises(ValueError, match="rate"):
                f(good, good, 0.0, bad)
        assert f([1, 2, 3], [4, 5, 6], 1, 2) == f((1.0, 2.0, 3.0), (4.0, 5.0, 6.0), 1.0, 2.0)       # lists and integers
