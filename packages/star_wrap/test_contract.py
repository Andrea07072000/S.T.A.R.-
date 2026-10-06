"""Refusals of star_wrap: hostile values, range limits, and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (the threshold test sat exactly on the threshold)."""
import math
from fractions import Fraction

import pytest

import star_wrap as sw

HOSTILE = [
    float("nan"), float("inf"), float("-inf"),
    10 ** 400, -10 ** 400, 1e300, -1e300,
    True, False, "10", None, 1j, [10.0], (10.0,), {"a": 1}
]


def test_pinned_constants_and_api():
    assert sw.__version__ == "0.1.0"
    assert sw.__all__ == ["wrap360", "wrap180", "difference", "circular_mean"]
    assert sw.LIMIT == 1e12
    assert sw.MIN_RESULTANT == 1e-9
    assert sw.MAX_ITEMS == 1_000_000
    assert len(HOSTILE) == 15


@pytest.mark.parametrize("f", [sw.wrap360, sw.wrap180], ids=lambda f: f.__name__)
def test_unary_functions_refuse_hostile_and_accept_numeric_reals(f):
    assert type(f(0.0)) is float
    assert f(Fraction(1, 2)) == f(0.5)
    for bad in HOSTILE:
        with pytest.raises(ValueError):
            f(bad)


def test_difference_refuses_hostile_in_both_arguments():
    assert type(sw.difference(1.0, 2.0)) is float
    for bad in HOSTILE:
        with pytest.raises(ValueError):
            sw.difference(bad, 0.0)
        with pytest.raises(ValueError):
            sw.difference(0.0, bad)


def test_numeric_limit_edges_for_angle_arguments():
    for v in (-1e12, 1e12, -1e12 + 1.0, 1e12 - 1.0):
        assert type(sw.wrap360(v)) is float
        assert type(sw.wrap180(v)) is float
        assert type(sw.difference(v, 0.0)) is float
    for v in (-1.0000001e12, 1.0000001e12):
        with pytest.raises(ValueError):
            sw.wrap360(v)
        with pytest.raises(ValueError):
            sw.wrap180(v)
        with pytest.raises(ValueError):
            sw.difference(v, 0.0)
        with pytest.raises(ValueError):
            sw.difference(0.0, v)


def test_circular_mean_collection_contract_and_hostiles():
    with pytest.raises(ValueError):
        sw.circular_mean([])
    with pytest.raises(ValueError):
        sw.circular_mean("10,20")
    with pytest.raises(ValueError):
        sw.circular_mean({10.0, 20.0})
    with pytest.raises(ValueError):
        sw.circular_mean((a for a in [10.0, 20.0]))
    with pytest.raises(ValueError):
        sw.circular_mean({"a": 10.0})
    with pytest.raises(ValueError):
        sw.circular_mean(10.0)

    for bad in HOSTILE:
        with pytest.raises(ValueError):
            sw.circular_mean([bad])


def test_circular_mean_cancellation_refusals_and_min_resultant_threshold():
    with pytest.raises(ValueError):
        sw.circular_mean([0, 180])
    with pytest.raises(ValueError):
        sw.circular_mean([0, 120, 240])
    with pytest.raises(ValueError):
        sw.circular_mean([10, 190])

    # two directions eps short of opposite: mean resultant length = sin(eps / 2); both sides of the threshold
    above, below = math.degrees(4.0 * sw.MIN_RESULTANT), math.degrees(1.0 * sw.MIN_RESULTANT)
    assert sw.circular_mean([0.0, 180.0 - above]) == pytest.approx(90.0, abs=1e-6)
    with pytest.raises(ValueError, match="undefined"):
        sw.circular_mean([0.0, 180.0 - below])


def test_circular_mean_max_items_guard_both_sides():
    ok = [0.0] * sw.MAX_ITEMS
    assert sw.circular_mean(ok) == 0.0
    too_many = [0.0] * (sw.MAX_ITEMS + 1)
    with pytest.raises(ValueError):
        sw.circular_mean(too_many)
