"""star_stats against published values, hand-derivable values, inverses and invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math
import itertools


import star_stats as ss


def test_published_nist_numacc1_exact():
    x = [10000001, 10000003, 10000002]
    assert ss.mean(x) == 10000002.0
    assert ss.stdev(x) == 1.0


def test_published_nist_numacc2():
    x = [1.2] + [1.1, 1.3] * 500
    assert ss.mean(x) == 1.2
    assert abs(ss.stdev(x) - 0.1) <= 1e-15


def test_textbook_population_and_sample():
    x = [2, 4, 4, 4, 5, 5, 7, 9]
    assert ss.mean(x) == 5.0
    assert ss.variance(x, False) == 4.0
    assert ss.stdev(x, False) == 2.0
    assert ss.variance(x) == 32.0 / 7.0


def test_hand_values_and_defaults():
    x = [1, 2, 3, 4]
    # mean=(1+2+3+4)/4=2.5 ; sample variance: deviations -1.5,-0.5,0.5,1.5 squares sum=5 then /3
    assert ss.mean(x) == 2.5
    assert ss.variance(x) == 1.6666666666666667
    assert ss.variance(x, True) == ss.variance(x)
    assert ss.variance(x, False) == 1.25
    assert ss.stdev(x, False) == math.sqrt(1.25)
    assert abs(ss.stdev(x) - math.sqrt(5.0 / 3.0)) <= 2.3e-16


def test_singleton_and_rms():
    assert ss.mean([7]) == 7.0
    assert ss.variance([7], False) == 0.0
    assert ss.stdev([7], False) == 0.0
    assert ss.rms([-5]) == 5.0


def test_no_cancellation_and_equal_values():
    x = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    # mean=1e9+10; deviations -6,-3,3,6 => squares sum=90; sample var=90/3=30 ; population=90/4=22.5
    assert ss.variance(x) == 30.0
    assert ss.variance(x, False) == 22.5
    assert ss.variance([0.1] * 7) == 0.0
    assert ss.mean([1e16, 1, -1e16]) == 0.3333333333333333
    assert ss.mean([0.1, 0.2, 0.3]) == 0.2


def test_order_independence_all_functions():
    x = [3.5, -2.0, 7.25, 1.125]
    w = [1.0, 4.0, 2.0, 3.0]
    base = (ss.mean(x), ss.variance(x), ss.variance(x, False), ss.stdev(x), ss.rms(x), ss.weighted_mean(x, w))
    for p in itertools.permutations(range(4)):
        xp = [x[i] for i in p]
        wp = [w[i] for i in p]
        got = (ss.mean(xp), ss.variance(xp), ss.variance(xp, False), ss.stdev(xp), ss.rms(xp), ss.weighted_mean(xp, wp))
        assert got == base


def test_rms_edge_magnitudes():
    assert ss.rms([3, 4]) == math.sqrt(12.5)
    assert ss.rms([1, -1, 1, -1]) == 1.0
    assert ss.rms([0, 0]) == 0.0
    assert ss.rms([5e-324]) == 5e-324
    assert ss.rms([1e150] * 3) == 1e150
    assert ss.stdev([5e-324, 0.0]) == 5e-324


def test_relations():
    x = [0.75, -1.25, 2.5, 4.0, -0.5]
    for sample in (True, False):
        v = ss.variance(x, sample)
        s = ss.stdev(x, sample)
        assert abs(s * s - v) <= 4e-16 * max(1.0, abs(v))
    # rms^2 = population variance + mean^2
    lhs = ss.rms(x) ** 2
    rhs = ss.variance(x, False) + ss.mean(x) ** 2
    assert abs(lhs - rhs) <= 1e-12
    n = len(x)
    assert abs(ss.variance(x) * (n - 1) - ss.variance(x, False) * n) <= 4e-16 * max(1.0, abs(ss.variance(x) * (n - 1)))


def test_translation_invariance_and_weighted_mean_properties():
    x = [1, 2, 4, 7]
    assert ss.variance([v + 10 for v in x]) == ss.variance(x)
    assert ss.weighted_mean([10, 20], [1, 3]) == 17.5
    assert ss.weighted_mean([10, 20], [0, 3]) == 20.0
    assert ss.weighted_mean([1, 2, 3], [1, 1, 2]) == 2.25
    eqw = [2.5] * len(x)
    assert ss.weighted_mean(x, eqw) == ss.mean(x)
    assert ss.weighted_mean([10, 20], [1, 3]) == ss.weighted_mean([10, 20], [8, 24])


def test_plus_zero_sign_and_tuple_list_equivalence():
    for r in (ss.mean([-0.0, 0.0]), ss.mean([-0.0]), ss.weighted_mean([-0.0], [2])):
        assert math.copysign(1.0, r) == 1.0
    x_list = [1, 2, 3]
    x_tup = (1, 2, 3)
    assert ss.mean(x_list) == ss.mean(x_tup)
    assert ss.variance(x_list) == ss.variance(x_tup)
    assert ss.stdev(x_list) == ss.stdev(x_tup)
    assert ss.rms(x_list) == ss.rms(x_tup)
