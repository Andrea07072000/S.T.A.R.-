"""Guard tests of star_chebyshev written by the reviewer: the recurrence against the polynomials written out in
exact fractions, the rule for a point at the edge of the interval, and the limits at their exact values."""
import math
from fractions import Fraction as F

import pytest

import star_chebyshev as sc


def exact(cs, x):
    """Sum of c_k T_k(x) and of c_k T_k'(x) in exact arithmetic, from T_(k+1) = 2x T_k - T_(k-1) and its derivative."""
    x = F(x)
    t0, t1, d0, d1 = F(1), x, F(0), F(1)
    p, dp = F(cs[0]), F(0)
    for c in cs[1:]:
        p, dp = p + F(c) * t1, dp + F(c) * d1
        t0, t1, d0, d1 = t1, 2 * x * t1 - t0, d1, 2 * t1 + 2 * x * d1 - d0
    return p, dp


def test_the_exact_reference_is_right_on_the_polynomials_written_out():
    x = F(3, 8)
    assert exact([0, 0, 1], x) == (2 * x * x - 1, 4 * x)
    assert exact([0, 0, 0, 1], x) == (4 * x ** 3 - 3 * x, 12 * x * x - 3)
    assert exact([0, 0, 0, 0, 1], x) == (8 * x ** 4 - 8 * x * x + 1, 32 * x ** 3 - 16 * x)
    assert exact([7, -2, 0, 5], x) == (7 - 2 * x + 5 * (4 * x ** 3 - 3 * x), -2 + 5 * (12 * x * x - 3))


SERIES = [[3.0], [1.0, -2.0], [0.5, 0.25, -4.0], [2.0, -3.0, 5.0, -7.0], [1.0, 0.0, 0.0, 0.0, 0.0, 11.0], [-1.5, 2.25, 0.0, -0.75, 3.0, 0.125, -6.0],
          [float(k * k - 7 * k + 3) for k in range(12)], [(-1.0) ** k / (k + 1) for k in range(25)], [1.0] * 40]


@pytest.mark.parametrize("cs", SERIES)
@pytest.mark.parametrize("x", [-1.0, -0.875, -0.5, -0.125, 0.0, 0.0625, 0.375, 0.75, 1.0])
def test_recurrence_equals_the_exact_sum(cs, x):
    p, dp = exact(cs, x)
    got = sc.evaluate(cs, x)
    scale = sum(abs(c) for c in cs)
    dscale = sum(k * k * abs(c) for k, c in enumerate(cs)) or 1.0
    assert abs(F(got[0]) - p) <= F(scale) * F(1, 10 ** 14)
    assert abs(F(got[1]) - dp) <= F(dscale) * F(1, 10 ** 14)
    assert type(got[0]) is float and type(got[1]) is float


@pytest.mark.parametrize("mid,radius", [(10.0, 5.0), (-3.0, 0.25), (0.0, 1.0), (1000.0, 8.0), (-0.5, 64.0)])
def test_interval_mapping_and_derivative_scale(mid, radius):
    cs = [2.0, -3.0, 5.0, -7.0]
    for x in (-1.0, -0.5, 0.0, 0.25, 1.0):                  # mid + radius * x is exact for these numbers
        p, dp = exact(cs, x)
        got = sc.evaluate_on(cs, mid + radius * x, mid, radius)
        assert got[0] == pytest.approx(float(p), abs=1e-13) and got[1] == pytest.approx(float(dp) / radius, rel=1e-13, abs=1e-13)
    assert sc.evaluate_on(cs, mid, mid, radius) == sc.evaluate(cs, 0.0)[:1] + (sc.evaluate(cs, 0.0)[1] / radius,)


def test_a_point_past_the_end_by_rounding_is_the_end_and_no_further():
    cs = [1.0, 2.0, 3.0]
    one, two, three = math.nextafter(15.0, 16.0), 15.0 + 2 * math.ulp(15.0), 15.0 + 3 * math.ulp(15.0)
    assert sc.evaluate_on(cs, 15.0, 10.0, 5.0) == (6.0, 2.8)
    assert sc.evaluate_on(cs, one, 10.0, 5.0) == (6.0, 2.8) and sc.evaluate_on(cs, two, 10.0, 5.0) == (6.0, 2.8)       # two units: taken as the end
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on(cs, three, 10.0, 5.0)                                                                           # three: refused
    low2, low3 = 5.0 - 2 * math.ulp(15.0), 5.0 - 3 * math.ulp(15.0)        # the allowance is in units of the largest of |t|, |mid|, radius: here 10
    assert math.ulp(15.0) == math.ulp(10.0)
    assert sc.evaluate_on(cs, low2, 10.0, 5.0) == (2.0, -2.0)
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on(cs, low3, 10.0, 5.0)
    # the allowance scales with the midpoint when it dominates: 2 ulp(1e6) = 2.3e-10, far more than the radius' own ulp
    mid, radius = 1e6, 1e-3
    assert sc.evaluate_on(cs, math.nextafter(mid + radius, math.inf), mid, radius) == (6.0, 14000.0)   # 1.6e-10 past the end
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on(cs, mid + radius + 4e-10, mid, radius)
    # and with the radius when the radius dominates
    big = 1e20
    assert sc.evaluate_on(cs, big + 2 * math.ulp(big), 0.0, big)[0] == 6.0
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on(cs, big + 3 * math.ulp(big), 0.0, big)
    # inside the interval nothing is clamped: just inside the end the value is not the end value
    inside = sc.evaluate_on([0.0, 1.0], 14.0, 10.0, 5.0)
    assert inside == (0.8, 0.2)
    assert sc.evaluate_on([0.0, 1.0], -14.0, -10.0, 5.0) == (-0.8, 0.2) and sc.evaluate_on([0.0, 1.0], 5.0, 10.0, 5.0) == (-1.0, 0.2)
    assert sc.evaluate_on([0.0, 1.0], one, 10.0, 5.0) == (1.0, 0.2) and sc.evaluate_on([0.0, 1.0], low2, 10.0, 5.0) == (-1.0, 0.2)   # clamped on both sides


def test_limits_at_their_exact_values():
    assert sc.MAX_TERMS == 200 and sc.BIG == 1e100 and sc.TINY == 1e-100
    assert sc.evaluate([1e100], 0.0) == (1e100, 0.0) and sc.evaluate([-1e100, 1e100], 1.0) == (0.0, 1e100)
    with pytest.raises(ValueError, match="a coefficient"):
        sc.evaluate([math.nextafter(1e100, math.inf)], 0.0)
    with pytest.raises(ValueError, match="a coefficient"):
        sc.evaluate([1.0, -math.nextafter(1e100, math.inf)], 0.0)
    assert sc.evaluate_on([1.0, 1.0], 0.0, 0.0, 1e-100) == (1.0, 1e100)
    with pytest.raises(ValueError, match="radius must be within"):
        sc.evaluate_on([1.0], 0.0, 0.0, math.nextafter(1e-100, 0.0))
    assert sc.evaluate_on([1.0, 1.0], 1e100, 0.0, 1e100) == (2.0, 1e-100)
    with pytest.raises(ValueError, match="radius"):
        sc.evaluate_on([1.0], 0.0, 0.0, math.nextafter(1e100, math.inf))
    assert sc.evaluate_on([1.0, 1.0], 2e100, 1e100, 1e100) == (2.0, 1e-100)             # t may reach mid + radius = 2e100
    assert sc.evaluate_on([1.0, 1.0], -2e100, -1e100, 1e100) == (0.0, 1e-100)
    with pytest.raises(ValueError, match="mid"):
        sc.evaluate_on([1.0], 0.0, math.nextafter(1e100, math.inf), 1e100)
    with pytest.raises(ValueError, match="t must be"):
        sc.evaluate_on([1.0], math.nextafter(2e100, math.inf), 1e100, 1e100)
    assert sc.evaluate([1.0] * 200, 1.0) == (200.0, float(sum(k * k for k in range(200))))  # 2646700
    with pytest.raises(ValueError, match="1 to 200"):
        sc.evaluate([1.0] * 201, 1.0)
    assert sc.evaluate([1e100] * 200, 1.0)[0] == pytest.approx(2e102, rel=1e-9) and math.isfinite(sc.evaluate_on([1e100] * 200, 1e-100, 0.0, 1e-100)[1])


def test_zeros_are_positive():
    for got in (sc.evaluate([-0.0], 0.5), sc.evaluate([0.0, -0.0], -0.0), sc.evaluate([1.0, -1.0], 1.0)[:1] + (0.0,), sc.evaluate_on([-0.0, 0.0, -0.0], -1.0, 0.0, 1.0)):
        assert got == (0.0, 0.0) and all(math.copysign(1.0, v) == 1.0 for v in got)
    assert math.copysign(1.0, sc.evaluate([3.0, 0.0, -0.0], -0.0)[1]) == 1.0 and math.copysign(1.0, sc.evaluate([0.0, 0.0, -1.0], 0.0)[1]) == 1.0
