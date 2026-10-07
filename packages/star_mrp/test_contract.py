"""Refusal contract for every public star_mrp function with hostile pinned values and range limits.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_mrp as sm

BAD_COMP = [True, False, "1", None, 1j, float("nan"), float("inf"), float("-inf"), 1e151, -1e151]
BAD_SEQ = [None, 1, 1.0, "x", {}, set(), (1, 2), [1, 2], (1, 2, 3, 4), [1, 2, 3, 4, 5]]


def test_pinned_constants_and_exports():
    assert sm.__version__ == "0.1.0"
    assert sm.BIG == 1e150
    assert sm.__all__ == [
        "mrp_from_quaternion", "quaternion_from_mrp", "shadow", "switch", "compose",
        "dcm_from_mrp", "rotation_vector_from_mrp", "mrp_from_rotation_vector", "mrp_rate"
    ]


@pytest.mark.parametrize("v", BAD_SEQ)
def test_shape_refusals(v):
    for f in (sm.quaternion_from_mrp, sm.shadow, sm.switch, sm.dcm_from_mrp, sm.rotation_vector_from_mrp, sm.mrp_from_rotation_vector):
        with pytest.raises(ValueError):
            f(v)
    for f in (sm.compose,):
        with pytest.raises(ValueError):
            f(v, (0, 0, 0))
        with pytest.raises(ValueError):
            f((0, 0, 0), v)
    for f in (sm.mrp_rate,):
        with pytest.raises(ValueError):
            f(v, (0, 0, 0))
        with pytest.raises(ValueError):
            f((0, 0, 0), v)
    if not (isinstance(v, (list, tuple)) and len(v) == 4):      # four numbers are a quaternion
        with pytest.raises(ValueError):
            sm.mrp_from_quaternion(v)
    if isinstance(v, (list, tuple)) and len(v) == 4:
        with pytest.raises(ValueError):
            sm.mrp_from_quaternion(v[:3])


@pytest.mark.parametrize("bad", BAD_COMP)
def test_component_refusals_all_arguments(bad):
    for i in range(3):
        s = [0.1, -0.2, 0.3]
        s[i] = bad
        for f in (sm.quaternion_from_mrp, sm.shadow, sm.switch, sm.dcm_from_mrp, sm.rotation_vector_from_mrp, sm.mrp_from_rotation_vector):
            with pytest.raises(ValueError):
                f(tuple(s))
        with pytest.raises(ValueError):
            sm.compose(tuple(s), (0.1, 0.2, 0.3))
        with pytest.raises(ValueError):
            sm.compose((0.1, 0.2, 0.3), tuple(s))
        with pytest.raises(ValueError):
            sm.mrp_rate(tuple(s), (0.1, 0.2, 0.3))
        with pytest.raises(ValueError):
            sm.mrp_rate((0.1, 0.2, 0.3), tuple(s))

    for i in range(4):
        q = [1.0, 0.1, -0.2, 0.3]
        q[i] = bad
        with pytest.raises(ValueError):
            sm.mrp_from_quaternion(tuple(q))


def test_special_refusals_and_threshold_limits():
    with pytest.raises(ValueError, match="zero quaternion"):
        sm.mrp_from_quaternion((0, 0, 0, 0))
    with pytest.raises(ValueError, match="no shadow set"):
        sm.shadow((0, 0, 0))

    for t in (0, -1.0, float("nan"), True, False):
        with pytest.raises(ValueError, match="threshold"):
            sm.switch((0.1, 0.2, 0.3), t)

    assert sm.switch((1.0, 0.0, 0.0), 1.0) == (1.0, 0.0, 0.0)
    assert sm.switch((1.000000000001, 0.0, 0.0), 1.0) == pytest.approx((-0.9999999999989999, 0.0, 0.0), rel=0, abs=0)
    assert sm.switch((0.999999999999, 0.0, 0.0), 1.0) == (0.999999999999, 0.0, 0.0)
