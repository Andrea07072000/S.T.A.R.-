"""star_tabint contract/refusals: hostile values on every argument, range edges in/out, pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_tabint as st

HOSTILE = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1 + 2j, 1e101, -1e101]


def test_pinned_public_surface_and_constants():
    assert st.__all__ == ["trapezoid", "cumulative", "simpson"]
    assert st.__version__ == "0.1.0"
    assert st.BIG == 1e100 and st.TINY == 1e-100 and st.MAX_POINTS == 100000


@pytest.mark.parametrize("bad", ["abc", (i for i in [0, 1]), None])
def test_xs_ys_must_be_list_or_tuple(bad):
    with pytest.raises(ValueError, match="xs must be a list or tuple"):
        st.trapezoid(bad, [0, 1])
    with pytest.raises(ValueError, match="ys must be a list or tuple"):
        st.trapezoid([0, 1], bad)
    with pytest.raises(ValueError, match="xs must be a list or tuple"):
        st.cumulative(bad, [0, 1])
    with pytest.raises(ValueError, match="ys must be a list or tuple"):
        st.cumulative([0, 1], bad)
    with pytest.raises(ValueError, match="ys must be a list or tuple"):
        st.simpson(bad, 1.0)


@pytest.mark.parametrize("fn", [st.trapezoid, st.cumulative])
def test_table_size_limits(fn):
    with pytest.raises(ValueError):
        fn([0], [0])
    n = st.MAX_POINTS + 1
    xs = list(range(n))
    ys = [1.0] * n
    with pytest.raises(ValueError):
        fn(xs, ys)


def test_simpson_minimum_and_odd_count_guards():
    with pytest.raises(ValueError, match="odd number of values"):
        st.simpson([1, 1], 1.0)
    with pytest.raises(ValueError, match="odd number of values"):
        st.simpson([1, 1, 1, 1], 1.0)


@pytest.mark.parametrize("bad", HOSTILE)
def test_hostile_values_refused_in_xs_and_ys_for_table_functions(bad):
    with pytest.raises(ValueError, match="xs must be finite real numbers"):
        st.trapezoid([0, bad], [0, 1])
    with pytest.raises(ValueError, match="ys must be finite real numbers"):
        st.trapezoid([0, 1], [0, bad])
    with pytest.raises(ValueError, match="xs must be finite real numbers"):
        st.cumulative([0, bad], [0, 1])
    with pytest.raises(ValueError, match="ys must be finite real numbers"):
        st.cumulative([0, 1], [0, bad])


@pytest.mark.parametrize("bad", HOSTILE)
def test_hostile_values_refused_in_simpson_ys_and_step(bad):
    with pytest.raises(ValueError, match="ys must be finite real numbers"):
        st.simpson([1, bad, 1], 1.0)
    with pytest.raises(ValueError, match="step must be"):
        st.simpson([1, 1, 1], bad)


def test_length_mismatch_and_monotonicity_guards():
    with pytest.raises(ValueError, match="same length"):
        st.trapezoid([0, 1, 2], [0, 1])
    with pytest.raises(ValueError, match="same length"):
        st.cumulative([0, 1, 2], [0, 1])
    with pytest.raises(ValueError, match="strictly increasing"):
        st.trapezoid([0, 0, 1], [1, 2, 3])   # equal neighbours
    with pytest.raises(ValueError, match="strictly increasing"):
        st.trapezoid([1, 0], [1, 1])         # decreasing
    with pytest.raises(ValueError, match="strictly increasing"):
        st.cumulative([0, 0, 1], [1, 2, 3])


def test_step_edges_inside_and_outside():
    assert st.simpson([1, 1, 1], 1e-100) == 2e-100
    assert st.simpson([1, 1, 1], 1e100) == 2e100
    with pytest.raises(ValueError, match="step must be"):
        st.simpson([1, 1, 1], 9e-101)
    with pytest.raises(ValueError, match="step must be"):
        st.simpson([1, 1, 1], 1.1e100)
    with pytest.raises(ValueError, match="step must be"):
        st.simpson([1, 1, 1], 0.0)
    with pytest.raises(ValueError, match="step must be"):
        st.simpson([1, 1, 1], -1.0)
