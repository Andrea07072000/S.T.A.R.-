"""star_wahba against published values and hand-derivable invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_wahba as sw


def _matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


def _det(a):
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def _apply(a, v):
    return tuple(sum(a[i][j] * v[j] for j in range(3)) for i in range(3))


def test_published_quarter_turn_about_z_triad_qmethod_rotation_matrix():
    q = (0.7071067811865476, 0.0, 0.0, 0.7071067811865476)
    a_expect = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    a_rm = sw.rotation_matrix(q)
    for i in range(3):
        for j in range(3):
            assert a_rm[i][j] == pytest.approx(a_expect[i][j], abs=3e-16)

    refs = [(1, 0, 0), (0, 1, 0)]
    bodies = [(0, -1, 0), (1, 0, 0)]
    a_t = sw.triad(*refs, *bodies)
    q_m = sw.q_method(refs, bodies)
    a_q = sw.rotation_matrix(q_m)
    for i in range(3):
        for j in range(3):
            assert a_t[i][j] == pytest.approx(a_expect[i][j], abs=1e-15)
            assert a_q[i][j] == pytest.approx(a_expect[i][j], abs=1e-15)
    assert q_m[0] == pytest.approx(q[0], abs=1e-15)
    assert q_m[1] == pytest.approx(0.0, abs=1e-15)
    assert q_m[2] == pytest.approx(0.0, abs=1e-15)
    assert q_m[3] == pytest.approx(q[3], abs=1e-15)


def test_identity_and_half_turn_about_x():
    refs = [(1, 2, 3), (-2, 1, 4)]
    q = sw.q_method(refs, refs)
    a = sw.rotation_matrix(q)
    i3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    for i in range(3):
        for j in range(3):
            assert a[i][j] == pytest.approx(i3[i][j], abs=1e-15)
    assert q[0] == pytest.approx(1.0, abs=1e-15)

    refs2 = [(0, 1, 0), (0, 0, 1)]
    bodies2 = [(0, -1, 0), (0, 0, -1)]
    a2 = sw.rotation_matrix(sw.q_method(refs2, bodies2))
    expect = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
    for i in range(3):
        for j in range(3):
            assert a2[i][j] == pytest.approx(expect[i][j], abs=1e-15)


def test_hand_derived_axis_rotations_and_q_minus_q_same_matrix():
    # By formula in doc: q=(cos(t/2), sin(t/2),0,0) gives x-axis rotation matrix with cos t / sin t entries.
    t = 0.7
    qx = (math.cos(t / 2.0), math.sin(t / 2.0), 0.0, 0.0)
    a = sw.rotation_matrix(qx)
    expect = ((1.0, 0.0, 0.0), (0.0, math.cos(t), math.sin(t)), (0.0, -math.sin(t), math.cos(t)))
    for i in range(3):
        for j in range(3):
            assert a[i][j] == pytest.approx(expect[i][j], abs=1e-15)

    ty = 0.9
    qy = (math.cos(ty / 2.0), 0.0, math.sin(ty / 2.0), 0.0)
    ay = sw.rotation_matrix(qy)
    expecty = ((math.cos(ty), 0.0, -math.sin(ty)), (0.0, 1.0, 0.0), (math.sin(ty), 0.0, math.cos(ty)))
    for i in range(3):
        for j in range(3):
            assert ay[i][j] == pytest.approx(expecty[i][j], abs=1e-15)

    an = sw.rotation_matrix(tuple(-c for c in qy))
    for i in range(3):
        for j in range(3):
            assert an[i][j] == pytest.approx(ay[i][j], abs=0.0)

    i3 = sw.rotation_matrix((2.0, 0.0, 0.0, 0.0))
    assert [c for row in i3 for c in row] == pytest.approx([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], abs=1e-15)      # corrected by the reviewer: approx does not compare nested tuples


def test_orthogonality_and_det_plus_one():
    q = sw.q_method([(1, 2, 3), (4, 5, 6), (-2, 1, 4)], [(-2, 1, 4), (1, -1, 2), (3, 0, -1)])
    a = sw.rotation_matrix(q)
    aat = _matmul(a, _transpose(a))
    for i in range(3):
        for j in range(3):
            assert aat[i][j] == pytest.approx(1.0 if i == j else 0.0, abs=1e-14)
    assert _det(a) == pytest.approx(1.0, abs=1e-14)


def test_scaling_invariance_of_vectors_and_weights_and_noise_free_loss():
    a0 = sw.rotation_matrix((0.9, 0.1, -0.2, 0.35))
    refs = [(1, 2, 3), (-2, 1, 4), (3, -1, 5)]
    bodies = [_apply(a0, r) for r in refs]
    q = sw.q_method(refs, bodies, [1, 3, 5])
    q_scaled = sw.q_method([(10 * x, 10 * y, 10 * z) for x, y, z in refs], [(7 * x, 7 * y, 7 * z) for x, y, z in bodies], [7, 21, 35])
    a = sw.rotation_matrix(q)
    a2 = sw.rotation_matrix(q_scaled)
    for i in range(3):
        for j in range(3):
            assert a[i][j] == pytest.approx(a0[i][j], abs=1e-12)
            assert a2[i][j] == pytest.approx(a0[i][j], abs=1e-12)
    assert sw.wahba_loss(q, refs, bodies, [1, 3, 5]) < 1e-25
    assert sw.wahba_loss(q, refs, bodies, [7, 21, 35]) < 1e-25


def test_published_inconsistent_two_pair_loss_value():
    # Derivation: inconsistent separations 90 deg vs 80 deg -> mismatch d=10 deg.
    # Equal weights optimum splits error equally, each residual angle d/2=5 deg.
    # Loss = 1 - cos(d/2) = 1 - cos(5 deg) = 0.0038053019082545.
    refs = [(1, 0, 0), (0, 1, 0)]  # 90 deg
    c80, s80 = math.cos(math.radians(80.0)), math.sin(math.radians(80.0))
    bodies = [(1, 0, 0), (c80, s80, 0.0)]  # 80 deg
    q = sw.q_method(refs, bodies, [1, 1])
    loss = sw.wahba_loss(q, refs, bodies, [1, 1])
    assert loss == pytest.approx(0.0038053019082545, abs=1e-14)
    assert loss <= 2.0
