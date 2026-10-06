"""Refusals and range limits for all public star_poly functions, with pinned constants and hostile values.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_poly as sp

HOSTILE = [True, False, "1", None, float("nan"), float("inf"), float("-inf"), 1j, 1.0000001e60, -1.0000001e60]


def test_pinned_constants_and_exports():
    assert sp.BIG == 1e60
    assert sp.MAX_COEFFICIENTS == 30
    assert sp.__all__ == ["quadratic_roots", "cubic_roots", "evaluate"]


@pytest.mark.parametrize("bad", HOSTILE)
def test_quadratic_refuses_hostile_each_argument(bad):
    with pytest.raises(ValueError):
        sp.quadratic_roots(bad, 1.0, 1.0)
    with pytest.raises(ValueError):
        sp.quadratic_roots(1.0, bad, 1.0)
    with pytest.raises(ValueError):
        sp.quadratic_roots(1.0, 1.0, bad)


@pytest.mark.parametrize("bad", HOSTILE)
def test_cubic_refuses_hostile_each_argument(bad):
    with pytest.raises(ValueError):
        sp.cubic_roots(bad, 1.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        sp.cubic_roots(1.0, bad, 1.0, 1.0)
    with pytest.raises(ValueError):
        sp.cubic_roots(1.0, 1.0, bad, 1.0)
    with pytest.raises(ValueError):
        sp.cubic_roots(1.0, 1.0, 1.0, bad)


def test_leading_zero_refused_in_both_signs():
    with pytest.raises(ValueError, match="must not be zero"):
        sp.quadratic_roots(0.0, 1.0, 1.0)
    with pytest.raises(ValueError, match="must not be zero"):
        sp.quadratic_roots(-0.0, 1.0, 1.0)
    with pytest.raises(ValueError, match="must not be zero"):
        sp.cubic_roots(0.0, 1.0, 1.0, 1.0)
    with pytest.raises(ValueError, match="must not be zero"):
        sp.cubic_roots(-0.0, 1.0, 1.0, 1.0)


def test_limits_just_inside_and_outside_for_numeric_range():
    assert sp.quadratic_roots(1e60, -1e60, 1.0)
    with pytest.raises(ValueError):
        sp.quadratic_roots(1.0000001e60, 0.0, 1.0)
    assert sp.cubic_roots(1.0, -1e60, 1e60, -1.0)
    with pytest.raises(ValueError):
        sp.cubic_roots(1.0, -1.0000001e60, 0.0, 0.0)
    assert sp.evaluate([1e60], -1e60) == (1e60, 0.0)
    with pytest.raises(ValueError):
        sp.evaluate([1.0000001e60], 0.0)
    with pytest.raises(ValueError):
        sp.evaluate([1.0], 1.0000001e60)


@pytest.mark.parametrize("coeffs", ["abc", (c for c in [1.0]), 1.0])
def test_evaluate_refuses_non_list_tuple(coeffs):
    with pytest.raises(ValueError):
        sp.evaluate(coeffs, 0.0)


def test_evaluate_refuses_empty_and_too_many_and_overflow():
    with pytest.raises(ValueError):
        sp.evaluate([], 0.0)
    assert sp.evaluate([1.0] * 30, 1.0)[0] == 30.0
    with pytest.raises(ValueError):
        sp.evaluate([1.0] * 31, 1.0)
    with pytest.raises(ValueError, match="overflows"):
        sp.evaluate([1e60] * 30, 1e60)


@pytest.mark.parametrize("bad", HOSTILE)
def test_evaluate_refuses_hostile_in_coefficients_and_x(bad):
    with pytest.raises(ValueError):
        sp.evaluate([1.0, bad], 0.0)
    with pytest.raises(ValueError):
        sp.evaluate([1.0, 2.0], bad)
