"""Contract/refusals for star_stats: hostile values, range edges, pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_stats as ss

HOSTILE_CONTAINER = ["", (v for v in [1.0]), 1.0, None]
HOSTILE_VALUE = [True, False, "1", None, float("nan"), float("inf"), float("-inf"), 1 + 2j, 1.0000001e150]
HOSTILE_SAMPLE = [1, 0, None, "yes"]
HOSTILE_WEIGHT = [float("nan"), float("inf"), True, "w"]


def test_pinned_constants_and_public_surface():
    assert ss.__all__ == ["mean", "variance", "stdev", "rms", "weighted_mean"]
    assert ss.__version__ == "0.1.0"
    assert ss.BIG == 1e150
    assert ss.MAX_VALUES == 100000


@pytest.mark.parametrize("f,args", [
    (ss.mean, ([1.0],)),
    (ss.variance, ([1.0, 2.0],)),
    (ss.stdev, ([1.0, 2.0],)),
    (ss.rms, ([1.0],)),
])
def test_values_must_be_list_or_tuple(f, args):
    for bad in HOSTILE_CONTAINER:
        with pytest.raises(ValueError, match="must be a list or tuple"):
            f(bad)


def test_values_element_refusals_and_big_edge_acceptance():
    for bad in HOSTILE_VALUE:
        for f in (ss.mean, ss.variance, ss.stdev, ss.rms):
            with pytest.raises(ValueError, match="finite real numbers"):
                f([bad, 1.0] if f in (ss.variance, ss.stdev) else [bad])
    assert ss.mean([1e150, 1e150]) == 1e150


def test_sample_argument_contract():
    for bad in HOSTILE_SAMPLE:
        with pytest.raises(ValueError, match="sample must be True or False"):
            ss.variance([1.0, 2.0], bad)
        with pytest.raises(ValueError, match="sample must be True or False"):
            ss.stdev([1.0, 2.0], bad)


def test_sample_needs_two_values_population_does_not():
    with pytest.raises(ValueError, match="at least 2 values"):
        ss.variance([7.0])
    with pytest.raises(ValueError, match="at least 2 values"):
        ss.stdev([7.0])
    assert ss.variance([7.0], False) == 0.0
    assert ss.stdev([7.0], False) == 0.0


def test_max_values_limits_once():
    with pytest.raises(ValueError, match="list or tuple of 1 to 100000"):
        ss.mean([0.0] * 100001)
    assert ss.mean([0.0] * 100000) == 0.0


def test_weighted_mean_contract_all_guards():
    assert ss.weighted_mean([1.0, 2.0], [1.0, 1.0]) == 1.5
    with pytest.raises(ValueError, match="weights must be a list or tuple"):
        ss.weighted_mean([1.0], 1.0)
    with pytest.raises(ValueError, match="weights must be as many"):
        ss.weighted_mean([1.0, 2.0], [1.0])
    with pytest.raises(ValueError, match="weights must not be negative"):
        ss.weighted_mean([1.0, 2.0], [1.0, -0.0 - 1.0])
    with pytest.raises(ValueError, match="weights must not be all zero"):
        ss.weighted_mean([1.0, 2.0], [0.0, 0.0])
    for bad in HOSTILE_WEIGHT:
        with pytest.raises(ValueError, match="weights must be finite real numbers"):
            ss.weighted_mean([1.0], [bad])


def test_empty_values_refused_everywhere():
    for f in (ss.mean, ss.variance, ss.stdev, ss.rms):
        with pytest.raises(ValueError, match="list or tuple of 1 to 100000"):
            f([])
    with pytest.raises(ValueError, match="list or tuple of 1 to 100000"):
        ss.weighted_mean([], [])
