"""star_poly against published values and hand-derivable cases: roots, invariants, inverses and edge branches.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_poly as sp


def _poly_value(coeffs, x):
    v, _ = sp.evaluate(list(coeffs), x)
    return v


def test_quadratic_published_cancellation_case_exact():
    # Published FACT: x^2 - 1e8 x + 1 has roots 1e-8 and 99999999.99999999.
    assert sp.quadratic_roots(1, -1e8, 1) == (1e-08, 99999999.99999999)


def test_quadratic_hand_cases_and_discriminant_sides():
    assert sp.quadratic_roots(1, -3, 2) == (1.0, 2.0)      # (x-1)(x-2)
    assert sp.quadratic_roots(2, -10, 12) == (2.0, 3.0)    # divide by 2 -> x^2-5x+6
    assert sp.quadratic_roots(-2, 0, 8) == (-2.0, 2.0)     # -2x^2+8=0 -> x^2=4
    assert sp.quadratic_roots(1, 0, 0) == (0.0,)           # x^2=0
    assert sp.quadratic_roots(1, -2, 1) == (1.0,)          # (x-1)^2
    assert sp.quadratic_roots(1, 2, 1) == (-1.0,)          # (x+1)^2
    assert sp.quadratic_roots(1, 0, 1) == ()               # x^2+1: no real root
    assert sp.quadratic_roots(1, -2, 1 + 1e-15) == ()      # disc = 4-4(1+eps)<0
    r = sp.quadratic_roots(1, -2, 1 - 1e-15)               # roots: 1 ± sqrt(1e-15)
    assert len(r) == 2
    assert r[0] == pytest.approx(0.9999999683772234, abs=1e-10)
    assert r[1] == pytest.approx(1.0000000316227766, abs=1e-10)
    s2 = math.sqrt(2.0)
    assert sp.quadratic_roots(1, 0, -2) == (-s2, s2)


def test_quadratic_tiny_leading_coefficient_and_invariants():
    roots = sp.quadratic_roots(1e-30, 1, 1e-30)
    assert roots[0] == pytest.approx(-1e30, rel=1e-15)
    assert roots[1] == pytest.approx(-1e-30, rel=1e-15)
    r1, r2 = sp.quadratic_roots(2, -10, 12)
    assert (r1 + r2) == pytest.approx(-(-10) / 2, rel=1e-12)  # Vieta sum
    assert (r1 * r2) == pytest.approx(12 / 2, rel=1e-12)      # Vieta product


def test_cubic_hand_cases_and_published_values():
    assert sp.cubic_roots(1, -6, 11, -6) == (1.0, 2.0, 3.0)      # (x-1)(x-2)(x-3)
    assert sp.cubic_roots(2, -12, 22, -12) == (1.0, 2.0, 3.0)    # scaled
    assert sp.cubic_roots(1, 0, -1, 0) == (-1.0, 0.0, 1.0)       # x(x^2-1)
    assert sp.cubic_roots(-1, 0, 1, 0) == (-1.0, 0.0, 1.0)       # sign scaled
    assert sp.cubic_roots(1, 0, -3, 2) == (-2.0, 1.0)            # (x-1)^2(x+2)
    assert sp.cubic_roots(1, -3, 3, -1) == (1.0,)                # (x-1)^3
    assert sp.cubic_roots(1, 0, 0, 0) == (0.0,)                  # x^3
    assert sp.cubic_roots(1, 0, 0, -8) == (2.0,)                 # x^3-8
    assert sp.cubic_roots(1, 0, 1, 1) == pytest.approx((-0.6823278038280193,), abs=1e-15)
    assert sp.cubic_roots(1e-20, 1, 1, 1)[0] == pytest.approx(-1e20, rel=1e-15)
    assert sp.cubic_roots(1, -1e8, 1, 0) == (0.0, 1e-08, 99999999.99999999)
    got = sp.cubic_roots(1.0, 629699208343.1134, -1725321542916490.2, 1125531448798881.0)
    exp = (-629699211083.0272, 0.6525157961281471, 2739.2612597839247)
    assert got == pytest.approx(exp, rel=1e-15)


def test_polynomial_residual_sorted_distinct_float_and_scaling_invariance():
    for coeffs, roots in [((1, -6, 11, -6), sp.cubic_roots(1, -6, 11, -6)), ((1, -3, 2), sp.quadratic_roots(1, -3, 2))]:
        assert tuple(sorted(roots)) == roots
        assert all(type(r) is float for r in roots)
        assert len(set(roots)) == len(roots)
        n = len(coeffs) - 1
        eps = 2.220446049250313e-16
        for r in roots:
            lhs = abs(_poly_value(coeffs, r))
            rhs = 4 * eps * sum(abs(c) * abs(r) ** (n - i) for i, c in enumerate(coeffs))
            assert lhs <= rhs + 1e-30
    assert sp.quadratic_roots(1, -3, 2) == sp.quadratic_roots(-2, 6, -4)
    assert sp.cubic_roots(1, -6, 11, -6) == sp.cubic_roots(-3, 18, -33, 18)


def test_evaluate_hand_cases_and_list_tuple_equivalence():
    assert sp.evaluate([1, -6, 11, -6], 2) == (0.0, -1.0)
    assert sp.evaluate([1, -6, 11, -6], 0) == (-6.0, 11.0)
    assert sp.evaluate([3], 7) == (3.0, 0.0)
    assert sp.evaluate([1, 0, 0], 3) == (9.0, 6.0)
    assert sp.evaluate([2, -3, 1, 5], 2) == (11.0, 13.0)
    assert sp.evaluate([2, -3, 1, 5], 2) == sp.evaluate((2, -3, 1, 5), 2)
