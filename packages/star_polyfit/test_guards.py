"""Guard tests of star_polyfit written by the reviewer: an independent oracle (Lagrange interpolation in exact
rationals, and the textbook centred sums for a line), exact invariants, the limits and every refusal by name."""
import random
from fractions import Fraction

import pytest

import star_polyfit as sp


def lagrange_coefficients(xs, ys):
    """Coefficients, lowest power first, of the polynomial through the points: product form expanded in exact rationals."""
    n = len(xs)
    total = [Fraction(0)] * n
    for i in range(n):
        basis = [Fraction(1)]
        denominator = Fraction(1)
        for j in range(n):
            if j != i:
                basis = [Fraction(0)] + basis                          # multiply by x ...
                for k in range(len(basis) - 1):
                    basis[k] -= Fraction(xs[j]) * basis[k + 1]         # ... minus x_j
                denominator *= Fraction(xs[i]) - Fraction(xs[j])
        for k in range(n):
            total[k] += Fraction(ys[i]) * basis[k] / denominator
    return tuple(float(c) for c in total)


@pytest.mark.parametrize("degree", range(0, 11))
def test_as_many_points_as_coefficients_is_interpolation(degree):
    rnd = random.Random(100 + degree)
    xs = rnd.sample([k / 8 for k in range(-40, 41)], degree + 1)
    ys = [rnd.randint(-50, 50) / 4 for _ in xs]
    got = sp.polyfit(xs, ys, degree)
    assert got == lagrange_coefficients(xs, ys) and len(got) == degree + 1
    assert all(sp.polyval(got, x) == pytest.approx(y, abs=1e-6) for x, y in zip(xs, ys))


def test_line_by_centred_sums_in_exact_rationals():
    rnd = random.Random(5)
    for _ in range(30):
        n = rnd.randint(2, 12)
        xs = [rnd.uniform(-100, 100) for _ in range(n)]
        ys = [rnd.uniform(-100, 100) for _ in range(n)]
        ws = [rnd.choice([0.5, 1.0, 3.0]) for _ in range(n)]
        fx, fy, fw = [Fraction(v) for v in xs], [Fraction(v) for v in ys], [Fraction(v) for v in ws]
        sw = sum(fw)
        mx, my = sum(w * x for w, x in zip(fw, fx)) / sw, sum(w * y for w, y in zip(fw, fy)) / sw
        slope = sum(w * (x - mx) * (y - my) for w, x, y in zip(fw, fx, fy)) / sum(w * (x - mx) ** 2 for w, x in zip(fw, fx))
        assert sp.polyfit(xs, ys, 1, ws) == (float(my - slope * mx), float(slope))
        assert sp.polyfit(xs, ys, 0, ws) == (float(my),)


def test_small_cases_by_hand():
    assert sp.polyfit([1, 2, 3], [2, 4, 9], 0) == (5.0,)                                   # the mean
    assert sp.polyfit([0, 1], [1, 4], 0, [1, 2]) == (3.0,)                                 # (1 + 8) / 3
    assert sp.polyfit([0, 1, 2, 3], [0, 1, 0, 1], 1) == (0.2, 0.2)                         # Sxy = 1, Sxx = 5
    assert sp.polyfit([1, 1, 2], [1, 2, 3], 1) == (0.0, 1.5)                               # mean (4/3, 2), Sxx = 2/3, Sxy = 1
    assert sp.polyfit([0, 1, 2, 3], [1, 0, 0, 2], 1, [1, 2, 2, 1]) == (1 / 11, 3 / 11)
    assert sp.polyfit([0, 1, 2], [0, 1, 4], 1, [1, 1, 0]) == (0.0, 1.0)                    # the third point does not count
    assert sp.polyfit([0, 1, 2], [0, 1, 4], 1) == (-1 / 3, 2.0)                            # with it: slope 2, intercept 5/3 - 2
    assert sp.polyfit([0, 1, 2, 3], [1, 1, 2, 4], 2) == (1.0, -0.5, 0.5)
    assert sp.polyfit((0.0, 1.0), (3.0, 5.0), 1) == (3.0, 2.0)                             # tuples are accepted
    assert sp.polyfit([-1, 0, 1], [1, 0, 1], 2) == (0.0, 0.0, 1.0) and sp.polyfit([-1, 0, 1], [1, 0, 1], 1) == (2 / 3, 0.0)


def test_wampler1_and_exact_polynomials_far_from_the_origin():
    xs = list(range(21))
    ys = [1 + x + x ** 2 + x ** 3 + x ** 4 + x ** 5 for x in xs]
    assert sp.polyfit(xs, ys, 5) == (1.0,) * 6 and sp.residual_sum(xs, ys, (1.0,) * 6) == 0.0
    assert sp.polyfit(xs, ys, 6) == (1.0,) * 6 + (0.0,)                                    # a higher degree adds an exact zero
    assert sp.polyfit([1e9 + k for k in range(8)], [k * k for k in range(8)], 2) == (1e18, -2e9, 1.0)
    assert sp.polyfit([1e6 + k for k in range(12)], [3.0 * k - 7.0 for k in range(12)], 3) == (-3000007.0, 3.0, 0.0, 0.0)
    cubic = [2.0 * (x - 1000.0) ** 3 - (x - 1000.0) for x in (1000.0 + k / 4 for k in range(10))]
    assert sp.polyfit([1000.0 + k / 4 for k in range(10)], cubic, 3) == (-2e9 + 1000.0, 6e6 - 1.0, -6000.0, 2.0)


def test_invariants_are_exact():
    rnd = random.Random(11)
    xs = [rnd.uniform(-3, 3) for _ in range(15)]
    ys = [rnd.uniform(-5, 5) for _ in range(15)]
    ws = [rnd.uniform(0.25, 4.0) for _ in range(15)]
    base = sp.polyfit(xs, ys, 4, ws)
    order = list(range(15))
    rnd.shuffle(order)
    assert sp.polyfit([xs[i] for i in order], [ys[i] for i in order], 4, [ws[i] for i in order]) == base
    assert sp.polyfit(xs * 2, ys * 2, 4, ws * 2) == base                                   # every point twice
    assert sp.polyfit(xs, ys, 4, [8.0 * w for w in ws]) == base                            # weights are relative (a power of two: exact)
    assert sp.polyfit(xs, ys, 4, [1.0] * 15) == sp.polyfit(xs, ys, 4) != base
    assert sp.polyfit(xs + [0.123], ys + [99.0], 4, ws + [0.0]) == base                    # a point of weight 0 is not there
    doubled = sp.polyfit(xs, [2.0 * y for y in ys], 4, ws)
    assert doubled == tuple(2.0 * c for c in base)                                         # linear in y, and doubling is exact


def test_normal_equations_hold_for_the_exact_solution():
    rnd = random.Random(3)
    xs = [rnd.uniform(-2, 2) for _ in range(12)]
    ys = [rnd.uniform(-10, 10) for _ in range(12)]
    coefficients = sp.polyfit(xs, ys, 3)
    best = sp.residual_sum(xs, ys, coefficients)
    for k in range(4):
        gradient = sum((Fraction(y) - sum(Fraction(c) * Fraction(x) ** j for j, c in enumerate(coefficients))) * Fraction(x) ** k for x, y in zip(xs, ys))
        assert abs(float(gradient)) < 1e-11
        for step in (1e-6, -1e-6):
            moved = list(coefficients)
            moved[k] += step
            assert sp.residual_sum(xs, ys, moved) > best


def test_polyval_and_residual_sum_are_exact_sums_rounded_once():
    assert sp.polyval([1, 2, 3], 2) == 17.0 and sp.polyval((5,), 123.0) == 5.0 and sp.polyval([0.0, 0.0, 1.0], -3) == 9.0
    assert sp.polyval([1e100, 1.0, -1e100], 1.0) == 1.0                                    # float arithmetic gives 0.0
    assert sp.polyval([1.0, 1e-30], 1.0) == 1.0 and sp.polyval([-1.0, 1.0], 1.0 + 2.0 ** -52) == 2.0 ** -52
    q = Fraction(0.1) + Fraction(0.2) * Fraction(0.3)
    assert sp.polyval([0.1, 0.2], 0.3) == float(q)
    assert sp.residual_sum([0, 1, 2, 3], [0, 1, 0, 1], [0.2, 0.2]) == pytest.approx(0.8, rel=1e-15)
    assert sp.residual_sum([0, 1, 2, 3], [0, 1, 0, 1], [0.0]) == 2.0 and sp.residual_sum([0, 1, 2, 3], [0, 1, 0, 1], [0.0], [1, 3, 5, 0.5]) == 3.5
    assert sp.residual_sum([1.0], [1e-200], [0.0]) == 0.0 and sp.residual_sum([2.0], [5.0], [1.0, 2.0]) == 0.0
    assert sp.residual_sum([0], [1e100], [-1e100]) == 4e200
    assert sp.residual_sum([0, 0, 0], [1e100] * 3, [-1e100]) == pytest.approx(1.2e201, rel=1e-15)
    assert isinstance(sp.polyval([1], 1), float) and isinstance(sp.residual_sum([1], [1], [1]), float) and isinstance(sp.polyfit([1], [1], 0)[0], float)


def test_limits():
    assert (sp.MAX_DEGREE, sp.MAX_POINTS, sp.BIG, sp.__version__) == (10, 10000, 1e100, "0.1.0")
    assert sp.polyfit([1e100], [1e100], 0) == (1e100,) and sp.polyfit([-1e100, 1e100], [-1e100, 1e100], 1) == (0.0, 1.0)
    xs = [k / 10 for k in range(sp.MAX_POINTS)]
    assert sp.polyfit(xs, [2.0] * sp.MAX_POINTS, 0) == (2.0,)
    with pytest.raises(ValueError, match="1 to 10000 numbers"):
        sp.polyfit(xs + [1.0], [2.0] * (sp.MAX_POINTS + 1), 0)
    assert len(sp.polyfit(list(range(11)), [float(k % 3) for k in range(11)], 10)) == 11
    assert sp.polyval([1.0] * 11, 1.0) == 11.0
    with pytest.raises(ValueError, match="coefficients must be a list or tuple of 1 to 11 numbers"):
        sp.polyval([1.0] * 12, 1.0)
    with pytest.raises(ValueError, match="coefficients must be a list or tuple of 1 to 11 numbers"):
        sp.residual_sum([1], [1], [])


def test_refusals_name_the_argument():
    for degree in (-1, 11, 1.0, "2", None, True, False):
        with pytest.raises(ValueError, match="degree must be an integer from 0 to 10"):
            sp.polyfit([0, 1, 2], [0, 1, 2], degree)
    for bad in ("12", None, {1.0, 2.0}, 3.0, [], iter([1.0, 2.0])):
        with pytest.raises(ValueError, match="xs must be a list or tuple"):
            sp.polyfit(bad, [1.0, 2.0], 0)
        with pytest.raises(ValueError, match="ys must be a list or tuple"):
            sp.polyfit([1.0, 2.0], bad, 0)
        with pytest.raises(ValueError, match="coefficients must be a list or tuple"):
            sp.polyval(bad, 0.0)
    for bad in (True, False, "1", None, 1j, float("nan"), float("inf"), float("-inf"), 1.0000001e100, -1.0000001e100, 10 ** 400):
        with pytest.raises(ValueError, match="xs must be finite real numbers"):
            sp.polyfit([0.0, bad], [1.0, 2.0], 0)
        with pytest.raises(ValueError, match="ys must be finite real numbers"):
            sp.residual_sum([0.0, 1.0], [bad, 2.0], [1.0])
        with pytest.raises(ValueError, match="weights must be finite real numbers"):
            sp.polyfit([0.0, 1.0], [1.0, 2.0], 0, [1.0, bad])
        with pytest.raises(ValueError, match="coefficients must be finite real numbers"):
            sp.polyval([bad], 0.0)
        with pytest.raises(ValueError, match="x must be finite real numbers"):
            sp.polyval([1.0], bad)
    with pytest.raises(ValueError, match="same length"):
        sp.polyfit([0, 1, 2], [0, 1], 0)
    with pytest.raises(ValueError, match="same length"):
        sp.residual_sum([0, 1], [0, 1, 2], [1.0])
    with pytest.raises(ValueError, match="as many as the points"):
        sp.polyfit([0, 1, 2], [0, 1, 2], 0, [1, 1])
    with pytest.raises(ValueError, match="weights must be a list or tuple"):
        sp.polyfit([0, 1, 2], [0, 1, 2], 0, 1.0)
    for weights in ([1, -1, 1], [1, 1, -5e-324]):
        with pytest.raises(ValueError, match="weights must be >= 0"):
            sp.polyfit([0, 1, 2], [0, 1, 2], 0, weights)
        with pytest.raises(ValueError, match="weights must be >= 0"):
            sp.residual_sum([0, 1, 2], [0, 1, 2], [0.0], weights)


def test_a_fit_that_is_not_unique_is_refused():
    for xs, ys, degree, weights, need in (([1, 1, 2], [1, 2, 3], 2, None, 3), ([1, 1, 1], [1, 2, 3], 1, None, 2), ([0, 1, 2], [1, 2, 3], 2, [1, 1, 0], 3),
                                          ([1, 2], [1, 2], 2, None, 3), ([0, 1], [1, 2], 0, [0, 0], 1), ([0.5] * 6, [1, 2, 3, 4, 5, 6], 5, None, 6)):
        with pytest.raises(ValueError, match=f"a fit of degree {degree} needs at least {need} distinct x with a positive weight"):
            sp.polyfit(xs, ys, degree, weights)
    assert sp.polyfit([1, 1, 1], [1, 2, 3], 0) == (2.0,)                                   # degree 0 needs one distinct x only
    assert sp.polyfit([0, 0, 2.0 ** -1000], [0, 0, 1], 1) == (0.0, 2.0 ** 1000)            # two x a hair apart are distinct


def test_results_too_large_for_a_float():
    with pytest.raises(ValueError, match="too large for a float"):
        sp.polyval([0.0] * 10 + [1e100], 1e100)
    with pytest.raises(ValueError, match="too large for a float"):
        sp.residual_sum([1e100], [1e100], [0.0, 0.0, 1e100])
    with pytest.raises(ValueError, match="too large for a float"):
        sp.polyfit([0.0, 1e-300], [0.0, 1e100], 1)                                         # slope 1e400
