"""star_linefit against published values and hand-derivable checks.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_linefit as sl


NIST_Y = [0.1, 338.8, 118.1, 888.0, 9.2, 228.1, 668.5, 998.5, 449.1, 778.9, 559.2, 0.3, 0.1, 778.1, 668.8, 339.3, 448.9, 10.8, 557.7, 228.3, 998.0, 888.8, 119.6, 0.3, 0.6,
          557.6, 339.3, 888.0, 998.5, 778.9, 10.2, 117.6, 228.9, 668.4, 449.2, 0.2]
NIST_X = [0.2, 337.4, 118.2, 884.6, 10.1, 226.5, 666.3, 996.3, 448.6, 777.0, 558.2, 0.4, 0.6, 775.5, 666.9, 338.0, 447.5, 11.6, 556.0, 228.1, 995.8, 887.6, 120.2, 0.3, 0.3,
          556.8, 339.1, 887.2, 999.0, 779.0, 11.1, 118.3, 229.2, 669.1, 448.9, 0.5]


def test_nist_norris_published_values():
    m, b = sl.fit(NIST_X, NIST_Y)
    em, eb, s = sl.fit_errors(NIST_X, NIST_Y)
    assert m == pytest.approx(1.00211681802045, rel=1e-12)
    assert b == pytest.approx(-0.262323073774029, rel=1e-12)
    assert em == pytest.approx(0.429796848199937e-03, rel=1e-12)
    assert eb == pytest.approx(0.232818234301152, rel=1e-12)
    assert s == pytest.approx(0.884796396144373, rel=1e-12)


def test_hand_derived_fit_and_errors_and_correlation():
    assert sl.fit([0, 1, 2], [1, 3, 5]) == (2.0, 1.0)  # y = 2x + 1 exactly
    assert sl.fit([0, 1], [5, 3]) == (-2.0, 5.0)      # two-point line through (0,5),(1,3)
    assert sl.fit([1, 2, 3], [2, 2, 2]) == (0.0, 2.0) # horizontal line
    # mean x=1.5, mean y=1, Sxx=5, Sxy=3 => slope=3/5=0.6, intercept=1-0.6*1.5=0.1
    m, b = sl.fit([0, 1, 2, 3], [0, 1, 1, 2])
    assert m == pytest.approx(0.6, abs=1e-15)
    assert b == pytest.approx(0.1, abs=1e-15)
    # residuals -0.1,0.3,-0.3,0.1 => RSS=0.2, variance=0.1 (dof=2), se_m=sqrt(0.1/5), se_b=sqrt(0.1*(1/4+1.5^2/5))
    em, eb, s = sl.fit_errors([0, 1, 2, 3], [0, 1, 1, 2])
    assert em == pytest.approx(math.sqrt(0.02), abs=1e-15)
    assert eb == pytest.approx(math.sqrt(0.07), abs=1e-15)
    assert s == pytest.approx(math.sqrt(0.1), abs=1e-15)
    assert sl.fit_errors([0, 1, 2], [1, 3, 5]) == (0.0, 0.0, 0.0)
    assert sl.correlation([1, 2, 3], [2, 4, 6]) == 1.0
    assert sl.correlation([1, 2, 3], [6, 4, 2]) == -1.0
    # x: mean 2.5 -> Sxx=5 ; y: mean 2.5 -> Syy=5 ; Sxy=4 => r=4/sqrt(25)=0.8
    assert sl.correlation([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8, abs=1e-15)
    assert sl.correlation([0, 1, 2, 3], [0, 1, 1, 2]) == pytest.approx(3 / math.sqrt(10), abs=1e-15)
    assert sl.correlation([-1, 0, 1], [1, 0, 1]) == 0.0


def test_far_origin_and_invariants_relations():
    assert sl.fit([1e9, 1e9 + 1, 1e9 + 2], [5, 7, 9]) == (2.0, -1999999995.0)
    xs, ys = [0, 1, 2, 3], [0, 1, 1, 2]
    m, b = sl.fit(xs, ys)
    r = sl.correlation(xs, ys)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    assert m == pytest.approx(r * math.sqrt(syy / sxx), abs=1e-15)
    assert m * mx + b == pytest.approx(my, abs=1e-12)
    assert -1.0 <= r <= 1.0
    assert sl.correlation(xs, ys) == sl.correlation(ys, xs)
    assert sl.correlation([x + 8 for x in xs], ys) == pytest.approx(r, abs=1e-15)
    assert sl.correlation([x * 4 for x in xs], [y * 8 for y in ys]) == pytest.approx(r, abs=1e-15)
    assert sl.correlation([-x for x in xs], ys) == pytest.approx(-r, abs=1e-15)
    p = [3, 1, 0, 2]
    xsp, ysp = [xs[i] for i in p], [ys[i] for i in p]
    assert sl.fit(xsp, ysp) == sl.fit(xs, ys)
    assert sl.fit_errors(xsp, ysp) == sl.fit_errors(xs, ys)
    assert sl.correlation(tuple(xs), tuple(ys)) == sl.correlation(xs, ys)
