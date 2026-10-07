"""star_polyfit against published reference values and hand-derivable checks.
Verifies published datasets, exact small systems, inverses/invariants and edge branches.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import random

import pytest

import star_polyfit as sp


def test_wampler1_published_exact():
    xs = list(range(21))
    ys = [sum(x ** k for k in range(6)) for x in xs]  # 1 + x + ... + x^5
    c = sp.polyfit(xs, ys, 5)
    assert c == (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert sp.residual_sum(xs, ys, c) == 0.0


def test_wampler2_published_relative_1e12():
    xs = list(range(21))
    ys = [round(sum((0.1 ** k) * (x ** k) for k in range(6)), 5) for x in xs]
    c = sp.polyfit(xs, ys, 5)
    ref = (1.0, 0.1, 0.01, 0.001, 0.0001, 0.00001)
    for a, b in zip(c, ref):
        assert a == pytest.approx(b, rel=1e-12, abs=0.0)


def test_hand_derived_exact_cases():
    assert sp.polyfit([1, 2, 3], [2, 4, 9], 0) == (5.0,)  # mean = (2+4+9)/3 = 5
    assert sp.polyfit([0, 1], [1, 4], 0, [1, 2]) == (3.0,)  # weighted mean = (1*1+2*4)/(1+2)=3
    assert sp.polyfit([0, 1, 2], [1, 3, 7], 2) == (1.0, 1.0, 1.0)  # 1 + x + x^2
    assert sp.polyfit([0, 1], [3, 5], 1) == (3.0, 2.0)  # y=3+2x
    assert sp.polyfit([5], [7], 0) == (7.0,)


def test_line_and_weighted_line_and_residual_by_hand():
    c = sp.polyfit([0, 1, 2, 3], [0, 1, 0, 1], 1)
    assert c == pytest.approx((0.2, 0.2), abs=1e-16)
    # residuals for y - (0.2 + 0.2x): -0.2, 0.6, -0.6, 0.2 => squares sum 0.8
    assert sp.residual_sum([0, 1, 2, 3], [0, 1, 0, 1], [0.2, 0.2]) == pytest.approx(0.8, abs=1e-15)

    cw = sp.polyfit([0, 1, 2, 3], [1, 0, 0, 2], 1, [1, 2, 2, 1])
    assert cw == pytest.approx((1 / 11, 3 / 11), abs=1e-16)


def test_zero_weight_removes_point_and_weight_scaling_invariant():
    c1 = sp.polyfit([0, 1, 2], [0, 1, 4], 1, [1, 1, 0])
    c2 = sp.polyfit([0, 1, 2], [0, 1, 4], 1, [7, 7, 0])
    assert c1 == (0.0, 1.0)
    assert c2 == c1


def test_offset_quadratic_exact_and_order_repetition_invariants():
    xs = [1e9 + k for k in range(8)]
    ys = [k * k for k in range(8)]
    # (x-1e9)^2 = x^2 - 2e9 x + 1e18
    assert sp.polyfit(xs, ys, 2) == (1e18, -2e9, 1.0)

    x2, y2 = [0, 1, 2, 3], [1, 1, 2, 4]
    assert sp.polyfit(x2, y2, 2) == (1.0, -0.5, 0.5)
    assert sp.polyfit([3, 1, 0, 2], [4, 1, 1, 2], 2) == (1.0, -0.5, 0.5)
    assert sp.polyfit(x2 * 2, y2 * 2, 2) == (1.0, -0.5, 0.5)


def test_polyval_and_least_squares_minimum_nonnegative():
    assert sp.polyval([1, 2, 3], 2) == 17.0
    assert sp.polyval([5], 123.0) == 5.0
    assert sp.polyval([0.1, 0.2], 0.3) == 0.16

    xs, ys = [0, 1, 2, 3, 4], [2, 3, 5, 4, 6]
    c = sp.polyfit(xs, ys, 2)
    r0 = sp.residual_sum(xs, ys, c)
    assert r0 >= 0.0
    for i in range(len(c)):
        d = list(c)
        d[i] = d[i] * (1 + 1e-3) if d[i] != 0 else 1e-3
        assert sp.residual_sum(xs, ys, d) >= r0 - 1e-15


def test_inverse_normal_equation_moments_small():
    rnd = random.Random(7)
    xs = [rnd.uniform(-2, 2) for _ in range(20)]
    ys = [rnd.uniform(-10, 10) for _ in range(20)]
    ws = [rnd.uniform(0.2, 2.0) for _ in range(20)]
    deg = 3
    c = sp.polyfit(xs, ys, deg, ws)
    rs = [ys[i] - sp.polyval(c, xs[i]) for i in range(len(xs))]
    for k in range(deg + 1):
        s = sum(ws[i] * rs[i] * (xs[i] ** k) for i in range(len(xs)))
        assert abs(s) < 1e-9
