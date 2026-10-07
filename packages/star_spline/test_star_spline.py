"""star_spline against published spline values and hand-derivable invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_spline as ss


def test_published_burden_faires_example():
    xs, ys = [1, 2, 3], [2, 3, 5]
    assert ss.second_derivatives(xs, ys) == (0.0, 1.5, 0.0)
    assert ss.values(xs, ys, [1, 1.5, 2, 2.5, 3]) == (2.0, 2.40625, 3.0, 3.90625, 5.0)
    assert ss.derivatives(xs, ys, [1, 2, 3]) == (0.75, 1.5, 2.25)
    assert ss.integral(xs, ys, 1, 3) == pytest.approx(6.375, abs=0)
    assert ss.integral(xs, ys, 1.5, 2.5) == pytest.approx(3.0546875, abs=0)


def test_two_points_are_a_line_and_exact_shapes():
    xs, ys = [0, 1], [1, 3]
    assert ss.second_derivatives(xs, ys) == (0.0, 0.0)
    assert ss.values(xs, ys, [0.25]) == (1.5,)
    assert ss.derivatives(xs, ys, [0.7]) == (2.0,)
    assert ss.integral(xs, ys, 0, 1) == pytest.approx(2.0, abs=0)
    assert ss.values(xs, ys, []) == ()
    assert isinstance(ss.integral(xs, ys, 0, 0), float)


def test_passes_through_knots_and_end_points_exactly():
    xs, ys = [0, 0.5, 2.0, 5.0], [1, -2, 4, 3]
    assert ss.values(xs, ys, xs) == tuple(float(y) for y in ys)
    assert ss.values(xs, ys, [xs[0], xs[-1]]) == (float(ys[0]), float(ys[-1]))


def test_line_data_give_zero_second_derivatives_even_and_uneven():
    xs1, ys1 = [0, 1, 2, 3, 4], [1, 3, 5, 7, 9]
    assert ss.second_derivatives(xs1, ys1) == (0.0, 0.0, 0.0, 0.0, 0.0)
    assert ss.values(xs1, ys1, [2.5]) == (6.0,)
    assert ss.derivatives(xs1, ys1, [0.25, 1.75, 3.5]) == (2.0, 2.0, 2.0)

    xs2 = [0, 0.125, 5, 5.5, 20]
    ys2 = [3 - 0.5 * x for x in xs2]
    assert ss.second_derivatives(xs2, ys2) == (0.0, 0.0, 0.0, 0.0, 0.0)
    assert ss.derivatives(xs2, ys2, [0.125, 2.0, 12.0]) == (-0.5, -0.5, -0.5)


def test_three_knot_hand_derivations():
    # For equally spaced [0,h,2h], natural spline gives: 4h M1 = 6*(y2 - 2y1 + y0)/h.
    # So M1 = 3*(y0 - 2y1 + y2)/(2*h^2).
    assert ss.second_derivatives([0, 1, 2], [0, 1, 0])[1] == -3.0
    # At x=0.5 for [0,1,2],[0,1,0]: linear interpolation is 0.5 and correction is +3/16 => 11/16 = 0.6875.
    assert ss.values([0, 1, 2], [0, 1, 0], [0.5]) == (0.6875,)
    assert ss.second_derivatives([0, 2, 4], [1, 0, 1])[1] == 0.75


def test_symmetry_linearity_scaling_shift():
    xs = [0, 1, 2, 3, 4]
    ys_sym = [2, 1, 0, 1, 2]
    x = 0.75
    xm = xs[0] + xs[-1] - x
    assert ss.values(xs, ys_sym, [x])[0] == ss.values(xs, ys_sym, [xm])[0]

    ys1 = [1, 0, -1, 2, 3]
    ys2 = [0, 4, 1, -2, 5]
    ysum = [a + b for a, b in zip(ys1, ys2)]
    p = [0.3, 1.1, 2.7, 3.6]
    v_sum = ss.values(xs, ysum, p)
    v_sep = tuple(a + b for a, b in zip(ss.values(xs, ys1, p), ss.values(xs, ys2, p)))
    for a, b in zip(v_sum, v_sep):
        assert a == pytest.approx(b, abs=1e-12)

    v2 = ss.values(xs, [2 * y for y in ys1], p)
    d2 = ss.derivatives(xs, [2 * y for y in ys1], p)
    for a, b in zip(v2, ss.values(xs, ys1, p)):
        assert a == 2.0 * b
    for a, b in zip(d2, ss.derivatives(xs, ys1, p)):
        assert a == 2.0 * b

    base = ss.values([0, 1, 2, 3, 4], ys1, [1.5])[0]
    shifted = ss.values([1e9 + k for k in range(5)], ys1, [1e9 + 1.5])[0]
    assert shifted == base


def test_derivative_continuity_and_second_derivative_limit():
    xs, ys = [0, 1, 2], [0, 1, 0]
    m = ss.second_derivatives(xs, ys)[1]
    eps = 1e-6
    dl = ss.derivatives(xs, ys, [1 - eps])[0]
    dr = ss.derivatives(xs, ys, [1 + eps])[0]
    d0 = ss.derivatives(xs, ys, [1])[0]
    assert d0 == pytest.approx((dl + dr) / 2, abs=1e-9)
    # Central finite-difference of derivative tends to second derivative at knot.
    assert (dr - dl) / (2 * eps) == pytest.approx(m, rel=1e-6, abs=0)


def test_integral_invariants_and_hand_formula():
    xs, ys = [0, 1, 2], [0, 1, 0]
    assert ss.integral(xs, ys, 1.2, 1.2) == 0.0
    assert ss.integral(xs, ys, 1.8, 0.2) == -ss.integral(xs, ys, 0.2, 1.8)
    iac = ss.integral(xs, ys, 0.1, 1.9)
    iab = ss.integral(xs, ys, 0.1, 1.0)
    ibc = ss.integral(xs, ys, 1.0, 1.9)
    assert iac == pytest.approx(iab + ibc, rel=1e-13, abs=0)

    # Natural spline integral on equally spaced knots:
    # sum trapezoids - h^3/24 * sum(M_i + M_{i+1}) over intervals.
    # Here h=1, trapezoid sum = 1.0, M=(0,-3,0), correction = -(1/24)*((-3)+(-3)) = +0.25 => 1.25.
    assert ss.integral([0, 1, 2], [0, 1, 0], 0, 2) == pytest.approx(1.25, abs=0)
