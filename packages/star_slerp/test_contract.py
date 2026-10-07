"""Contract/refusal tests for star_slerp, including hostile pinned values and range limits.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_slerp as ss


BAD = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1j]


def test_pinned_constants_and_exports():
    assert ss.__all__ == ["slerp", "interpolate"]
    assert ss.__version__ == "0.1.0"
    assert ss.UNIT_TOLERANCE == 1e-9
    assert ss.SMALL_ANGLE == 1e-8
    assert ss.BIG_TIME == 1e15
    assert ss.MAX_ROWS == 100000


@pytest.mark.parametrize("bad_q", [(1, 0, 0), "q", None])
def test_quaternion_container_refusals(bad_q):
    with pytest.raises(ValueError, match="must be a list or tuple of 4 numbers"):
        ss.slerp(bad_q, (1.0, 0.0, 0.0, 0.0), 0.5)
    with pytest.raises(ValueError, match="must be a list or tuple of 4 numbers"):
        ss.slerp((1.0, 0.0, 0.0, 0.0), bad_q, 0.5)


@pytest.mark.parametrize("bad_c", BAD)
def test_quaternion_component_refusals(bad_c):
    q = [1.0, 0.0, 0.0, 0.0]
    q[1] = bad_c
    with pytest.raises(ValueError, match="a component of"):
        ss.slerp(q, (1.0, 0.0, 0.0, 0.0), 0.5)


@pytest.mark.parametrize("q", [(1.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0), (1.0 + 1e-8, 0.0, 0.0, 0.0)])
def test_non_unit_quaternions_refused(q):
    with pytest.raises(ValueError, match="unit length"):
        ss.slerp(q, (1.0, 0.0, 0.0, 0.0), 0.5)


def test_unit_tolerance_limits():
    assert ss.slerp((1.0 + 1e-10, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), 0.0) == (1.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="unit length"):
        ss.slerp((1.0 + 1.1e-9, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), 0.0)


@pytest.mark.parametrize("bad_t", [-0.1, 1.0000001, float("nan"), float("inf"), True, "0.5", None])
def test_slerp_t_refusals(bad_t):
    with pytest.raises(ValueError, match="t must be a finite real number from 0 to 1"):
        ss.slerp((1.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), bad_t)


def test_slerp_t_limits_accepted():
    q = (1.0, 0.0, 0.0, 0.0)
    assert ss.slerp(q, q, 0) == q
    assert ss.slerp(q, q, 1) == q


def test_interpolate_times_contract():
    with pytest.raises(ValueError, match="times must be a list or tuple"):
        ss.interpolate("not-a-seq", [(1.0, 0.0, 0.0, 0.0)] * 2, 0.0)
    with pytest.raises(ValueError, match="times must be a list or tuple"):
        ss.interpolate([0.0], [(1.0, 0.0, 0.0, 0.0)], 0.0)

    for bad in [float("nan"), float("inf"), True, ss.BIG_TIME + 1.0]:
        with pytest.raises(ValueError, match="a time"):
            ss.interpolate([0.0, bad], [(1.0, 0.0, 0.0, 0.0)] * 2, 0.0)

    with pytest.raises(ValueError, match="strictly increasing"):
        ss.interpolate([0.0, 0.0], [(1.0, 0.0, 0.0, 0.0)] * 2, 0.0)
    with pytest.raises(ValueError, match="strictly increasing"):
        ss.interpolate([1.0, 0.0], [(1.0, 0.0, 0.0, 0.0)] * 2, 0.0)

    assert ss.interpolate([-ss.BIG_TIME, ss.BIG_TIME], [(1.0, 0.0, 0.0, 0.0)] * 2, 0.0) == (1.0, 0.0, 0.0, 0.0)


def test_interpolate_quaternion_table_contract_and_t_range():
    times = [0.0, 1.0]
    with pytest.raises(ValueError, match="one quaternion for each time"):
        ss.interpolate(times, "not-a-table", 0.5)
    with pytest.raises(ValueError, match="one quaternion for each time"):
        ss.interpolate(times, [(1.0, 0.0, 0.0, 0.0)], 0.5)
    with pytest.raises(ValueError, match="a quaternion of the table"):
        ss.interpolate(times, [(1.0, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 0.0)], 0.5)

    with pytest.raises(ValueError, match="t must be a finite real number from"):
        ss.interpolate(times, [(1.0, 0.0, 0.0, 0.0)] * 2, -1e-12)
    with pytest.raises(ValueError, match="t must be a finite real number from"):
        ss.interpolate(times, [(1.0, 0.0, 0.0, 0.0)] * 2, 1.0 + 1e-12)

    assert ss.interpolate(times, [(1.0, 0.0, 0.0, 0.0)] * 2, 0.0) == (1.0, 0.0, 0.0, 0.0)
    assert ss.interpolate(times, [(1.0, 0.0, 0.0, 0.0)] * 2, 1.0) == (1.0, 0.0, 0.0, 0.0)
