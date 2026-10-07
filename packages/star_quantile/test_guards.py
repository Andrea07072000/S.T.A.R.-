"""Guard tests of star_quantile written by the reviewer: the definition written out in exact fractions in another
form (position split by divmod), every branch at its boundary, and the limits at their exact values."""
import math
from fractions import Fraction as F

import pytest

import star_quantile as sq


def type7(values, q):
    """Hyndman-Fan definition 7 on exact fractions: position (n - 1) q split into whole part and remainder."""
    xs = sorted(F(v) for v in values)
    whole, part = divmod((len(xs) - 1) * F(q), 1)
    return xs[int(whole)] if part == 0 else xs[int(whole)] * (1 - part) + xs[int(whole) + 1] * part


DATASETS = [[3.0, 1.0, 2.0], [4.0, 1.0, 3.0, 2.0], [0.1, 0.7, 0.3, 0.9, 0.2, 0.6], [1e9 + 0.25, 1e9 + 0.5, 1e9, 1e9 + 3.0, 1e9 - 7.0], [5.0], [2.0, 2.0, 2.0, 2.0],
            [-1e150, 1e150, 0.0, 1.0], [5e-324, 1e-323, 0.0], [1.0, 2.0, 3.0, 4.0, 1e12], [float((k * 37) % 23 - 11) for k in range(47)], [-3.5, -1.25, -0.5, -8.0]]
QS = [0.0, 1.0, 0.5, 0.25, 0.75, 0.1, 0.9, 1.0 / 3.0, 0.999, 1e-300, math.nextafter(1.0, 0.0), 5e-324]


@pytest.mark.parametrize("values", DATASETS)
def test_every_statistic_is_the_exact_definition_rounded_once(values):
    for q in QS:
        got = sq.quantile(values, q)
        assert got == float(type7(values, q)) and type(got) is float
    med = type7(values, 0.5)
    assert sq.median(values) == float(med) == sq.quantile(values, 0.5)
    assert sq.iqr(values) == float(type7(values, 0.75) - type7(values, 0.25)) and sq.iqr(values) >= 0.0
    assert sq.mad(values) == float(type7([abs(F(v) - med) for v in values], 0.5)) and sq.mad(values) >= 0.0
    shuffled = values[1::2] + values[0::2][::-1]
    for f in (sq.median, sq.iqr, sq.mad, lambda v: sq.quantile(v, 0.3)):
        assert f(shuffled) == f(values) and f(tuple(values)) == f(values)
    assert sq.quantile(values, 0) == min(values) and sq.quantile(values, 1) == max(values)
    steps = [sq.quantile(values, k / 20) for k in range(21)]
    assert steps == sorted(steps)


def test_small_cases_by_hand():
    assert sq.median([3, 1, 2]) == 2.0 and sq.median([4, 1, 3, 2]) == 2.5 and sq.median([5]) == 5.0 and sq.median([1, 9]) == 5.0
    assert sq.quantile([1, 2, 3, 4], 0.25) == 1.75 and sq.quantile([1, 2, 3, 4], 0.75) == 3.25 and sq.quantile([0, 10], 0.1) == 1.0
    assert sq.quantile([1, 2, 3, 4, 5], 0.25) == 2.0 and sq.quantile([1, 2, 3, 4, 5], 0.75) == 4.0 and sq.quantile([1, 2, 3, 4, 5], 0.5) == 3.0
    assert sq.quantile([10, 20, 30], 0.75) == 25.0 and sq.quantile([10, 20, 30], 0.25) == 15.0     # positions 1.5 and 0.5
    assert sq.quantile([10, 20, 40], 0.75) == 30.0 and sq.quantile([10, 20, 40], 0.25) == 15.0     # the upper gap is 20 wide, the lower 10
    assert sq.iqr([1, 2, 3, 4]) == 1.5 and sq.iqr([1, 2, 3, 4, 5]) == 2.0 and sq.iqr([1, 1, 2, 2, 4, 6, 9]) == 3.5 and sq.iqr([10, 20, 40]) == 15.0
    assert sq.mad([1, 1, 2, 2, 4, 6, 9]) == 1.0 and sq.mad([1, 2, 3, 4, 5]) == 1.0 and sq.mad([1, 2, 3, 4, 100]) == 1.0 and sq.mad([0, 10]) == 5.0
    assert sq.mad([0, 1, 5]) == 1.0 and sq.mad([0, 4, 5]) == 1.0 and sq.mad([0, 1, 2, 10]) == 1.0   # deviations 1, 0, 4; 4, 0, 1; 1.5, 0.5, 0.5, 8.5
    assert sq.mad([5]) == 0.0 and sq.iqr([5]) == 0.0 and sq.mad([7, 7, 7]) == 0.0 and sq.iqr([7, 7, 7]) == 0.0
    assert sq.iqr([0.1, 0.2, 0.4, 0.7]) == float(F(0.4) * F(3, 4) + F(0.7) * F(1, 4) - F(0.1) * F(1, 4) - F(0.2) * F(3, 4))   # one rounding, not two


def test_the_last_position_is_reached_only_at_q_equal_to_one():
    values = [1.0, 2.0, 4.0, 8.0]
    assert sq.quantile(values, 1.0) == 8.0 and sq.quantile(values, 1) == 8.0
    below = math.nextafter(1.0, 0.0)
    assert sq.quantile(values, below) == float(F(4) + (3 * F(below) - 2) * 4) and sq.quantile(values, below) < 8.0
    assert sq.quantile(values, 2.0 / 3.0) == float(type7(values, 2.0 / 3.0)) and 3.9 < sq.quantile(values, 2.0 / 3.0) <= 4.0   # just below the third value
    assert sq.quantile([1.0, 2.0], 5e-324) == 1.0 and sq.quantile([1.0, 1e150], 5e-324) == float(1 + F(5e-324) * (F(1e150) - 1))
    assert sq.quantile([3.0], 0.0) == 3.0 and sq.quantile([3.0], 1.0) == 3.0 and sq.quantile([3.0], 0.5) == 3.0


def test_refusals_and_limits():
    assert sq.BIG == 1e150 and sq.MAX_VALUES == 100000
    assert sq.median([1e150, -1e150]) == 0.0 and sq.iqr([1e150, -1e150]) == 1e150 and sq.mad([1e150, -1e150]) == 1e150
    over = math.nextafter(1e150, math.inf)
    for f in (sq.median, sq.iqr, sq.mad, lambda v: sq.quantile(v, 0.5)):
        for bad in ([], "12", None, 5, iter([1.0])):
            with pytest.raises(ValueError, match="values must be a list or tuple"):
                f(bad)
        for bad in (True, "1", None, float("nan"), float("inf"), -float("inf"), 1j, over, -over, 10 ** 400):
            with pytest.raises(ValueError, match="values must be finite"):
                f([1.0, bad])
        assert isinstance(f([1e150]), float) and isinstance(f([-1e150, 1.0]), float)
    for bad in (-0.1, -5e-324, math.nextafter(1.0, 2.0), 2, -1, float("nan"), float("inf"), True, False, "0.5", None, 1j, 10 ** 400):
        with pytest.raises(ValueError, match="q must be a finite real number from 0 to 1"):
            sq.quantile([1.0, 2.0], bad)
    with pytest.raises(ValueError, match="values must be a list or tuple"):
        sq.quantile([], 2.0)                                 # the data are checked first
    assert sq.quantile([1.0, 2.0], 0) == 1.0 and sq.quantile([1.0, 2.0], F(1, 2)) == 1.5      # an int and a Fraction are real numbers
