"""star_euler: the twelve sequences on rotations that can be done by hand.
Verifies: R1, R2, R3 (README).

Reference: the aerospace yaw-pitch-roll sequence (Z, then the new Y, then the new X) and its direction cosine matrix
as printed in any flight-dynamics text; elementary rotations by the right-hand rule; for the proper sequences the
classical Euler angles of ZXZ (precession, nutation, spin).
The comparison with SciPy and NAIF SPICE over all twelve sequences (744 cases) is in crosscheck_euler.py."""
import math
import random

import pytest

import star_euler as e

TAIT = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")
PROPER = ("XYX", "XZX", "YXY", "YZY", "ZXZ", "ZYZ")


def apply(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def close(a, b, tol=1e-12):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def mclose(a, b, tol=1e-12):
    return all(abs(a[i][j] - b[i][j]) <= tol for i in range(3) for j in range(3))


def test_the_twelve_sequences():
    assert e.SEQUENCES == TAIT + PROPER and len(set(e.SEQUENCES)) == 12


def test_single_rotations_follow_the_right_hand_rule():
    assert close(apply(e.to_dcm("ZYX", 90, 0, 0), (1, 0, 0)), (0, 1, 0))            # yaw: X -> Y
    assert close(apply(e.to_dcm("ZYX", 0, 90, 0), (1, 0, 0)), (0, 0, -1))           # pitch about Y: X -> -Z
    assert close(apply(e.to_dcm("ZYX", 0, 0, 90), (0, 1, 0)), (0, 0, 1))            # roll about X: Y -> Z
    assert close(apply(e.to_dcm("XYZ", 90, 0, 0), (0, 1, 0)), (0, 0, 1)) and close(apply(e.to_dcm("XYZ", 0, 0, 90), (1, 0, 0)), (0, 1, 0))
    assert close(apply(e.to_dcm("ZXZ", 30, 0, 60), (1, 0, 0)), (0, 1, 0))           # two turns about the same axis add up
    assert e.to_dcm("YXZ", 0, 0, 0) == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def test_yaw_pitch_roll_matrix_as_printed_in_flight_dynamics_texts():
    y, p, r = 30.0, 20.0, 10.0
    cy, sy, cp, sp, cr, sr = (f(math.radians(a)) for a in (y, p, r) for f in (math.cos, math.sin))
    expected = ((cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
                (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
                (-sp, cp * sr, cp * cr))
    assert mclose(e.to_dcm("ZYX", y, p, r), expected, 1e-15)
    assert close(e.from_dcm("ZYX", expected), (y, p, r), 1e-12)


def test_rotations_are_intrinsic_the_second_is_about_the_new_axis():
    # pitch 90 tilts the nose in the body's own vertical plane: whatever the yaw, body X ends pointing along -Z
    for yaw in (0, 37, 90, 200):
        assert close(apply(e.to_dcm("ZYX", yaw, 90, 0), (1, 0, 0)), (0, 0, -1))
    # yaw 90 then pitch 90: intrinsic = Rz(90) Ry(90) sends +Y to -X; the extrinsic reading Ry(90) Rz(90) would send it to +Z
    m = e.to_dcm("ZYX", 90, 90, 0)
    assert close(apply(m, (0, 1, 0)), (-1, 0, 0))
    assert close(m[0], (0, -1, 0)) and close(m[1], (0, 0, 1)) and close(m[2], (-1, 0, 0))


@pytest.mark.parametrize("seq", TAIT + PROPER)
def test_matrix_is_the_product_of_three_elementary_rotations(seq):
    def elem(axis, deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        return {"X": ((1, 0, 0), (0, c, -s), (0, s, c)), "Y": ((c, 0, s), (0, 1, 0), (-s, 0, c)), "Z": ((c, -s, 0), (s, c, 0), (0, 0, 1))}[axis]

    def mul(a, b):
        return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    a = (41.0, -23.0, 117.0)
    assert mclose(e.to_dcm(seq, *a), mul(mul(elem(seq[0], a[0]), elem(seq[1], a[1])), elem(seq[2], a[2])), 1e-15)


@pytest.mark.parametrize("seq", TAIT + PROPER)
def test_angles_come_back_in_the_principal_ranges(seq):
    rnd = random.Random(sum(map(ord, seq)))
    proper = seq in PROPER
    for _ in range(200):
        mid = rnd.uniform(0.01, 179.99) if proper else rnd.uniform(-89.99, 89.99)
        a = (rnd.uniform(-179.99, 179.99), mid, rnd.uniform(-179.99, 179.99))
        back = e.from_dcm(seq, e.to_dcm(seq, *a))
        assert close(back, a, 1e-9) and e.is_singular(seq, e.to_dcm(seq, *a)) is False
    # angles outside the principal ranges describe the same rotation and come back inside them
    for a in ((200.0, 100.0, -300.0), (-540.0, -100.0, 725.0), (10.0, 190.0, 20.0)):
        m = e.to_dcm(seq, *a)
        b = e.from_dcm(seq, m)
        assert mclose(e.to_dcm(seq, *b), m, 1e-12) and -180 < b[0] <= 180 and -180 < b[2] <= 180
        assert (0 <= b[1] <= 180) if proper else (-90 <= b[1] <= 90)


@pytest.mark.parametrize("seq", TAIT + PROPER)
def test_gimbal_lock_is_reported_and_the_rotation_is_still_recovered(seq):
    proper = seq in PROPER
    for mid in ((0.0, 180.0) if proper else (90.0, -90.0)):
        for a1, a3 in ((30.0, 50.0), (-120.0, 77.0), (0.0, 0.0)):
            m = e.to_dcm(seq, a1, mid, a3)
            assert e.is_singular(seq, m) is True
            b = e.from_dcm(seq, m)
            assert b[2] == 0.0 and abs(b[1] - mid) < 1e-6 and mclose(e.to_dcm(seq, *b), m, 1e-12)
    near = e.to_dcm(seq, 30.0, (0.001 if proper else 89.999), 50.0)             # a thousandth of a degree away: regular
    assert e.is_singular(seq, near) is False and close(e.from_dcm(seq, near), (30.0, 0.001 if proper else 89.999, 50.0), 1e-6)


def test_classical_euler_angles_zxz():
    # precession 40 about Z, nutation 25 about the line of nodes (new X), spin 60 about the new Z
    m = e.to_dcm("ZXZ", 40, 25, 60)
    assert close(apply(m, (0, 0, 1)), (math.sin(math.radians(40)) * math.sin(math.radians(25)),
                                       -math.cos(math.radians(40)) * math.sin(math.radians(25)), math.cos(math.radians(25))))
    assert abs(m[2][2] - math.cos(math.radians(25))) < 1e-15 and close(e.from_dcm("ZXZ", m), (40, 25, 60), 1e-12)
