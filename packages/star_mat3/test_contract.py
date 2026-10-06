"""star_mat3 contract/refusal tests with pinned hostile values and range edges.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math
from fractions import Fraction

import pytest

import star_mat3 as sm


HOSTILE = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1 + 2j, 1.0000001e60]
GOOD_M = ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 3.0))
GOOD_V = (1.0, 2.0, 3.0)


def test_pinned_constants_and_exports():
    assert sm.__all__ == ["transpose", "determinant", "inverse", "matmul", "matvec", "identity", "is_rotation"]
    assert sm.__version__ == "0.1.0"
    assert sm.BIG == 1e60
    assert sm.SINGULAR == 1e-12


@pytest.mark.parametrize("bad_m", [
    ((1, 2, 3), (4, 5, 6)),                              # two rows
    ((1, 2, 3), (4, 5, 6), (7, 8, 9), (0, 0, 0)),       # four rows
    ((1, 2), (3, 4, 5), (6, 7, 8)),                      # row of two
    (1, 2, 3, 4, 5, 6, 7, 8, 9),                         # flat 9
    "matrix", None, 7
])
def test_matrix_shape_type_refusals_every_public_matrix_arg(bad_m):
    for f, args in [
        (sm.transpose, (bad_m,)),
        (sm.determinant, (bad_m,)),
        (sm.inverse, (bad_m,)),
        (sm.matmul, (bad_m, GOOD_M)),
        (sm.matmul, (GOOD_M, bad_m)),
        (sm.matvec, (bad_m, GOOD_V)),
        (sm.is_rotation, (bad_m,))
    ]:
        with pytest.raises(ValueError):
            f(*args)


def test_hostile_entry_refused_in_matrix_positions_and_vector_positions():
    for bad in HOSTILE:
        m = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        m[1][2] = bad
        with pytest.raises(ValueError):
            sm.determinant(m)
        v = [1.0, 2.0, 3.0]
        v[0] = bad
        with pytest.raises(ValueError):
            sm.matvec(GOOD_M, v)


@pytest.mark.parametrize("bad_v", [None, "v", 3, (1, 2), (1, 2, 3, 4), [1, 2]])
def test_matvec_vector_shape_type_refusals(bad_v):
    with pytest.raises(ValueError):
        sm.matvec(GOOD_M, bad_v)


def test_limits_inside_outside_for_entries_and_tol():
    assert sm.determinant(((1e60, 0, 0), (0, 1, 0), (0, 0, 1))) == 1e60
    with pytest.raises(ValueError):
        sm.determinant(((1.0000001e60, 0, 0), (0, 1, 0), (0, 0, 1)))

    c, s = math.cos(0.2), math.sin(0.2)
    R = ((c, s, 0.0), (-s, c, 0.0), (0.0, 0.0, 1.0))
    assert sm.is_rotation(R, tol=1.0) is True
    for bad_tol in (0.0, -1e-9, 1.0000001, float("nan"), True, "1e-6"):
        with pytest.raises(ValueError):
            sm.is_rotation(R, bad_tol)


def test_inverse_refusals_singular_near_singular_and_overflow_message():
    with pytest.raises(ValueError, match="singular"):
        sm.inverse(((1, 2, 3), (2, 4, 6), (1, 0, 1)))
    with pytest.raises(ValueError, match="singular"):
        sm.inverse(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    with pytest.raises(ValueError, match="singular"):
        sm.inverse(((1, 0, 0), (0, 1, 0), (0, 0, 1e-13)))
    assert sm.inverse(((1, 0, 0), (0, 1, 0), (0, 0, 1.1e-12)))
    with pytest.raises(ValueError, match="overflows"):
        sm.inverse(((1e-320, 0, 0), (0, 1e-320, 0), (0, 0, 1e-320)))


def test_ints_tuples_lists_fraction_accepted():
    m = [[2, 0, 0], [0, Fraction(3, 1), 0], [0, 0, 4]]
    assert sm.determinant(m) == 24.0
    assert sm.matmul(((1, 0, 0), (0, 1, 0), (0, 0, 1)), m) == ((2.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 4.0))
