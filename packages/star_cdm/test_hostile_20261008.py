"""Regression tests of 2026-10-08: rtn_axes divided by zero when the RTN frame does not exist."""
import math

import pytest

import star_cdm as sc


def test_rtn_axes_of_a_circular_equatorial_state():
    R, T, N = sc.rtn_axes((7000.0, 0.0, 0.0), (0.0, 7.5, 0.0))
    assert (R, T, N) == ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])


def test_rtn_axes_are_orthonormal_and_right_handed():
    R, T, N = sc.rtn_axes((6524.834, 6862.875, 6448.296), (4.901327, 5.533756, -1.976341))
    for a in (R, T, N):
        assert math.sqrt(sum(c * c for c in a)) == pytest.approx(1.0, rel=0, abs=1e-15)
    for a, b in ((R, T), (T, N), (R, N)):
        assert sum(x * y for x, y in zip(a, b)) == pytest.approx(0.0, rel=0, abs=1e-15)
    cross = [R[1] * T[2] - R[2] * T[1], R[2] * T[0] - R[0] * T[2], R[0] * T[1] - R[1] * T[0]]
    assert cross == pytest.approx(N, rel=0, abs=1e-15)


@pytest.mark.parametrize("r, v", [
    ((0.0, 0.0, 0.0), (0.0, 7.5, 0.0)),                 # no position
    ((7000.0, 0.0, 0.0), (0.0, 0.0, 0.0)),              # no velocity: no orbit plane
    ((7000.0, 0.0, 0.0), (7.5, 0.0, 0.0)),              # radial velocity: no orbit plane
    ((7000.0, 0.0, 0.0), (-1.0, 0.0, 0.0)),
    ((1.0, 2.0, 3.0), (2.0, 4.0, 6.0)),
    ((float("nan"), 0.0, 0.0), (0.0, 7.5, 0.0)),
    ((7000.0, 0.0, 0.0), (0.0, float("inf"), 0.0)),
])
def test_rtn_axes_refuses_a_state_without_a_frame(r, v):
    with pytest.raises(ValueError, match="RTN frame is undefined"):
        sc.rtn_axes(r, v)


def test_rtn_axes_do_not_depend_on_the_size_of_the_vectors():
    # a threshold on the norm would refuse small but valid vectors
    small = sc.rtn_axes((1e-3, 0.0, 0.0), (0.0, 1e-3, 0.0))
    assert small == ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])
    assert sc.rtn_axes((0.5, 0.0, 0.0), (0.0, 0.5, 0.0)) == small
    assert sc.rtn_axes((7e9, 0.0, 0.0), (0.0, 3e4, 0.0)) == small
