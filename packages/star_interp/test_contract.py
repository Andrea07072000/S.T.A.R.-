"""Contract/refusals for star_interp with hostile values and range limits.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (one finite-difference bound tighter than FACTS.md allowed)."""

import pytest

import star_interp as si

BAD = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1j, 1e151, -1e151]
NON_SEQ = [(i for i in [0.0, 1.0]), "01", {"a": 1}, {0.0, 1.0}, None, 3.0]


def test_pinned_constants_and_exports():
    assert si.MIN_POINTS == 2
    assert si.MAX_POINTS == 20
    assert si.BIG == 1e150
    assert si.__all__ == ["lagrange", "lagrange_derivative", "lagrange_weights"]


@pytest.mark.parametrize("f", [si.lagrange, si.lagrange_derivative])
def test_every_argument_refuses_hostile_values(f):
    base_xs, base_ys, base_x = [0.0, 1.0], [0.0, 1.0], 0.5
    for bad in BAD:
        with pytest.raises(ValueError):
            f([bad, 1.0], base_ys, base_x)
        with pytest.raises(ValueError):
            f(base_xs, [bad, 1.0], base_x)
        with pytest.raises(ValueError):
            f(base_xs, base_ys, bad)


def test_sequence_type_and_lengths_and_point_count():
    for bad in NON_SEQ:
        with pytest.raises(ValueError):
            si.lagrange(bad, [0.0, 1.0], 0.5)
        with pytest.raises(ValueError):
            si.lagrange([0.0, 1.0], bad, 0.5)
        with pytest.raises(ValueError):
            si.lagrange_derivative(bad, [0.0, 1.0], 0.5)
        with pytest.raises(ValueError):
            si.lagrange_weights(bad)

    with pytest.raises(ValueError):
        si.lagrange([0.0], [0.0], 0.0)
    with pytest.raises(ValueError):
        si.lagrange_weights([0.0])
    with pytest.raises(ValueError):
        si.lagrange(list(range(21)), list(range(21)), 10.0)
    with pytest.raises(ValueError):
        si.lagrange_weights(list(range(21)))
    with pytest.raises(ValueError):
        si.lagrange([0.0, 1.0], [0.0], 0.5)


def test_distinct_nodes_and_extrapolation_edges():
    with pytest.raises(ValueError, match="distinct"):
        si.lagrange([0.0, 0.0], [1.0, 2.0], 0.0)

    xs, ys = [0.0, 1.0, 2.0], [0.0, 1.0, 4.0]
    assert si.lagrange(xs, ys, 0.0) == 0.0
    assert si.lagrange(xs, ys, 2.0) == 4.0
    assert si.lagrange(xs, ys, 1e-12) == pytest.approx(1e-24, abs=1e-20)
    assert si.lagrange(xs, ys, 2.0 - 1e-12) == pytest.approx((2.0 - 1e-12) ** 2, rel=1e-12)
    with pytest.raises(ValueError, match="extrapolation"):
        si.lagrange(xs, ys, -1e-7)
    with pytest.raises(ValueError, match="extrapolation"):
        si.lagrange(xs, ys, 2.0 + 1e-7)


def test_too_close_nodes_overflow_weights():
    with pytest.raises(ValueError, match="too close"):
        si.lagrange_weights([0.0, 1e-320])
    with pytest.raises(ValueError, match="too close"):
        si.lagrange([0.0, 1e-320], [0.0, 1.0], 0.0)
