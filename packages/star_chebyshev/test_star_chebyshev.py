"""star_chebyshev against published values, hand-derivable values, inverses and invariants, and edge cases.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_chebyshev as sc


def test_published_cspice_example_evaluate_on():
    p, dp = sc.evaluate_on([1, 3, 0.5, 1, 0.5, -1, 1], 1, 0.5, 3)
    assert p == pytest.approx(-0.340878, abs=5e-7)
    assert dp == pytest.approx(0.382716, abs=5e-7)


def test_hand_values_for_low_orders_and_types():
    assert sc.evaluate([5], 0.3) == (5.0, 0.0)
    assert sc.evaluate([1, 2], 0.3) == (1.6, 2.0)
    # 1 + 2*T1(0.5) + 3*T2(0.5) = 1 + 1 + 3*(2*0.25-1)=0.5 ; derivative 2 + 3*(4x)=2+6=8
    assert sc.evaluate([1, 2, 3], 0.5) == (0.5, 8.0)
    assert sc.evaluate([0, 0, 1], 0.5) == (-0.5, 2.0)
    # T3(0.5)=4*0.125-1.5=-1 ; T3'(x)=12x^2-3, so T3'(0.5)=0
    assert sc.evaluate([0, 0, 0, 1], 0.5) == (-1.0, 0.0)
    # T4(0.5)=8*0.0625-8*0.25+1=-0.5 ; T4'=32x^3-16x=-4 at x=0.5
    assert sc.evaluate([0, 0, 0, 0, 1], 0.5) == (-0.5, -4.0)
    assert sc.evaluate([2, 0, 1], 0.0) == (1.0, 0.0)
    assert sc.evaluate((1, -2, 3), -0.25) == (-1.125, -5.0)
    assert sc.evaluate((1, -2, 3), -0.25) == sc.evaluate([1, -2, 3], -0.25)
    assert sc.evaluate([1, 2, 3], 1) == sc.evaluate([1, 2, 3], 1.0)


def test_ends_tk_rules_and_max_order_exact():
    assert sc.evaluate([1, 1, 1, 1], 1) == (4.0, 14.0)
    assert sc.evaluate([1, 1, 1, 1], -1) == (0.0, 6.0)
    assert sc.evaluate([0, 1], -1) == (-1.0, 1.0)
    c7 = [0] * 7 + [1]
    assert sc.evaluate(c7, 1) == (1.0, 49.0)
    assert sc.evaluate(c7, -1) == (-1.0, 49.0)
    c199 = [0] * 199 + [1]
    assert sc.evaluate(c199, 1) == (1.0, 39601.0)
    assert sc.evaluate(c199, -1) == (-1.0, 39601.0)


def test_trigonometric_identity_for_tn_and_derivative():
    n, a = 11, 0.7
    x = math.cos(a)
    p, dp = sc.evaluate([0] * n + [1], x)
    assert p == pytest.approx(math.cos(n * a), abs=1e-13)
    assert dp == pytest.approx(n * math.sin(n * a) / math.sin(a), abs=1e-13)


def test_linearity_and_signed_zero():
    x = 0.123
    c1 = [1.25, -0.75]
    c2 = [-2.5, 0.5]
    p1, d1 = sc.evaluate(c1, x)
    p2, d2 = sc.evaluate(c2, x)
    ps, ds = sc.evaluate([c1[0] + c2[0], c1[1] + c2[1]], x)
    assert ps == pytest.approx(p1 + p2, abs=1e-12)
    assert ds == pytest.approx(d1 + d2, abs=1e-12)
    assert sc.evaluate([0.0], x) == (0.0, 0.0)
    pz, dz = sc.evaluate([-0.0, 0.0], -0.0)
    assert pz == 0.0 and dz == 0.0 and math.copysign(1.0, pz) == 1.0 and math.copysign(1.0, dz) == 1.0


def test_evaluate_on_mapping_chain_rule_and_identity_radius_one():
    assert sc.evaluate_on([1, 2, 3], 12.5, 10, 5) == (0.5, 1.6)
    assert sc.evaluate_on([0, 1], 7, 5, 4) == (0.5, 0.25)
    assert sc.evaluate_on([1, 2, 3], 15, 10, 5) == (6.0, 2.8)
    assert sc.evaluate_on([1, 2, 3], 5, 10, 5) == (2.0, -2.0)
    assert sc.evaluate_on([4], 3, 3, 1e-100) == (4.0, 0.0)
    c = [1.5, -2.0, 0.25, 4.0]
    x = -0.7
    assert sc.evaluate_on(c, x, 0, 1) == sc.evaluate(c, x)


def test_interval_rounding_tolerance_branch_and_outside_rejection():
    mid, radius = 1e6, 1e-3
    t = mid + radius
    assert sc.evaluate_on([1, 2, 3], t, mid, radius) == (6.0, 14000.0)
    t2 = math.nextafter(15.0, 16.0)
    assert sc.evaluate_on([1, 2, 3], t2, 10, 5) == (6.0, 2.8)
    with pytest.raises(ValueError, match="t must lie within"):
        sc.evaluate_on([1], 15.000001, 10, 5)


def test_extreme_size_finite_and_about_expected_sum():
    p, dp = sc.evaluate([1e100] * 200, 1.0)
    assert math.isfinite(p) and math.isfinite(dp)
    assert p == pytest.approx(2e102, rel=1e-9)
