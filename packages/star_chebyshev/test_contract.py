"""Contract/refusals for every public argument and both sides of all documented limits in star_chebyshev.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_chebyshev as sc


HOSTILE = [float("nan"), float("inf"), -float("inf"), True, "x", None]


def test_pinned_constants_and_exports():
    assert sc.__all__ == ["evaluate", "evaluate_on"]
    assert sc.__version__ == "0.1.0"
    assert sc.MAX_TERMS == 200
    assert sc.BIG == 1e100
    assert sc.TINY == 1e-100


def test_coefficients_container_refusals_and_limits():
    with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
        sc.evaluate([], 0.0)
    with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
        sc.evaluate([0.0] * 201, 0.0)
    with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
        sc.evaluate("abc", 0.0)
    with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
        sc.evaluate((i for i in [1.0]), 0.0)
    with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
        sc.evaluate(1.0, 0.0)
    with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
        sc.evaluate(None, 0.0)
    assert sc.evaluate([1.0] * 200, 0.0)[0] == 0.0  # accepted max length


@pytest.mark.parametrize("bad", [True, "1", None, float("nan"), float("inf"), 1 + 0j, 1.0000001e100])
def test_each_bad_coefficient_value_is_refused(bad):
    with pytest.raises(ValueError, match="a coefficient"):
        sc.evaluate([bad], 0.0)


def test_coefficient_limits_inside_accepted():
    assert sc.evaluate([1e100], 0.0) == (1e100, 0.0)
    assert sc.evaluate([-1e100], 0.0) == (-1e100, 0.0)


@pytest.mark.parametrize("x", [1.0000001, -1.0000001, float("nan"), float("inf"), True, "x", None])
def test_evaluate_x_refusals(x):
    with pytest.raises(ValueError, match="x"):
        sc.evaluate([1.0], x)


def test_evaluate_x_limits_inside_accepted():
    assert sc.evaluate([0, 1], 1.0) == (1.0, 1.0)
    assert sc.evaluate([0, 1], -1.0) == (-1.0, 1.0)


@pytest.mark.parametrize("r", [0.0, -1.0, 9e-101, 1.1e100, float("nan"), True, "r"])
def test_radius_refusals(r):
    with pytest.raises(ValueError):
        sc.evaluate_on([1.0], 0.0, 0.0, r)


def test_radius_limits_inside_accepted():
    assert sc.evaluate_on([1.0], 0.0, 0.0, 1e-100) == (1.0, 0.0)
    assert sc.evaluate_on([1.0], 0.0, 0.0, 1e100) == (1.0, 0.0)


@pytest.mark.parametrize("mid", [float("nan"), float("inf"), True, 1.1e100])
def test_mid_refusals(mid):
    with pytest.raises(ValueError, match="mid"):
        sc.evaluate_on([1.0], 0.0, mid, 1.0)


@pytest.mark.parametrize("t", [float("nan"), float("inf"), True, None])
def test_t_refusals(t):
    with pytest.raises(ValueError, match="t"):
        sc.evaluate_on([1.0], t, 0.0, 1.0)


def test_t_interval_refusals_and_bounds():
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on([1], 6.1, 0, 6)
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on([1], -6.1, 0, 6)
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on([1], 15.000001, 10, 5)
    assert sc.evaluate_on([1], 6.0, 0, 6) == (1.0, 0.0)
    assert sc.evaluate_on([1], -6.0, 0, 6) == (1.0, 0.0)
