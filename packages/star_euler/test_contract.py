"""Refusals of star_euler with hostile inputs (unknown sequences, NaN, inf, huge integers, booleans, text, wrong shapes,
matrices that are not rotations).
Verifies: R4 (README).

Every function returns finite floats or raises ValueError: never NaN, never a guess about the sequence."""
import math

import pytest

import star_euler as e

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e150, -1e150, True, False, "1", None, 1j, [1.0], (1.0,)]
BAD_SEQ = ["", "zyx", "ZYZX", "ZY", "ZZX", "XXY", "ABC", "XYW", " ZYX", "ZYX ", None, 5, ("Z", "Y", "X"), ["Z", "Y", "X"], b"ZYX", 321, "xyz", "ZZZ"]
EYE = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(BAD_SEQ) == 18 and e.__version__ == "0.1.0"
    assert (e.DCM_TOL, e.LOCK_TOL) == (1e-9, 2e-9) and e.__all__ == ["SEQUENCES", "to_dcm", "from_dcm", "is_singular"]
    assert e.SEQUENCES == ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX", "XYX", "XZX", "YXY", "YZY", "ZXZ", "ZYZ")


@pytest.mark.parametrize("seq", BAD_SEQ, ids=repr)
def test_an_unknown_sequence_is_refused_not_guessed(seq):
    for call in (lambda: e.to_dcm(seq, 1.0, 2.0, 3.0), lambda: e.from_dcm(seq, EYE), lambda: e.is_singular(seq, EYE)):
        with pytest.raises(ValueError, match="sequence must be one of"):
            call()


def test_angles_refuse_hostile_values():
    for bad in BAD:
        for k in range(3):
            a = [10.0, 20.0, 30.0]
            a[k] = bad
            with pytest.raises(ValueError):
                e.to_dcm("ZYX", *a)
    out = e.to_dcm("ZYX", 9e149, -9e149, 5)
    assert all(type(v) is float and math.isfinite(v) for row in out for v in row)


@pytest.mark.parametrize("m, why", [
    (((1, 0, 0), (0, 1, 0), (0, 0, -1)), "reflection"), (((0, 1, 0), (1, 0, 0), (0, 0, 1)), "reflection"),
    (((1, 0, 0), (0, 1, 0), (0, 0, 1.000001)), "orthonormal"), (((1, 1e-8, 0), (0, 1, 0), (0, 0, 1)), "orthonormal"),
    (((2, 0, 0), (0, 2, 0), (0, 0, 2)), "orthonormal"), (((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orthonormal")])
def test_a_matrix_that_is_not_a_rotation_is_refused(m, why):
    for f in (e.from_dcm, e.is_singular):
        with pytest.raises(ValueError, match=why):
            f("ZYX", m)


def test_matrix_shape_and_hostile_entries_are_refused():
    for bad in (None, 5, "abc", EYE[:2], EYE + ((0, 0, 1),), ((1, 0), (0, 1), (0, 0)), (1, 2, 3), {0: (1, 0, 0), 1: (0, 1, 0), 2: (0, 0, 1)},
                ((1, 0, 0), (0, 1, 0), "001"), ((1, 0, 0), (0, 1, 0), None), ((1, 0, 0), (0, 1, 0), 5)):
        for f in (e.from_dcm, e.is_singular):
            with pytest.raises(ValueError):
                f("ZYX", bad)
    for bad in BAD:
        for i in range(3):
            for j in range(3):
                m = [list(r) for r in EYE]
                m[i][j] = bad
                with pytest.raises(ValueError):
                    e.from_dcm("XYZ", m)


def test_results_are_plain_floats_in_range_and_identity_is_all_zeros():
    for seq in e.SEQUENCES:
        out = e.from_dcm(seq, EYE)
        assert out == (0.0, 0.0, 0.0) and all(type(v) is float and str(v) == "0.0" for v in out)
        assert e.is_singular(seq, EYE) is (seq[0] == seq[2])                      # identity is gimbal lock for the proper sequences
        m = e.to_dcm(seq, 12, 34, 56)
        assert isinstance(m, tuple) and all(isinstance(r, tuple) and all(type(v) is float for v in r) for r in m)
    assert e.from_dcm("ZYX", [[0, -1, 0], [1, 0, 0], [0, 0, 1]]) == (90.0, 0.0, 0.0)                 # integers and lists
    nearly = ((1.0, 5e-10, 0.0), (-5e-10, 1.0, 0.0), (0.0, 0.0, 1.0))                                 # within the tolerance
    assert all(map(math.isfinite, e.from_dcm("ZYX", nearly)))
