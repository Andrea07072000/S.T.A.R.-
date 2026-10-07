"""Contract and refusals of star_polyfit: hostile values, limits and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_polyfit as sp

HOSTILE = [True, False, "2", None, 1j, float("nan"), float("inf"), float("-inf"), 1.0000001e100]


def test_pinned_constants_and_exports():
    assert sp.MAX_DEGREE == 10
    assert sp.MAX_POINTS == 10000
    assert sp.BIG == 1e100
    assert sp.__all__ == ["polyfit", "polyval", "residual_sum"]


@pytest.mark.parametrize("degree", [-1, 11, 1.0, "2", None, True, False])
def test_degree_refusals(degree):
    with pytest.raises(ValueError, match="degree must be an integer from 0 to 10"):
        sp.polyfit([0, 1], [0, 1], degree)


def test_degree_limits_accept():
    sp.polyfit([0], [1], 0)
    xs = list(range(11))
    ys = [sum((k + 1) * (x ** k) for k in range(11)) for x in xs]
    assert len(sp.polyfit(xs, ys, 10)) == 11


@pytest.mark.parametrize("bad", ["x", None, {1, 2}, (v for v in [1, 2]), 3])
def test_xs_ys_container_refusals(bad):
    with pytest.raises(ValueError):
        sp.polyfit(bad, [1], 0)
    with pytest.raises(ValueError):
        sp.polyfit([1], bad, 0)
