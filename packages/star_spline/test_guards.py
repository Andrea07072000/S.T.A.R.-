"""Guard tests of star_spline written by the reviewer: an independent oracle (the conditions that DEFINE the natural
spline, checked in exact rational arithmetic on the pieces rebuilt here from the numbers returned), the textbook
example, hand cases, and every refusal by name. Relative tolerances carry abs=0."""
import math
import random
from fractions import Fraction

import pytest

import star_spline as ss


def random_table(rnd, n):
    xs = [rnd.uniform(-20.0, 20.0)]
    for _ in range(n - 1):
        xs.append(xs[-1] + 10.0 ** rnd.uniform(-2, 1))
    return xs, [rnd.uniform(-10.0, 10.0) for _ in range(n)]


def test_textbook_example_of_burden_and_faires():
    xs, ys = [1, 2, 3], [2, 3, 5]
    assert ss.second_derivatives(xs, ys) == (0.0, 1.5, 0.0)
    assert ss.values(xs, ys, [1, 1.5, 2, 2.5, 3]) == (2.0, 2.40625, 3.0, 3.90625, 5.0)
    assert ss.derivatives(xs, ys, [1, 2, 3]) == (0.75, 1.5, 2.25) and ss.derivatives(xs, ys, [1.5, 2.5]) == (0.9375, 2.0625)      # 3/4 + 3/4 t^2; 3/2 + 3/2 t - 3/4 t^2
    assert ss.integral(xs, ys, 1, 3) == 6.375 and ss.integral(xs, ys, 1, 2) == 2.4375 and ss.integral(xs, ys, 2, 3) == 3.9375
    assert ss.integral(xs, ys, 1.5, 2.5) == 3.0546875 and ss.integral(xs, ys, 3, 1) == -6.375 and ss.integral(xs, ys, 2, 2) == 0.0


@pytest.mark.parametrize("n", [3, 4, 5, 9, 20])
def test_the_defining_conditions_hold(n):
    """On every interval the cubic rebuilt from the values and derivatives returned at its ends must have, at interior
    knots, the same slope and the same second derivative as its neighbour; at the two ends the second derivative is 0."""
    rnd = random.Random(n)
    xs, ys = random_table(rnd, n)
    m = ss.second_derivatives(xs, ys)
    slopes = ss.derivatives(xs, ys, xs)
    assert ss.values(xs, ys, xs) == tuple(float(y) for y in ys) and m[0] == 0.0 and m[-1] == 0.0 and len(m) == n
    scale_m = max(abs(v) for v in m) or 1.0
    scale_s = max(abs(v) for v in slopes)
    for i in range(n - 1):
        h = xs[i + 1] - xs[i]
        chord = (ys[i + 1] - ys[i]) / h
        # a cubic with second derivatives m_i, m_(i+1) at the ends of an interval of length h and chord slope `chord`:
        assert slopes[i] == pytest.approx(chord - h * (2 * m[i] + m[i + 1]) / 6, abs=3e-13 * (scale_s + h * scale_m))
        assert slopes[i + 1] == pytest.approx(chord + h * (m[i] + 2 * m[i + 1]) / 6, abs=3e-13 * (scale_s + h * scale_m))
        middle = xs[i] + h / 2
        assert ss.values(xs, ys, [middle])[0] == pytest.approx((ys[i] + ys[i + 1]) / 2 - h * h * (m[i] + m[i + 1]) / 16, abs=1e-12 * (10 + h * h * scale_m))
    # the tridiagonal equations themselves, in exact rationals on the floats returned
    for i in range(1, n - 1):
        h0, h1 = Fraction(xs[i]) - Fraction(xs[i - 1]), Fraction(xs[i + 1]) - Fraction(xs[i])
        left = h0 * Fraction(m[i - 1]) + 2 * (h0 + h1) * Fraction(m[i]) + h1 * Fraction(m[i + 1])
        right = 6 * ((Fraction(ys[i + 1]) - Fraction(ys[i])) / h1 - (Fraction(ys[i]) - Fraction(ys[i - 1])) / h0)
        assert abs(float(left - right)) <= 1e-13 * (h0 + h1) * scale_m + 1e-13 * abs(float(right))


def test_hand_cases():
    assert ss.second_derivatives([0, 1], [1, 3]) == (0.0, 0.0) and ss.values([0, 1], [1, 3], [0.25]) == (1.5,) and ss.derivatives([0, 1], [1, 3], [0.7]) == (2.0,)
    assert ss.integral([0, 1], [1, 3], 0, 1) == 2.0 and ss.integral([0, 1], [1, 3], 0.5, 1) == 1.25
    assert ss.second_derivatives([0, 1, 2], [0, 1, 0]) == (0.0, -3.0, 0.0)                 # 4 h M1 = 6 (y2 - 2 y1 + y0) / h
    assert ss.values([0, 1, 2], [0, 1, 0], [0.5, 1.5]) == (0.6875, 0.6875) and ss.integral([0, 1, 2], [0, 1, 0], 0, 2) == 1.25
    assert ss.derivatives([0, 1, 2], [0, 1, 0], [0, 1, 2]) == (1.5, 0.0, -1.5)             # chord 1, minus h (2 M0 + M1) / 6 = +1/2
    assert ss.second_derivatives([0, 2, 4], [1, 0, 1]) == (0.0, 0.75, 0.0) and ss.second_derivatives((0, 2, 4), (1, 0, 1)) == (0.0, 0.75, 0.0)
    line = [0, 1, 2, 3, 4]
    assert ss.second_derivatives(line, [1, 3, 5, 7, 9]) == (0.0,) * 5 and ss.values(line, [1, 3, 5, 7, 9], [2.5]) == (6.0,) and ss.derivatives(line, [1, 3, 5, 7, 9], [0, 0.3, 4]) == (2.0,) * 3
    uneven = [0, 0.125, 5, 5.5, 20]
    on_line = [3 - 0.5 * x for x in uneven]
    assert ss.second_derivatives(uneven, on_line) == (0.0,) * 5 and ss.derivatives(uneven, on_line, [0.05, 3, 19]) == (-0.5,) * 3 and ss.values(uneven, on_line, [7.0]) == (-0.5,)
    assert ss.values([0, 1, 2], [5, 5, 5], [0.3, 1.9]) == (5.0, 5.0) and ss.integral([0, 1, 2], [5, 5, 5], 0.25, 1.75) == 7.5
    assert ss.values([0, 1, 2], [0, 1, 0], []) == () and ss.derivatives([0, 1, 2], [0, 1, 0], ()) == ()


def test_exactness_where_floats_would_lose_digits():
    ys = [0.3, -1.2, 2.5, 0.7, 1.1]
    near = ss.values([0, 1, 2, 3, 4], ys, [1.5, 3.25])
    assert ss.values([1e9 + k for k in range(5)], ys, [1e9 + 1.5, 1e9 + 3.25]) == near                     # a shift that floats hold exactly changes nothing
    assert ss.second_derivatives([1e9 + k for k in range(5)], ys) == ss.second_derivatives([0, 1, 2, 3, 4], ys)
    small = ss.values([0, 1, 2, 3, 4], [0.0, 2.0, 1.0, 4.0, 3.0], [1.5])[0]
    big = ss.values([0, 1, 2, 3, 4], [1e15 + y for y in (0.0, 2.0, 1.0, 4.0, 3.0)], [1.5])[0]
    assert abs(big - 1e15 - small) <= 0.0625                                                               # the nearest float to 1e15 + small: floats are 0.125 apart there
    scaled = ss.values([0, 1, 2, 3, 4], [2 * y for y in ys], [1.5, 3.25])
    assert scaled == tuple(2 * v for v in near)                                                            # doubling is exact
    tiny = [k * 2.0 ** -40 for k in range(5)]                                                              # knots 1e-12 apart
    assert ss.values(tiny, ys, [1.5 * 2.0 ** -40, 3.25 * 2.0 ** -40]) == near
    assert ss.second_derivatives(tiny, ys) == tuple(v * 2.0 ** 80 for v in ss.second_derivatives([0, 1, 2, 3, 4], ys))
    sym_x, sym_y = [-3, -1, 0, 1, 3], [2.0, -1.5, 0.25, -1.5, 2.0]
    assert ss.values(sym_x, sym_y, [-2.2, -0.4]) == ss.values(sym_x, sym_y, [2.2, 0.4])
    assert ss.derivatives(sym_x, sym_y, [-2.2])[0] == -ss.derivatives(sym_x, sym_y, [2.2])[0] and ss.derivatives(sym_x, sym_y, [0])[0] == 0.0


def test_integral_identities():
    rnd = random.Random(8)
    xs, ys = random_table(rnd, 12)
    a, b, c = xs[0], xs[5] + 0.3 * (xs[6] - xs[5]), xs[-1]
    whole = ss.integral(xs, ys, a, c)
    assert ss.integral(xs, ys, a, b) + ss.integral(xs, ys, b, c) == pytest.approx(whole, rel=1e-13, abs=0)
    assert ss.integral(xs, ys, c, a) == -whole and ss.integral(xs, ys, b, b) == 0.0
    m = ss.second_derivatives(xs, ys)
    expected = sum((xs[i + 1] - xs[i]) * (ys[i] + ys[i + 1]) / 2 - (xs[i + 1] - xs[i]) ** 3 * (m[i] + m[i + 1]) / 24 for i in range(11))    # trapezoid minus the cubic correction
    assert whole == pytest.approx(expected, rel=1e-12, abs=0)
    step = 1e-6                                                                            # the derivative of the integral is the spline
    assert (ss.integral(xs, ys, a, b + step) - ss.integral(xs, ys, a, b - step)) / (2 * step) == pytest.approx(ss.values(xs, ys, [b])[0], rel=1e-7, abs=0)
    assert (ss.values(xs, ys, [b + step])[0] - ss.values(xs, ys, [b - step])[0]) / (2 * step) == pytest.approx(ss.derivatives(xs, ys, [b])[0], rel=1e-7, abs=0)


def test_limits():
    assert (ss.MAX_POINTS, ss.BIG, ss.__version__, ss.__all__) == (300, 1e100, "0.1.0", ["second_derivatives", "values", "derivatives", "integral"])
    xs = [float(k) for k in range(ss.MAX_POINTS)]
    ys = [float(k % 2) for k in range(ss.MAX_POINTS)]
    m = ss.second_derivatives(xs, ys)
    assert len(m) == 300 and m[0] == 0.0 and m[-1] == 0.0 and all(isinstance(v, float) for v in m)
    with pytest.raises(ValueError, match="xs must be a list or tuple of 2 to 300 numbers"):
        ss.second_derivatives(xs + [300.0], ys + [0.0])
    assert ss.values([-1e100, 1e100], [-1e100, 1e100], [0.0, 1e100]) == (0.0, 1e100)
    assert ss.values([0, 1e-300, 2e-300], [0, 1e100, 0], [1e-300]) == (1e100,)
    with pytest.raises(ValueError, match="too large for a float"):
        ss.second_derivatives([0, 1e-300, 2e-300], [0, 1e100, 0])                          # about -3e700
    with pytest.raises(ValueError, match="too large for a float"):
        ss.derivatives([0, 1e-300, 2e-300], [0, 1e100, 0], [0])
    assert ss.integral([-1e100, 1e100], [1e100, 1e100], -1e100, 1e100) == 2e200           # the largest area the limits allow is still a float


def test_refusals_name_the_argument():
    good_x, good_y = [0.0, 1.0, 2.0], [0.0, 1.0, 0.0]
    for bad in ("abc", None, 3.0, iter([0.0, 1.0]), [1.0], []):
        with pytest.raises(ValueError, match="xs must be a list or tuple of 2 to 300 numbers"):
            ss.values(bad, good_y, [0.5])
        with pytest.raises(ValueError, match="ys must be a list or tuple of 2 to 300 numbers"):
            ss.second_derivatives(good_x, bad)
    for bad in (True, False, "1", None, 1j, float("nan"), float("inf"), float("-inf"), 1.0000001e100, 10 ** 400):
        with pytest.raises(ValueError, match="xs must be finite real numbers"):
            ss.second_derivatives([0.0, 1.0, bad], good_y)
        with pytest.raises(ValueError, match="ys must be finite real numbers"):
            ss.derivatives(good_x, [0.0, bad, 0.0], [0.5])
        with pytest.raises(ValueError, match="points must be finite real numbers"):
            ss.values(good_x, good_y, [0.5, bad])
        with pytest.raises(ValueError, match="a must be finite real numbers"):
            ss.integral(good_x, good_y, bad, 1.0)
        with pytest.raises(ValueError, match="b must be finite real numbers"):
            ss.integral(good_x, good_y, 0.0, bad)
    with pytest.raises(ValueError, match="same length"):
        ss.values(good_x, [0.0, 1.0], [0.5])
    for bad in ([0, 1, 1], [0, 2, 1], [2, 1, 0], [0, 0, 1]):
        with pytest.raises(ValueError, match="xs must be strictly increasing"):
            ss.second_derivatives(bad, good_y)
    assert ss.second_derivatives([0.0, math.nextafter(0.0, 1.0), 1.0], [0.0, 0.0, 0.0]) == (0.0, 0.0, 0.0)       # two knots one float apart are distinct
    for outside in (math.nextafter(0.0, -1.0), math.nextafter(2.0, 3.0), -1.0, 2.5):
        with pytest.raises(ValueError, match="points must be inside the table"):
            ss.values(good_x, good_y, [outside])
        with pytest.raises(ValueError, match="points must be inside the table"):
            ss.derivatives(good_x, good_y, [1.0, outside])
        with pytest.raises(ValueError, match="a must be inside the table"):
            ss.integral(good_x, good_y, outside, 1.0)
        with pytest.raises(ValueError, match="b must be inside the table"):
            ss.integral(good_x, good_y, 1.0, outside)
    for bad in (0.5, "ab", None, {0.5}):
        with pytest.raises(ValueError, match="points must be a list or tuple of numbers"):
            ss.values(good_x, good_y, bad)
