"""star_quaternion: the convention, checked on rotations that can be done by hand.
Verifies: R1, R2, R3 (README).

Reference: the definition used by NAIF SPICE (Rotations Required Reading): the unit quaternion
(cos(t/2), sin(t/2) u) is the rotation by t about u, and the rotation by +90 degrees about +Z takes +X to +Y.
The comparison with SPICE and SciPy on 411 cases is in crosscheck_quaternion.py."""
import math
import random

import pytest

import star_quaternion as a

S = math.sqrt(0.5)
I = (1.0, 0.0, 0.0, 0.0)
X90, Y90, Z90 = (S, S, 0.0, 0.0), (S, 0.0, S, 0.0), (S, 0.0, 0.0, S)


def close(p, q, tol=1e-12):
    return len(p) == len(q) and all(abs(x - y) <= tol for x, y in zip(p, q))


def same_rotation(p, q, tol=1e-12):
    return close(p, q, tol) or close(p, tuple(-c for c in q), tol)


def test_quarter_turns_follow_the_right_hand_rule():
    assert close(a.rotate(Z90, (1, 0, 0)), (0, 1, 0)) and close(a.rotate(Z90, (0, 1, 0)), (-1, 0, 0)) and close(a.rotate(Z90, (0, 0, 1)), (0, 0, 1))
    assert close(a.rotate(X90, (0, 1, 0)), (0, 0, 1)) and close(a.rotate(X90, (0, 0, 1)), (0, -1, 0))
    assert close(a.rotate(Y90, (0, 0, 1)), (1, 0, 0)) and close(a.rotate(Y90, (1, 0, 0)), (0, 0, -1))
    assert a.rotate(I, (3.0, -4.0, 5.0)) == (3.0, -4.0, 5.0)


def test_matrix_of_the_quarter_turn_about_z_and_of_the_identity():
    m = a.to_dcm(Z90)
    for row, expected in zip(m, ((0, -1, 0), (1, 0, 0), (0, 0, 1))):
        assert close(row, expected)
    assert a.to_dcm(I) == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    for row, expected in zip(a.to_dcm(a.from_axis_angle((1, 0, 0), 30)), ((1, 0, 0), (0, c, -s), (0, s, c))):
        assert close(row, expected)
    for row, expected in zip(a.to_dcm(a.from_axis_angle((0, 1, 0), 30)), ((c, 0, s), (0, 1, 0), (-s, 0, c))):
        assert close(row, expected)


def test_product_applies_the_right_factor_first():
    # turn about Z first, then about X: +X goes to +Y, then +Y goes to +Z
    q = a.multiply(X90, Z90)
    assert close(a.rotate(q, (1, 0, 0)), (0, 0, 1))
    assert close(a.rotate(a.multiply(Z90, X90), (1, 0, 0)), (0, 1, 0))            # the other order leaves +X at +Y
    assert same_rotation(a.multiply(Z90, Z90), (0, 0, 0, 1)) and same_rotation(a.multiply(a.multiply(Z90, Z90), a.multiply(Z90, Z90)), I)
    assert close(a.multiply((0, 1, 0, 0), (0, 0, 1, 0)), (0, 0, 0, 1)) and close(a.multiply((0, 0, 1, 0), (0, 1, 0, 0)), (0, 0, 0, -1))   # ij = k, ji = -k
    assert close(a.multiply((0, 0, 1, 0), (0, 0, 0, 1)), (0, 1, 0, 0)) and close(a.multiply((0, 0, 0, 1), (0, 1, 0, 0)), (0, 0, 1, 0))    # jk = i, ki = j


def test_product_matches_the_matrix_product_and_conjugate_is_the_inverse():
    rnd = random.Random(5)
    for _ in range(200):
        p, q = a.normalize([rnd.gauss(0, 1) for _ in range(4)]), a.normalize([rnd.gauss(0, 1) for _ in range(4)])
        mp, mq, mpq = a.to_dcm(p), a.to_dcm(q), a.to_dcm(a.multiply(p, q))
        for i in range(3):
            for j in range(3):
                assert abs(mpq[i][j] - sum(mp[i][k] * mq[k][j] for k in range(3))) < 1e-14
        assert same_rotation(a.multiply(p, a.conjugate(p)), I, 1e-15)
        v = [rnd.uniform(-5, 5) for _ in range(3)]
        w = a.rotate(p, v)
        assert close(a.rotate(a.conjugate(p), w), v, 1e-13) and abs(math.hypot(*w) - math.hypot(*v)) < 1e-13
        mt = a.to_dcm(a.conjugate(p))
        assert all(abs(mt[i][j] - mp[j][i]) < 1e-15 for i in range(3) for j in range(3))               # inverse = transpose
        assert same_rotation(a.from_dcm(mp), p, 1e-14) and a.from_dcm(mp)[0] >= 0.0


def test_from_dcm_on_half_turns_where_the_trace_method_divides_by_zero():
    for q in ((0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1), (0, S, S, 0), (0, S, 0, -S), a.normalize((0, 1, 2, 3)), a.normalize((1e-9, 3, -2, 1))):
        back = a.from_dcm(a.to_dcm(q))
        assert same_rotation(back, q, 1e-14) and abs(math.hypot(*back) - 1) < 1e-15
        lead = next(c for c in back if abs(c) > 1e-15)
        assert lead > 0                                                             # canonical sign
    assert a.from_dcm(((1, 0, 0), (0, 1, 0), (0, 0, 1))) == I
    assert a.from_dcm(((1, 0, 0), (0, -1, 0), (0, 0, -1))) == (0.0, 1.0, 0.0, 0.0)
    assert all(str(c) != "-0.0" for c in a.from_dcm(((-1, 0, 0), (0, -1, 0), (0, 0, 1))))


def test_axis_angle_round_trip_and_ranges():
    q = a.from_axis_angle((0, 0, 2), 90)
    assert close(q, Z90) and close(a.from_axis_angle((0, 0, -5e-300), -90), Z90) and close(a.from_axis_angle((3e140, 0, 4e140), 180), (0, 0.6, 0, 0.8), 1e-15)
    axis, angle = a.to_axis_angle(Z90)
    assert close(axis, (0, 0, 1)) and abs(angle - 90) < 1e-12
    axis, angle = a.to_axis_angle(a.from_axis_angle((0, 0, 1), 270))               # 270 about +Z is 90 about -Z
    assert close(axis, (0, 0, -1)) and abs(angle - 90) < 1e-12
    assert a.to_axis_angle(I) == ((1.0, 0.0, 0.0), 0.0) and a.to_axis_angle((-1, 0, 0, 0)) == ((1.0, 0.0, 0.0), 0.0)
    assert same_rotation(a.from_axis_angle((1, 2, 3), 360), I, 1e-15) and same_rotation(a.from_axis_angle((1, 2, 3), 400), a.from_axis_angle((1, 2, 3), 40), 1e-14)
    assert same_rotation(a.from_axis_angle((1, 2, 3), -40), a.conjugate(a.from_axis_angle((1, 2, 3), 40)), 1e-15)
    rnd = random.Random(9)
    for _ in range(100):
        ax, ang = [rnd.uniform(-1, 1) for _ in range(3)], rnd.uniform(0.001, 179.999)
        n = math.hypot(*ax)
        axis, angle = a.to_axis_angle(a.from_axis_angle(ax, ang))
        assert close(axis, [c / n for c in ax], 1e-10) and abs(angle - ang) < 1e-10


def test_small_angles_keep_their_precision():
    for ang in (1e-3, 1e-6, 1e-9, 1e-12):
        axis, angle = a.to_axis_angle(a.from_axis_angle((1, 1, 1), ang))
        assert angle == pytest.approx(ang, rel=1e-6)                                # acos(w) would return 0 below 1e-6 deg
        assert a.angle_between_deg(I, a.from_axis_angle((0, 1, 0), ang)) == pytest.approx(ang, rel=1e-6)


def test_angle_between_attitudes():
    assert a.angle_between_deg(Z90, Z90) == 0.0 and abs(a.angle_between_deg(I, Z90) - 90) < 1e-12
    assert abs(a.angle_between_deg(Z90, tuple(-c for c in Z90))) < 1e-12            # q and -q are the same attitude
    assert abs(a.angle_between_deg(a.from_axis_angle((1, 0, 0), 10), a.from_axis_angle((1, 0, 0), 200)) - 170) < 1e-12
    assert abs(a.angle_between_deg(X90, a.multiply(X90, a.from_axis_angle((0.3, -1, 2), 33))) - 33) < 1e-12
    assert abs(a.angle_between_deg(I, (0, 0, 1, 0)) - 180) < 1e-12


def test_normalize_and_tolerated_drift():
    assert close(a.normalize((2, 0, 0, 0)), I) and close(a.normalize((0, 3, 0, 4)), (0, 0.6, 0, 0.8))
    assert close(a.normalize((1e-200, 0, 0, 1e-200)), (S, 0, 0, S), 1e-15) and close(a.normalize((1e140, 0, 0, -1e140)), (S, 0, 0, -S), 1e-15)
    drift = tuple(c * (1 + 5e-7) for c in Z90)                                      # integration drift within the tolerance
    assert close(a.rotate(drift, (1, 0, 0)), (0, 1, 0)) and abs(math.hypot(*a.conjugate(drift)) - 1) < 1e-15
