"""star_tabint behaviour: published arithmetic values, hand-derivable checks, inverses/invariants and edge cases.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math


import star_tabint as st


def test_trapezoid_published_values_and_types():
    assert st.trapezoid([0, 1, 2], [0, 1, 4]) == 3.0  # 0.5*(0+1) + 0.5*(1+4) = 0.5 + 2.5
    assert st.trapezoid([0, 1], [3, 5]) == 4.0        # width 1 * average 4
    assert st.trapezoid([0, 2, 3], [1, 1, 1]) == 3.0  # constant 1 over total width 3
    assert st.trapezoid([1, 2, 4, 8], [2, 4, 8, 16]) == 63.0
    assert st.trapezoid([-1, 0, 1], [-1, 0, 1]) == 0.0
    assert st.trapezoid([0, 0.5, 2], [4, 0, 2]) == 2.5
    assert isinstance(st.trapezoid((0, 1), (3, 5)), float)


def test_cancellation_and_rounding_examples():
    assert st.trapezoid([0, 1, 2, 3], [1e16, 1, -1e16, 1]) == -4999999999999998.0
    assert st.trapezoid([0, 1, 2], [1e16, 1.0, -1e16]) == 1.0


def test_cumulative_published_and_prefix_identity():
    xs, ys = [0, 1, 3], [0, 2, 2]
    c = st.cumulative(xs, ys)
    assert c == (0.0, 1.0, 5.0)
    assert c[0] == 0.0 and c[-1] == st.trapezoid(xs, ys)
    for k in range(1, len(xs)):
        assert c[k] == st.trapezoid(xs[: k + 1], ys[: k + 1])

    assert st.cumulative([0, 1, 2, 3], [1, 1, 1, 1]) == (0.0, 1.0, 2.0, 3.0)
    assert st.cumulative([0, 1], [3, 5]) == (0.0, 4.0)
    assert st.cumulative([0, 1, 2, 3], [1e16, 1, -1e16, 1]) == (
        0.0,
        5000000000000000.0,
        1.0,
        -4999999999999998.0,
    )
    assert all(type(v) is float for v in st.cumulative([0, 1], [3, 5]))


def test_simpson_published_values_weights_and_line_agreement():
    assert st.simpson([0, 1, 8], 1) == 4.0
    assert abs(st.simpson([0, 1, 4, 9, 16], 0.5) - (32 / 3)) <= 2e-15
    assert st.simpson([1, 1, 1], 2) == 4.0
    assert st.simpson([5, 5, 5, 5, 5], 0.25) == 5.0
    assert abs(st.simpson([1, 0.8, 2 / 3, 4 / 7, 0.5], 0.25) - (1747 / 2520)) <= 2e-16
    assert st.simpson([0, 1, 0, 0, 0], 3) == 4.0
    assert st.simpson([0, 0, 1, 0, 0], 3) == 2.0
    assert st.simpson([1, 0, 0, 0, 0], 3) == 1.0
    assert st.simpson([0, 0, 0, 0, 1], 3) == 1.0
    assert st.simpson([1, 3, 5], 1) == st.trapezoid([0, 1, 2], [1, 3, 5]) == 6.0


def test_scaling_sign_shift_and_non_symmetric_input():
    xs = [1, 3, 6, 10]
    ys = [2, -3, 5, 7]  # no zeros/symmetry
    base = st.trapezoid(xs, ys)
    assert st.trapezoid(xs, [2 * y for y in ys]) == 2 * base
    assert st.trapezoid(xs, [-y for y in ys]) == -base
    assert st.trapezoid([x + 11 for x in xs], ys) == base


def test_extreme_finite_result_and_constants():
    assert st.BIG == 1e100 and st.TINY == 1e-100 and st.MAX_POINTS == 100000
    assert st.trapezoid([-1e100, 1e100], [1e100, 1e100]) == 2e200
    assert math.isfinite(st.trapezoid([-1e100, 1e100], [1e100, 1e100]))
