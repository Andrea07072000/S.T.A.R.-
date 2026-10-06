"""star_mat3 behavioural tests from hand-derivable values and invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_mat3 as sm


A = ((2, 0, 1), (1, 3, 2), (1, 0, 1))
B = ((0, 1, 0), (0, 0, 1), (1, 0, 0))


def test_hand_values_for_a_and_identity_and_types():
    inv_a = sm.inverse(A)
    # From FACTS: exact inverse entries from adjugate/determinant.
    assert inv_a == ((1.0, 0.0, -1.0), (1.0 / 3.0, 1.0 / 3.0, -1.0), (-1.0, 0.0, 2.0))
    # Expanding det(A) along col 2: 3 * (2*1 - 1*1) = 3.
    assert sm.determinant(A) == 3.0
    assert sm.transpose(A) == ((2.0, 1.0, 1.0), (0.0, 3.0, 0.0), (1.0, 2.0, 1.0))
    assert sm.matvec(A, (1, 2, 3)) == (5.0, 13.0, 4.0)
    assert sm.matvec(sm.transpose(A), (1, 2, 3)) == (7.0, 6.0, 8.0)

    i = sm.identity()
    assert i == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    assert sm.determinant(i) == 1.0
    assert sm.inverse(i) == i
    assert sm.matmul(i, A) == ((2.0, 0.0, 1.0), (1.0, 3.0, 2.0), (1.0, 0.0, 1.0))
    assert sm.matmul(A, i) == ((2.0, 0.0, 1.0), (1.0, 3.0, 2.0), (1.0, 0.0, 1.0))
    assert sm.matvec(i, (4, 5, 6)) == (4.0, 5.0, 6.0)
    assert type(sm.determinant(A)) is float and sm.is_rotation(B) is True


def test_products_noncommutative_associative_with_vector_and_det_multiplicative():
    assert sm.matmul(A, B) == ((1.0, 2.0, 0.0), (2.0, 1.0, 3.0), (1.0, 1.0, 0.0))
    assert sm.matmul(B, A) == ((1.0, 3.0, 2.0), (1.0, 0.0, 1.0), (2.0, 0.0, 1.0))
    assert sm.transpose(sm.matmul(A, B)) == sm.matmul(sm.transpose(B), sm.transpose(A))
    v = (3, -2, 5)
    assert sm.matvec(sm.matmul(A, B), v) == sm.matvec(A, sm.matvec(B, v))
    assert sm.determinant(sm.matmul(A, B)) == sm.determinant(A) * sm.determinant(B)


def test_inverse_and_rotation_invariants_and_perturbation_tolerance():
    ai = sm.inverse(A)
    p = sm.matmul(A, ai)
    for r in range(3):
        for c in range(3):
            assert abs(p[r][c] - (1.0 if r == c else 0.0)) <= 1e-15

    c, s = math.cos(0.3), math.sin(0.3)
    R = ((c, s, 0.0), (-s, c, 0.0), (0.0, 0.0, 1.0))
    assert sm.is_rotation(R) is True
    assert abs(sm.determinant(R) - 1.0) <= 1e-15
    Rt = sm.transpose(R)
    Ri = sm.inverse(R)
    for i in range(3):
        for j in range(3):
            assert abs(Ri[i][j] - Rt[i][j]) <= 1e-15
    v = (0.2, -0.4, 0.9)
    back = sm.matvec(Rt, sm.matvec(R, v))
    for i in range(3):
        assert abs(back[i] - float(v[i])) <= 1e-15

    assert sm.is_rotation(((1, 0, 0), (0, 1, 0), (0, 0, -1))) is False
    assert sm.is_rotation(A) is False
    assert sm.is_rotation(((2, 0, 0), (0, 2, 0), (0, 0, 2))) is False
    Rp = ((c + 1e-9, s, 0.0), (-s, c, 0.0), (0.0, 0.0, 1.0))
    assert sm.is_rotation(Rp) is False
    assert sm.is_rotation(Rp, tol=1e-6) is True


def test_exactness_scale_and_singularity_threshold_edges():
    # (1e8+1)(1e8-1) - 1e16 = -1 exactly.
    M = ((1e8 + 1, 1e8, 0), (1e8, 1e8 - 1, 0), (0, 0, 1))
    assert sm.determinant(M) == -1.0

    d234 = ((2, 0, 0), (0, 3, 0), (0, 0, 4))
    assert sm.determinant(d234) == 24.0
    assert sm.inverse(((4, 0, 0), (0, 2, 0), (0, 0, 1))) == ((0.25, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 1.0))

    with pytest.raises(ValueError, match="singular"):
        sm.inverse(((1, 0, 0), (0, 1, 0), (0, 0, 1e-13)))
    assert sm.inverse(((1, 0, 0), (0, 1, 0), (0, 0, 1.1e-12)))  # accepted edge just inside

    s = 1e-200
    lhs = sm.inverse(tuple(tuple(s * float(x) for x in row) for row in A))
    rhs = tuple(tuple(1e200 * x for x in row) for row in sm.inverse(A))
    for i in range(3):
        for j in range(3):
            assert lhs[i][j] == pytest.approx(rhs[i][j], rel=1e-15, abs=0.0)

    assert sm.inverse(((1e-200, 0, 0), (0, 1e-200, 0), (0, 0, 1e-200)))
