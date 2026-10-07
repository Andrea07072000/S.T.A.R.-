"""Refusals and limits for every public function argument in star_quantile.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_quantile as sq

HOSTILE_VALUES = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1 + 2j, 1.0000001e150]


def test_pinned_constants_and_exports():
    assert sq.BIG == 1e150
    assert sq.MAX_VALUES == 100000
    assert sq.__all__ == ["median", "quantile", "iqr", "mad"]


@pytest.mark.parametrize("bad_values", [[], "123", (x for x in [1, 2]), 5, None])
def test_values_container_refusals_all_public_functions(bad_values):
    for f in (sq.median, sq.iqr, sq.mad):
        with pytest.raises(ValueError):
            f(bad_values)
    with pytest.raises(ValueError):
        sq.quantile(bad_values, 0.5)


@pytest.mark.parametrize("bad_item", HOSTILE_VALUES)
def test_values_items_refused_all_public_functions(bad_item):
    vals = [1.0, bad_item, 2.0]
    for f in (sq.median, sq.iqr, sq.mad):
        with pytest.raises(ValueError):
            f(vals)
    with pytest.raises(ValueError):
        sq.quantile(vals, 0.5)


def test_values_limits_inside_and_outside():
    ok = [1.0, -1.0, 1e150, -1e150]
    for f in (sq.median, sq.iqr, sq.mad):
        assert isinstance(f(ok), float)
    assert isinstance(sq.quantile(ok, 0.5), float)

    for bad in ([1.0000001e150], [-1.0000001e150]):
        for f in (sq.median, sq.iqr, sq.mad):
            with pytest.raises(ValueError):
                f(bad)
        with pytest.raises(ValueError):
            sq.quantile(bad, 0.5)


def test_max_values_limit_once():
    vals = [0.0] * sq.MAX_VALUES
    assert sq.median(vals) == 0.0
    with pytest.raises(ValueError):
        sq.median(vals + [0.0])


@pytest.mark.parametrize("q", [-0.1, 1.0000001, float("nan"), float("inf"), float("-inf"), True, False, "q", None])
def test_quantile_q_refusals(q):
    with pytest.raises(ValueError):
        sq.quantile([1, 2, 3], q)


def test_quantile_q_limits_accepted_including_ints():
    assert sq.quantile([2, 9, 1], 0) == 1.0
    assert sq.quantile([2, 9, 1], 1) == 9.0
    assert sq.quantile([2, 9, 1], 0.0) == 1.0
    assert sq.quantile([2, 9, 1], 1.0) == 9.0
