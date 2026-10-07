"""Guard tests of star_linefit written by the reviewer: every result against the textbook sums written out in exact
fractions (not the centred sums the module uses), the correct rounding of the square roots, and the limits."""
import math
from fractions import Fraction as F

import pytest

import star_linefit as lf


def nearest(x: float, q: F) -> bool:
    """True when x is the float nearest to the non-negative real whose square is q."""
    lo, hi = (F(x) + F(math.nextafter(x, 0.0))) / 2, (F(x) + F(math.nextafter(x, math.inf))) / 2
    return lo * lo <= q <= hi * hi


def textbook(xs, ys):
    """Slope, intercept, squared errors, squared residual deviation and squared correlation from the raw sums."""
    x, y = [F(v) for v in xs], [F(v) for v in ys]
    n = len(x)
    sx, sy, sxx, sxy, syy = sum(x), sum(y), sum(a * a for a in x), sum(a * b for a, b in zip(x, y)), sum(b * b for b in y)
    d = n * sxx - sx * sx
    slope = (n * sxy - sx * sy) / d
    intercept = (sy - slope * sx) / n
    rss = sum((b - slope * a - intercept) ** 2 for a, b in zip(x, y))
    var = rss / (n - 2) if n > 2 else None
    r2 = None if n * syy == sy * sy else (n * sxy - sx * sy) ** 2 / (d * (n * syy - sy * sy))
    return slope, intercept, var, (None if var is None else var * n / d), (None if var is None else var * sxx / d), r2, (n * sxy - sx * sy)


DATASETS = [([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 1.0, 2.0]), ([1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0]), ([0.1, 0.2, 0.3, 0.4, 0.5], [1.1, 0.9, 1.3, 1.2, 1.7]),
            ([1e9, 1e9 + 1, 1e9 + 2, 1e9 + 3], [5.0, 7.5, 9.0, 11.25]), ([-3.0, -1.0, 2.0, 2.0, 7.0], [10.0, -4.0, 0.5, 0.25, -8.0]),
            ([1e-8, 2e-8, 4e-8], [1e8, -3e8, 5e7]), ([5.0, 6.0, 7.0], [2.0, 2.0, 2.0]), ([1e100, -1e100, 0.0], [1.0, 2.0, 4.0]),
            ([float(k) for k in range(30)], [float((k * k * 7) % 31) for k in range(30)]), ([2.0, 3.0, 5.0, 7.0, 11.0, 13.0], [1.5, -2.5, 3.5, -4.5, 5.5, -6.5])]


@pytest.mark.parametrize("xs,ys", DATASETS)
def test_every_result_is_the_exact_value_rounded_once(xs, ys):
    slope, intercept, var, slope_var, intercept_var, r2, sign = textbook(xs, ys)
    assert lf.fit(xs, ys) == (float(slope), float(intercept))
    errors = lf.fit_errors(xs, ys)
    assert nearest(errors[0], slope_var) and nearest(errors[1], intercept_var) and nearest(errors[2], var)
    if r2 is None:
        with pytest.raises(ValueError, match="all the y are equal"):
            lf.correlation(xs, ys)
    else:
        r = lf.correlation(xs, ys)
        assert nearest(abs(r), r2) and (r < 0) == (sign < 0) and -1.0 <= r <= 1.0
        assert lf.correlation(ys, xs) == r and lf.correlation(xs, [-v for v in ys]) == -r and lf.correlation([0.5 * v for v in xs], [0.25 * v for v in ys]) == r
    order = list(range(len(xs)))[::-1]
    assert lf.fit([xs[i] for i in order], [ys[i] for i in order]) == lf.fit(xs, ys) and lf.fit_errors([xs[i] for i in order], [ys[i] for i in order]) == errors
    assert lf.fit(tuple(xs), tuple(ys)) == lf.fit(xs, ys) and all(type(v) is float for v in lf.fit(xs, ys) + errors)


def test_small_cases_by_hand():
    assert lf.fit([0, 1, 2], [1, 3, 5]) == (2.0, 1.0) and lf.fit([0, 1], [5, 3]) == (-2.0, 5.0) and lf.fit([2, 0], [1, 7]) == (-3.0, 7.0)
    assert lf.fit([0, 2, 4], [1, 1, 4]) == (0.75, 0.5)       # means 2 and 2; Sxx = 8, Sxy = (-2)(-1) + 0 + (2)(2) = 6
    assert lf.fit_errors([0, 2, 4], [1, 1, 4]) == (math.sqrt(F(3, 16)), math.sqrt(F(5, 4)), math.sqrt(F(3, 2)))  # residuals 0.5, -1, 0.5: 1.5 over 1; 1.5/8; 1.5 (1/3 + 4/8)
    assert lf.correlation([0, 2, 4], [1, 1, 4]) == math.sqrt(0.75)          # 36 / (8 * 6)
    assert lf.correlation([0, 2, 4], [4, 1, 1]) == -math.sqrt(0.75)
    assert lf.fit_errors([0, 1, 2], [1, 3, 5]) == (0.0, 0.0, 0.0) and lf.fit_errors([1, 2, 3], [2, 2, 2]) == (0.0, 0.0, 0.0)
    assert lf.correlation([0, 1], [5, 3]) == -1.0 and lf.correlation([0, 1], [3, 5]) == 1.0 and lf.correlation([-1, 0, 1], [1, 0, 1]) == 0.0
    assert math.copysign(1.0, lf.correlation([-1, 0, 1], [1, 0, 1])) == 1.0 and math.copysign(1.0, lf.fit([1, 2, 3], [2, 2, 2])[0]) == 1.0
    almost = lf.correlation([0.0, 1.0, 2.0], [0.0, 1.0, math.nextafter(2.0, 3.0)])
    assert almost == 1.0 or almost == math.nextafter(1.0, 0.0)               # not exactly on a line: within one float of 1
    assert lf.fit_errors([0.0, 1.0, 2.0], [0.0, 1.0, math.nextafter(2.0, 3.0)])[2] > 0.0     # and the residual is not zero


def test_square_root_next_to_a_rounding_boundary():
    for a in (1.0, 1.5, 0.7, 1e-200, 1e200, 3.0, 5.0, math.nextafter(2.0, 0.0), math.nextafter(1.0, 2.0)):   # even and odd last bits: both ways of a tie
        b = math.nextafter(a, math.inf)
        middle = (F(a) + F(b)) / 2
        tiny = middle * middle / 10 ** 120
        assert lf._sqrt(middle * middle + tiny) == b and lf._sqrt(middle * middle - tiny) == a and lf._sqrt(middle * middle) in (a, b)
        assert lf._sqrt(F(a) * F(a)) == a
    assert lf._sqrt(F(0)) == 0.0 and lf._sqrt(F(9, 4)) == 1.5 and lf._sqrt(F(5e-324) ** 2) == 5e-324 and lf._sqrt(F(5e-324) ** 2 / 5) == 0.0
    with pytest.raises(ValueError, match="too large"):
        lf._sqrt(F(10) ** 700)
    with pytest.raises(ValueError, match="too large"):
        lf._float(F(10) ** 400)
    assert lf._float(F(1, 3)) == 1 / 3


def test_degenerate_and_limit_cases():
    assert lf.BIG == 1e100 and lf.MAX_POINTS == 100000
    for f in (lf.fit, lf.fit_errors, lf.correlation):
        with pytest.raises(ValueError, match="all the x are equal"):
            f([3.0, 3.0, 3.0], [1.0, 2.0, 4.0])
        with pytest.raises(ValueError, match="same length"):
            f([1.0, 2.0, 3.0], [1.0, 2.0])
        with pytest.raises(ValueError, match="same length"):
            f([1.0, 2.0], [1.0, 2.0, 3.0])
        for bad in ([1.0], [], "12", None, iter([1.0, 2.0])):
            with pytest.raises(ValueError, match="xs must be a list or tuple"):
                f(bad, [1.0, 2.0, 3.0])
            with pytest.raises(ValueError, match="ys must be a list or tuple"):
                f([1.0, 2.0, 3.0], bad)
        for bad in (True, "1", None, float("nan"), float("inf"), -float("inf"), 1j, math.nextafter(1e100, math.inf), -math.nextafter(1e100, math.inf), 10 ** 400):
            with pytest.raises(ValueError, match="xs must be finite"):
                f([1.0, bad, 3.0], [1.0, 2.0, 4.0])
            with pytest.raises(ValueError, match="ys must be finite"):
                f([1.0, 2.0, 3.0], [1.0, bad, 4.0])
    assert lf.fit([1e100, -1e100], [1e100, -1e100]) == (1.0, 0.0) and lf.correlation([1e100, -1e100, 0.0], [-1e100, 1e100, 0.0]) == -1.0
    with pytest.raises(ValueError, match="at least 3 points"):
        lf.fit_errors([0.0, 1.0], [5.0, 3.0])
    assert lf.fit_errors([0.0, 1.0, 2.0], [5.0, 3.0, 1.0]) == (0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="too large for a float"):
        lf.fit([0.0, 5e-324], [1e100, -1e100])
    with pytest.raises(ValueError, match="too large for a float"):
        lf.fit_errors([0.0, 5e-324, 1e-323], [1e100, -1e100, 1e100])
    assert lf.correlation([0.0, 5e-324], [1e100, -1e100]) == -1.0           # the correlation of the same points is finite
