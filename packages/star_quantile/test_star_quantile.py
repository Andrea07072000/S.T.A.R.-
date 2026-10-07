"""star_quantile against published values, hand-derivable values, inverses/invariants and edge cases.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math
import random


import star_quantile as sq


def test_published_quantiles_hyndman_fan_def7():
    vals = [1, 2, 3, 4, 5]
    assert sq.quantile(vals, 0.25) == 2.0
    assert sq.quantile(vals, 0.5) == 3.0
    assert sq.quantile(vals, 0.75) == 4.0


def test_published_mad_worked_example():
    assert sq.mad([1, 1, 2, 2, 4, 6, 9]) == 1.0


def test_median_hand_values_and_exact_half_relation():
    assert sq.median([3, 1, 2]) == 2.0
    assert sq.median([4, 1, 3, 2]) == 2.5  # middle two are 2 and 3 -> (2+3)/2
    assert sq.median([5]) == 5.0
    assert sq.median([1, 2, 3, 4, 100]) == 3.0
    assert sq.median([1e9 + 1, 1e9 + 2]) == 1000000001.5
    assert sq.median([1e150, -1e150]) == 0.0  # mean of +/-1e150
    v = [9, 3, 7, 1, 5, 11]
    assert sq.median(v) == sq.quantile(v, 0.5)


def test_quantile_hand_values_and_endpoints():
    assert sq.quantile([1, 2, 3, 4], 0.25) == 1.75  # h=(4-1)*0.25=0.75 -> 1+0.75*(2-1)
    assert sq.quantile([1, 2, 3, 4], 0.75) == 3.25
    assert sq.quantile([10, 20, 30, 40], 0.5) == 25.0
    assert sq.quantile([0, 10], 0.1) == 1.0
    v = [7, 2, 9, 4]
    assert sq.quantile(v, 0) == float(min(v))
    assert sq.quantile(v, 1) == float(max(v))
    assert sq.quantile([5], 0.0) == 5.0
    assert sq.quantile([5], 0.37) == 5.0
    assert sq.quantile([5], 1.0) == 5.0
    assert sq.quantile([1, 3], 0.5) == 2.0
    assert sq.quantile([0, 1], 0.1) == 0.1


def test_quantile_grid_hits_order_stats_exactly():
    v = [5, 1, 4, 2, 3]
    s = sorted(v)
    assert sq.quantile(v, 0.25) == float(s[1])
    assert sq.quantile(v, 0.5) == float(s[2])
    assert sq.quantile(v, 0.75) == float(s[3])


def test_iqr_hand_values():
    assert sq.iqr([1, 2, 3, 4]) == 1.5      # 3.25 - 1.75
    assert sq.iqr([1, 2, 3, 4, 5]) == 2.0
    assert sq.iqr([1, 1, 2, 2, 4, 6, 9]) == 3.5  # q1=1.5, q3=5
    assert sq.iqr([7, 7, 7]) == 0.0
    assert sq.iqr([5]) == 0.0


def test_mad_hand_values():
    assert sq.mad([1, 2, 3, 4, 5]) == 1.0
    assert sq.mad([1, 2, 3, 4, 100]) == 1.0
    assert sq.mad([5]) == 0.0
    assert sq.mad([7, 7, 7]) == 0.0
    assert sq.mad([0, 10]) == 5.0


def test_permutation_invariance_and_tuple_equals_list():
    vals = [9, 1, 7, 3, 5, 11, -2]
    perm = [3, 11, 1, 9, -2, 7, 5]
    for f in (sq.median, sq.iqr, sq.mad):
        assert f(vals) == f(perm)
        assert f(vals) == f(tuple(vals))
    for q in (0.0, 0.1, 0.5, 1.0):
        assert sq.quantile(vals, q) == sq.quantile(perm, q)
        assert sq.quantile(vals, q) == sq.quantile(tuple(vals), q)


def test_shift_and_scale_invariances():
    v = [1, 4, 9, 16, 25]
    c = 7
    shifted = [x + c for x in v]
    doubled = [2 * x for x in v]
    assert sq.median(shifted) == sq.median(v) + c
    assert sq.quantile(shifted, 0.3) == sq.quantile(v, 0.3) + c
    assert sq.iqr(shifted) == sq.iqr(v)
    assert sq.mad(shifted) == sq.mad(v)
    assert sq.median(doubled) == 2.0 * sq.median(v)
    assert sq.quantile(doubled, 0.3) == 2.0 * sq.quantile(v, 0.3)
    assert sq.iqr(doubled) == 2.0 * sq.iqr(v)
    assert sq.mad(doubled) == 2.0 * sq.mad(v)


def test_nonnegative_spreads_and_quantile_monotone():
    rnd = random.Random(7)
    vals = [rnd.uniform(-100, 100) for _ in range(25)]
    assert sq.iqr(vals) >= 0.0
    assert sq.mad(vals) >= 0.0
    qs = [i / 20 for i in range(21)]
    qvals = [sq.quantile(vals, q) for q in qs]
    assert all(a <= b for a, b in zip(qvals, qvals[1:]))


def test_signed_zero_edge():
    assert sq.median([-0.0, 0.0]) == 0.0
    assert math.copysign(1.0, sq.median([-0.0, 0.0])) == 1.0
