"""Refusals/limits contract for every public function and every argument in star_linefit.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_linefit as sl


HOSTILE = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1j, 1.0000001e100, -1.0000001e100]
GOOD_XS = [0.0, 1.0, 2.0]
GOOD_YS = [1.0, 3.0, 5.0]


def test_pinned_constants_and_exports():
    assert sl.BIG == 1e100
    assert sl.MAX_POINTS == 100000
    assert sl.__all__ == ["fit", "fit_errors", "correlation"]


@pytest.mark.parametrize("f", [sl.fit, sl.fit_errors, sl.correlation], ids=lambda f: f.__name__)
def test_xs_ys_must_be_list_or_tuple_and_min_len(f):
    with pytest.raises(ValueError, match="xs must be a list or tuple"):
        f("12", GOOD_YS)
    with pytest.raises(ValueError, match="xs must be a list or tuple"):
        f((x for x in GOOD_XS), GOOD_YS)
    with pytest.raises(ValueError, match="xs must be a list or tuple"):
        f(None, GOOD_YS)
    with pytest.raises(ValueError, match="ys must be a list or tuple"):
        f(GOOD_XS, "12")
    with pytest.raises(ValueError, match="ys must be a list or tuple"):
        f(GOOD_XS, (y for y in GOOD_YS))
    with pytest.raises(ValueError, match="ys must be a list or tuple"):
        f(GOOD_XS, None)
    with pytest.raises(ValueError):
        f([1.0], [2.0])


@pytest.mark.parametrize("f", [sl.fit, sl.fit_errors, sl.correlation], ids=lambda f: f.__name__)
def test_every_argument_refuses_hostile_elements(f):
    for bad in HOSTILE:
        with pytest.raises(ValueError, match="xs must be finite real numbers"):
            f([0.0, bad], [1.0, 2.0])
        with pytest.raises(ValueError, match="ys must be finite"):
            f([0.0, 1.0], [2.0, bad])


def test_range_edges_big_inside_and_outside():
    assert sl.fit([0.0, 1e100], [0.0, 1e100]) == (1.0, 0.0)
    with pytest.raises(ValueError):
        sl.fit([0.0, 1.0000001e100], [0.0, 1.0])


def test_length_mismatch_and_all_x_equal_and_all_y_equal_branches():
    with pytest.raises(ValueError, match="same length"):
        sl.fit([1, 2, 3], [1, 2])
    with pytest.raises(ValueError, match="all the x are equal"):
        sl.fit([1, 1], [1, 2])
    with pytest.raises(ValueError, match="all the x are equal"):
        sl.fit([3, 3, 3], [1, 2, 3])
    assert sl.fit([1, 2, 3], [5, 5, 5]) == (0.0, 5.0)
    assert sl.fit_errors([1, 2, 3], [5, 5, 5]) == (0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="all the y are equal"):
        sl.correlation([1, 2, 3], [5, 5, 5])


def test_two_points_branch_fit_errors_refusal_but_fit_and_correlation_accept():
    assert sl.fit([0, 1], [5, 3]) == (-2.0, 5.0)
    assert sl.correlation([0, 1], [5, 3]) == -1.0
    with pytest.raises(ValueError, match="at least 3 points"):
        sl.fit_errors([0, 1], [5, 3])


def test_too_large_result_for_float_branch():
    with pytest.raises(ValueError, match="too large for a float"):
        sl.fit([0.0, 5e-324], [1e100, -1e100])


def test_max_points_limit_once():
    xs = [float(i) for i in range(sl.MAX_POINTS + 1)]
    ys = [float(2 * i + 1) for i in range(sl.MAX_POINTS + 1)]
    with pytest.raises(ValueError, match="list or tuple of 2 to 100000"):
        sl.fit(xs, ys)
