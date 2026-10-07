"""Guard tests of star_stats written by the reviewer: correct rounding of the square root at a rounding boundary,
exact results against rational arithmetic written out here, and the limits at their exact values."""
import math
from fractions import Fraction as F

import pytest

import star_stats as ss


def nearest(x: float, q: F) -> bool:
    """True when x is the float nearest to the non-negative real whose square is q."""
    lo, hi = (F(x) + F(math.nextafter(x, 0.0))) / 2, (F(x) + F(math.nextafter(x, math.inf))) / 2
    return lo * lo <= q <= hi * hi


def test_square_root_of_fractions_is_correctly_rounded():
    assert ss._sqrt(F(0)) == 0.0 and ss._sqrt(F(4)) == 2.0 and ss._sqrt(F(9, 4)) == 1.5 and ss._sqrt(F(1, 4)) == 0.5
    for q in (F(2), F(3), F(1, 3), F(2, 7), F(10) ** 300, F(1, 10 ** 300), F(5e-324), F(5e-324) / 2, F(5e-324) ** 2, F(1e150) ** 2, F(12345678901234567890, 7)):
        got = ss._sqrt(q)
        assert nearest(got, q), q
    assert ss._sqrt(F(5e-324) ** 2) == 5e-324 and ss._sqrt(F(1e150) ** 2) == 1e150
    assert ss._sqrt(F(5e-324) ** 2 / 2) == 5e-324            # 3.5e-324 rounds up to the smallest float
    assert ss._sqrt(F(5e-324) ** 2 / 5) == 0.0               # 2.2e-324 rounds down to zero


@pytest.mark.parametrize("a", [1.0, 1.5, 3.0, 0.7, 1e-200, 1e200, math.nextafter(2.0, 0.0)])
def test_square_root_next_to_a_rounding_boundary(a):
    b = math.nextafter(a, math.inf)
    middle = (F(a) + F(b)) / 2                               # sqrt(q) on one side or the other of the boundary by 1 part in 1e120
    tiny = middle * middle / 10 ** 120
    assert ss._sqrt(middle * middle + tiny) == b
    assert ss._sqrt(middle * middle - tiny) == a
    assert ss._sqrt(middle * middle) in (a, b)               # an exact tie: either neighbour is a nearest float
    assert ss._sqrt(F(a) * F(a)) == a and ss._sqrt(F(b) * F(b)) == b


DATASETS = [[1.0, 2.0, 3.0, 4.0], [0.1, 0.2, 0.3], [1e16, 1.0, -1e16], [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16], [2.5, -7.25, 0.125, 3.0, 3.0, -1e-3],
            [1e150, -1e150, 1e150], [5e-324, 1e-320, 0.0], [3.0, 3.0], [1e-8, 1.0, 1e8, -1e8, 12345.678], [float(k * k % 17) - 8.0 for k in range(40)]]


@pytest.mark.parametrize("xs", DATASETS)
def test_every_statistic_is_the_exact_value_rounded_once(xs):
    fx = [F(x) for x in xs]
    n = len(fx)
    m = sum(fx) / n
    ssq = sum((x - m) ** 2 for x in fx)                      # the two-pass definition, in exact arithmetic
    assert ss.mean(xs) == float(m)
    assert ss.variance(xs) == float(ssq / (n - 1)) and ss.variance(xs, True) == float(ssq / (n - 1))
    assert ss.variance(xs, False) == float(ssq / n)
    assert nearest(ss.stdev(xs), ssq / (n - 1)) and nearest(ss.stdev(xs, True), ssq / (n - 1)) and nearest(ss.stdev(xs, False), ssq / n)
    assert nearest(ss.rms(xs), sum(x * x for x in fx) / n)
    ws = [float(k % 3) + (0.5 if k == 0 else 0.0) for k in range(n)]
    fw = [F(w) for w in ws]
    assert ss.weighted_mean(xs, ws) == float(sum(w * x for w, x in zip(fw, fx)) / sum(fw))
    for f in (ss.mean, ss.variance, ss.stdev, ss.rms):
        assert f(list(reversed(xs))) == f(xs) and f(tuple(sorted(xs))) == f(xs)
    assert ss.weighted_mean(list(reversed(xs)), list(reversed(ws))) == ss.weighted_mean(xs, ws)


def test_sample_and_population_differ_as_n_minus_one_and_n():
    assert ss.variance([1.0, 3.0]) == 2.0 and ss.variance([1.0, 3.0], False) == 1.0          # deviations -1, 1: 2/1 and 2/2
    assert ss.stdev([1.0, 3.0], False) == 1.0 and ss.stdev([0.0, 0.0, 3.0, 3.0], False) == 1.5
    assert ss.variance([0.0, 0.0, 3.0, 3.0]) == 3.0 and ss.stdev([0.0, 0.0, 3.0, 3.0]) == math.sqrt(3.0)
    assert ss.variance([5.0], False) == 0.0 and ss.stdev([5.0], sample=False) == 0.0 and ss.rms([0.0]) == 0.0
    assert ss.variance([1.0, 2.0, 4.0]) == 7 / 3 and ss.variance([1.0, 2.0, 4.0], False) == 14 / 9   # mean 7/3; squares 16/9, 1/9, 25/9
    for bad in ([5.0], (5.0,)):
        with pytest.raises(ValueError, match="at least 2"):
            ss.variance(bad)
        with pytest.raises(ValueError, match="at least 2"):
            ss.stdev(bad, True)
    for bad in (1, 0, None, "True", 1.0):
        with pytest.raises(ValueError, match="sample must be"):
            ss.variance([1.0, 2.0], bad)
        with pytest.raises(ValueError, match="sample must be"):
            ss.stdev([1.0, 2.0], sample=bad)


def test_weights():
    assert ss.weighted_mean([1.0, 5.0], [3.0, 1.0]) == 2.0 and ss.weighted_mean([1.0, 5.0], [1.0, 3.0]) == 4.0
    assert ss.weighted_mean([1.0, 5.0], [0.0, 1e-300]) == 5.0 and ss.weighted_mean([1.0, 5.0], [1e150, 1e150]) == 3.0
    assert ss.weighted_mean([-2.0, 2.0], [1.0, 1.0]) == 0.0 and math.copysign(1.0, ss.weighted_mean([-2.0, 2.0], [1.0, 1.0])) == 1.0
    assert math.copysign(1.0, ss.weighted_mean([-0.0, -0.0], [1.0, 2.0])) == 1.0 and math.copysign(1.0, ss.mean([-0.0, -0.0])) == 1.0
    with pytest.raises(ValueError, match="as many"):
        ss.weighted_mean([1.0, 2.0, 3.0], [1.0, 1.0])
    with pytest.raises(ValueError, match="as many"):
        ss.weighted_mean([1.0], [1.0, 1.0])
    with pytest.raises(ValueError, match="not be negative"):
        ss.weighted_mean([1.0, 2.0], [3.0, -5e-324])
    with pytest.raises(ValueError, match="all zero"):
        ss.weighted_mean([1.0, 2.0], [0.0, -0.0])
    with pytest.raises(ValueError, match="weights must be a list"):
        ss.weighted_mean([1.0, 2.0], "12")
    with pytest.raises(ValueError, match="weights must be a list"):
        ss.weighted_mean([1.0], [])
    with pytest.raises(ValueError, match="weights must be finite"):
        ss.weighted_mean([1.0, 2.0], [1.0, math.nextafter(1e150, math.inf)])
    with pytest.raises(ValueError, match="values must be finite"):
        ss.weighted_mean([1.0, True], [1.0, 1.0])
    with pytest.raises(ValueError, match="weights must be finite"):
        ss.weighted_mean([1.0, 2.0], [1.0, False])


def test_limits_at_their_exact_values():
    assert ss.BIG == 1e150 and ss.MAX_VALUES == 100000
    assert ss.mean([1e150, -1e150]) == 0.0 and ss.rms([1e150, -1e150]) == 1e150 and ss.variance([1e150, -1e150], False) == float(F(1e150) ** 2)
    assert float(F(1e150) ** 2) == 9.999999999999999e+299    # the float 1e150 is slightly below 10^150
    over = math.nextafter(1e150, math.inf)
    for f in (ss.mean, ss.rms, lambda v: ss.variance(v, False), lambda v: ss.stdev(v, False), lambda v: ss.weighted_mean(v, [1.0])):
        with pytest.raises(ValueError, match="values must be finite"):
            f([over])
        with pytest.raises(ValueError, match="values must be finite"):
            f([-over])
        with pytest.raises(ValueError, match="values must be a list"):
            f([])
        assert isinstance(f([1e150]), float) and isinstance(f([-1e150]), float)
    with pytest.raises(ValueError, match="values must be finite"):
        ss.mean([10 ** 400])                                 # an integer too large for a float
    assert ss.mean([10 ** 150, 1]) == 5e149
