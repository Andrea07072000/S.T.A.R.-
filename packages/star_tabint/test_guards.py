"""Guard tests of star_tabint written by the reviewer: each rule against the same rule written out in exact
fractions in another form (prefix by prefix, pair by pair), and every limit at its exact value."""
import math
from fractions import Fraction as F

import pytest

import star_tabint as ti

TABLES = [([0.0, 1.0, 2.0], [0.0, 1.0, 4.0]), ([0.0, 0.5, 2.0], [4.0, 0.0, 2.0]), ([-3.0, -1.5, 0.25, 7.0, 7.5], [0.1, -0.2, 0.3, -0.4, 0.5]),
          ([0.0, 1.0, 2.0, 3.0], [1e16, 1.0, -1e16, 1.0]), ([1e9, 1e9 + 0.25, 1e9 + 3.0], [1e-9, 2e-9, -5e-9]), ([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], [0.7, 0.1, 0.9, 0.3, 0.2, 0.8, 0.4]),
          ([-1e100, 0.0, 1e100], [1e100, -1e100, 1e100]), ([5e-324, 1e-323, 1.0], [1.0, 2.0, 3.0]), ([float(k * k) for k in range(25)], [float((k * 37) % 11 - 5) for k in range(25)])]


def area(xs, ys, upto):
    """The trapezoid rule up to index `upto`, from the definition, in exact fractions."""
    return sum((F(xs[k + 1]) - F(xs[k])) * (F(ys[k]) + F(ys[k + 1])) for k in range(upto)) / 2


@pytest.mark.parametrize("xs,ys", TABLES)
def test_trapezoid_and_every_partial_integral_are_exact_values_rounded_once(xs, ys):
    n = len(xs)
    assert ti.trapezoid(xs, ys) == float(area(xs, ys, n - 1))
    running = ti.cumulative(xs, ys)
    assert type(running) is tuple and len(running) == n and running[0] == 0.0 and math.copysign(1.0, running[0]) == 1.0
    for k in range(n):
        assert running[k] == float(area(xs, ys, k)) and type(running[k]) is float
    assert running[-1] == ti.trapezoid(xs, ys)
    assert ti.trapezoid(tuple(xs), tuple(ys)) == ti.trapezoid(xs, ys) and ti.trapezoid(xs, [-v for v in ys]) == -ti.trapezoid(xs, ys)
    assert ti.trapezoid(xs, [0.5 * v for v in ys]) == float(area(xs, ys, n - 1) / 2)


@pytest.mark.parametrize("ys,step", [([0.0, 1.0, 8.0], 1.0), ([1.0, 0.8, 2.0 / 3.0, 4.0 / 7.0, 0.5], 0.25), ([0.3, -0.1, 0.7, 0.2, -0.9, 0.4, 0.6], 0.1),
                                     ([1e16, 1.0, -1e16], 3.0), ([1e100, -1e100, 1e100, -1e100, 1e100], 1e100), ([5e-324, 5e-324, 5e-324], 1e-100),
                                     ([float(k % 7) for k in range(41)], 1.0 / 3.0)])
def test_simpson_is_the_exact_weighted_sum_rounded_once(ys, step):
    weights = [1] + [4 if k % 2 else 2 for k in range(1, len(ys) - 1)] + [1]
    exact = F(step) * sum(w * F(y) for w, y in zip(weights, ys)) / 3
    assert ti.simpson(ys, step) == float(exact) and type(ti.simpson(ys, step)) is float
    assert ti.simpson(tuple(ys), step) == float(exact) and ti.simpson(list(reversed(ys)), step) == float(exact)     # the weights are symmetric


def test_small_cases_by_hand():
    assert ti.trapezoid([0, 1], [3, 5]) == 4.0 and ti.trapezoid([0, 2, 3], [1, 1, 1]) == 3.0 and ti.trapezoid([1, 2, 4, 8], [2, 4, 8, 16]) == 63.0
    assert ti.trapezoid([-1, 0, 1], [-1, 0, 1]) == 0.0 and math.copysign(1.0, ti.trapezoid([-1, 0, 1], [-1, 0, 1])) == 1.0
    assert ti.trapezoid([0, 1, 2], [1e16, 1.0, -1e16]) == 1.0 and ti.cumulative([0, 1, 3], [0, 2, 2]) == (0.0, 1.0, 5.0)
    assert ti.cumulative([0, 1], [3, 5]) == (0.0, 4.0) and ti.cumulative([2, 3, 5, 6], [1, 1, 1, 1]) == (0.0, 1.0, 3.0, 4.0)
    assert ti.simpson([0, 1, 0, 0, 0], 3) == 4.0 and ti.simpson([0, 0, 1, 0, 0], 3) == 2.0 and ti.simpson([0, 0, 0, 1, 0], 3) == 4.0
    assert ti.simpson([1, 0, 0, 0, 0], 3) == 1.0 and ti.simpson([0, 0, 0, 0, 1], 3) == 1.0 and ti.simpson([0, 1, 0], 3) == 4.0
    assert ti.simpson([1, 3, 5], 1) == 6.0 and ti.simpson([0, 1, 8], 1) == 4.0 and ti.simpson([0, 1, 8], 2) == 8.0 and ti.simpson([0, 1, 8], 0.5) == 2.0
    assert ti.simpson([0, 0, 0, 0, 0, 1, 0], 3) == 4.0 and ti.simpson([0, 0, 0, 0, 1, 0, 0], 3) == 2.0       # the pattern 4, 2 continues


def test_tables_refused():
    for f in (ti.trapezoid, ti.cumulative):
        for xs in ([0.0, 0.0, 1.0], [1.0, 0.0], [0.0, 1.0, 1.0], [0.0, 2.0, 1.0], [0.0, math.nextafter(0.0, -1.0)], [-0.0, 0.0]):
            with pytest.raises(ValueError, match="strictly increasing"):
                f(xs, [1.0] * len(xs))
        assert f([0.0, 5e-324], [1.0, 1.0]) is not None and f([-5e-324, 0.0, 5e-324], [1.0, 1.0, 1.0]) is not None      # neighbouring floats are increasing
        with pytest.raises(ValueError, match="same length"):
            f([0.0, 1.0, 2.0], [1.0, 2.0])
        with pytest.raises(ValueError, match="same length"):
            f([0.0, 1.0], [1.0, 2.0, 3.0])
        for bad in ([1.0], [], "12", None, iter([1.0, 2.0])):
            with pytest.raises(ValueError, match="xs must be a list or tuple"):
                f(bad, [1.0, 2.0])
            with pytest.raises(ValueError, match="ys must be a list or tuple"):
                f([1.0, 2.0], bad)
        for bad in (True, "1", None, float("nan"), float("inf"), -float("inf"), 1j, math.nextafter(1e100, math.inf), -math.nextafter(1e100, math.inf), 10 ** 400):
            with pytest.raises(ValueError, match="xs must be finite"):
                f([0.0, bad], [1.0, 2.0])
            with pytest.raises(ValueError, match="ys must be finite"):
                f([0.0, 1.0], [1.0, bad])
    assert ti.BIG == 1e100 and ti.TINY == 1e-100 and ti.MAX_POINTS == 100000
    assert ti.trapezoid([-1e100, 1e100], [1e100, 1e100]) == 2e200 and ti.trapezoid([-1e100, 1e100], [-1e100, -1e100]) == -2e200


def test_simpson_refused():
    for ys in ([1.0, 2.0], [1.0, 2.0, 3.0, 4.0], [0.0] * 6):
        with pytest.raises(ValueError, match="odd number of values"):
            ti.simpson(ys, 1.0)
    for bad in ([1.0], [], "123", None):
        with pytest.raises(ValueError, match="ys must be a list or tuple"):
            ti.simpson(bad, 1.0)
    with pytest.raises(ValueError, match="ys must be finite"):
        ti.simpson([1.0, float("nan"), 3.0], 1.0)
    for bad in (0, 0.0, -1.0, math.nextafter(1e-100, 0.0), math.nextafter(1e100, math.inf), float("nan"), float("inf"), True, "1", None, 1j, 10 ** 400):
        with pytest.raises(ValueError, match="step must be"):
            ti.simpson([1.0, 2.0, 3.0], bad)
    assert ti.simpson([1, 1, 1], 1e-100) == 2e-100 and ti.simpson([1, 1, 1], 1e100) == 2e100 and ti.simpson([1, 1, 1], 2) == 4.0
