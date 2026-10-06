"""Refusals of star_quaternion with hostile inputs (NaN, inf, huge integers, booleans, text, wrong shapes, non-unit
quaternions, matrices that are not rotations).
Verifies: R4 (README).

Every function returns finite floats or raises ValueError: never NaN, never a silently normalised wrong input."""
import math

import pytest

import star_quaternion as a

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e150, -1e150, True, False, "1", None, 1j, [1.0], (1.0,)]
BAD_SHAPE = [None, 5, "abcd", b"abcd", (1, 0, 0), (1, 0, 0, 0, 0), [], {0: 1, 1: 0, 2: 0, 3: 0}, {1, 2, 3, 4}, iter([1, 0, 0, 0])]
S = math.sqrt(0.5)
Q, V = (S, 0.0, 0.0, S), (1.0, 2.0, 3.0)
EYE = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
QUAT_FUNCS = {"normalize": lambda q: a.normalize(q), "conjugate": lambda q: a.conjugate(q), "to_dcm": lambda q: a.to_dcm(q),
              "to_axis_angle": lambda q: a.to_axis_angle(q), "multiply_left": lambda q: a.multiply(q, Q), "multiply_right": lambda q: a.multiply(Q, q),
              "rotate": lambda q: a.rotate(q, V), "angle_left": lambda q: a.angle_between_deg(q, Q), "angle_right": lambda q: a.angle_between_deg(Q, q)}


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(BAD_SHAPE) == 10 and len(QUAT_FUNCS) == 9 and a.__version__ == "0.1.0"
    assert (a.UNIT_TOL, a.DCM_TOL) == (1e-6, 1e-9)
    assert a.__all__ == ["normalize", "conjugate", "multiply", "rotate", "to_dcm", "from_dcm", "from_axis_angle", "to_axis_angle", "angle_between_deg"]


@pytest.mark.parametrize("name", sorted(QUAT_FUNCS))
def test_quaternion_arguments_refuse_hostile_values_and_shapes(name):
    f = QUAT_FUNCS[name]
    f(Q)
    for bad in BAD:
        for i in range(4):
            q = list(Q)
            q[i] = bad
            with pytest.raises(ValueError):
                f(q)
    for bad in BAD_SHAPE:
        with pytest.raises(ValueError):
            f(bad)
    with pytest.raises(ValueError):
        f((0.0, 0.0, 0.0, 0.0))


@pytest.mark.parametrize("name", sorted(n for n in QUAT_FUNCS if n != "normalize"))
def test_a_quaternion_that_is_not_unit_is_refused_not_normalised(name):
    f = QUAT_FUNCS[name]
    for scale in (1 + 2e-6, 1 - 2e-6, 2.0, 0.5, 1e-9):
        with pytest.raises(ValueError, match="not a unit quaternion"):
            f(tuple(c * scale for c in Q))
    for scale in (1 + 9e-7, 1 - 9e-7):
        f(tuple(c * scale for c in Q))


def test_vectors_axes_and_angles_refuse_hostile_values():
    for bad in BAD:
        for i in range(3):
            v = list(V)
            v[i] = bad
            with pytest.raises(ValueError):
                a.rotate(Q, v)
            with pytest.raises(ValueError):
                a.from_axis_angle(v, 10.0)
        with pytest.raises(ValueError):
            a.from_axis_angle(V, bad)
    for bad in (None, 5, "abc", (1, 2), (1, 2, 3, 4), {1, 2, 3}):
        with pytest.raises(ValueError):
            a.rotate(Q, bad)
        with pytest.raises(ValueError):
            a.from_axis_angle(bad, 10.0)
    for zero in ((0, 0, 0), (0.0, -0.0, 0.0)):
        with pytest.raises(ValueError, match="not an axis"):
            a.from_axis_angle(zero, 10.0)
    assert all(map(math.isfinite, a.from_axis_angle((9e149, -9e149, 9e149), 9e149))) and all(map(math.isfinite, a.rotate(Q, (9e149, 9e149, 9e149))))


@pytest.mark.parametrize("m, why", [
    (((1, 0, 0), (0, 1, 0), (0, 0, -1)), "reflection"), (((0, 1, 0), (1, 0, 0), (0, 0, 1)), "reflection"),
    (((1, 0, 0), (0, 1, 0), (0, 0, 1.000001)), "orthonormal"), (((1, 1e-8, 0), (0, 1, 0), (0, 0, 1)), "orthonormal"),
    (((2, 0, 0), (0, 2, 0), (0, 0, 2)), "orthonormal"), (((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orthonormal"),
    (((1, 0, 0), (0, 1, 0), (1, 0, 0)), "orthonormal")])
def test_a_matrix_that_is_not_a_rotation_is_refused(m, why):
    with pytest.raises(ValueError, match=why):
        a.from_dcm(m)


def test_matrix_shape_and_hostile_entries_are_refused():
    for bad in (None, 5, "abc", EYE[:2], EYE + ((0, 0, 1),), ((1, 0), (0, 1), (0, 0)), (1, 2, 3), {0: (1, 0, 0), 1: (0, 1, 0), 2: (0, 0, 1)},
                ((1, 0, 0), (0, 1, 0), "001"), ((1, 0, 0), (0, 1, 0), None)):
        with pytest.raises(ValueError):
            a.from_dcm(bad)
    for bad in BAD:
        for i in range(3):
            for j in range(3):
                m = [list(r) for r in EYE]
                m[i][j] = bad
                with pytest.raises(ValueError):
                    a.from_dcm(m)
    assert a.from_dcm([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == (1.0, 0.0, 0.0, 0.0)                   # integers and lists are fine
    nearly = ((1.0, 5e-10, 0.0), (-5e-10, 1.0, 0.0), (0.0, 0.0, 1.0))                               # within the tolerance
    q = a.from_dcm(nearly)
    assert abs(math.hypot(*q) - 1) < 1e-15 and q[0] > 0.999999


def test_results_are_plain_finite_floats():
    outs = [a.normalize((1, 2, 3, 4)), a.conjugate(Q), a.multiply(Q, Q), a.rotate(Q, (1, 2, 3)), a.from_dcm(EYE), a.from_axis_angle((1, 2, 3), 77)]
    outs += list(a.to_dcm(Q)) + [a.to_axis_angle(Q)[0], (a.to_axis_angle(Q)[1], a.angle_between_deg(Q, Q))]
    for out in outs:
        assert isinstance(out, tuple) and all(type(v) is float and math.isfinite(v) for v in out)
