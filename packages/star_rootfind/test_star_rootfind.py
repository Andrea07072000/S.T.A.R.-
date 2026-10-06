"""star_rootfind against published and hand-derivable values, inverses/invariants, and edge/special branches.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math


import star_rootfind as sr


def test_published_wallis_cubic_root():
    r = sr.find_root(lambda x: x**3 - 2 * x - 5, 2, 3)
    assert abs(r - 2.0945514815423265) <= 4.5e-16


def test_hand_derivable_find_root_values_and_end_roots():
    assert sr.find_root(lambda x: x - 3, 0, 10) == 3.0
    assert sr.find_root(lambda x: 3 - x, 0, 10) == 3.0
    assert sr.find_root(lambda x: x, -1, 1) == 0.0
    assert sr.find_root(lambda x: 2 * x - 1, 0, 1) == 0.5
    # root solves x - 1/3 = 0, so x = 1/3 exactly as float(1/3)
    assert sr.find_root(lambda x: x - 1 / 3, 0, 1) == 1 / 3
    assert sr.find_root(lambda x: 1 / 3 - x, 0, 1) == 1 / 3
    # x^3 - 8 = 0 => x = 2, huge bracket still returns exact root
    assert sr.find_root(lambda x: x**3 - 8, -1e100, 1e100) == 2.0

    assert sr.find_root(lambda x: x - 3, 3, 5) == 3.0
    assert sr.find_root(lambda x: x - 5, 3, 5) == 5.0
    assert sr.find_root(lambda x: x * (x - 1), 0, 1) == 0.0


def test_within_one_float_examples_and_tie_to_lower():
    r = sr.find_root(lambda x: x * x - 2.0, 0.0, 2.0)
    assert r == 1.414213562373095
    assert abs(r - math.sqrt(2.0)) <= 2.3e-16

    r2 = sr.find_root(math.cos, 1.0, 2.0)
    assert abs(r2 - (math.pi / 2.0)) <= 2.3e-16

    r3 = sr.find_root(lambda x: math.exp(x) - 5.0, 0.0, 10.0)
    assert abs(r3 - math.log(5.0)) <= 4.5e-16


def test_signed_zero_is_positive_zero():
    for r in (
        sr.find_root(lambda x: x, -1, 1),
        sr.find_root(lambda x: -x, -2.0, -0.0),
        sr.find_root(lambda x: x, -1, 0),
    ):
        assert r == 0.0
        assert math.copysign(1.0, r) == 1.0


def test_cost_and_step_function_location():
    calls = 0

    def f(x):
        nonlocal calls
        calls += 1
        return 1.0 if x > 1e-310 else -1.0

    r = sr.find_root(f, -1e300, 1e300)
    assert calls <= 66
    assert abs(r - 1e-310) <= 5e-324

    calls2 = 0

    def g(x):
        nonlocal calls2
        calls2 += 1
        return x - 0.5

    assert sr.find_root(g, 0.0, 1.0) == 0.5
    assert calls2 <= 66


def test_jump_function_tie_rule_lower_end():
    r = sr.find_root(lambda x: 1.0 if x > 0.3 else -1.0, -1.0, 1.0)
    assert r == 0.3


def test_find_roots_published_behaviour():
    roots = sr.find_roots(math.sin, -0.5, 10.0, 50)
    target = (0.0, math.pi, 2 * math.pi, 3 * math.pi)
    assert len(roots) == 4
    for a, b in zip(roots, target):
        assert abs(a - b) <= 1e-15

    def poly(x):
        return (x - 1) * (x - 2) * (x - 3)

    assert sr.find_roots(poly, 0, 4, 4) == (1.0, 2.0, 3.0)
    assert sr.find_roots(poly, 0, 4, 3) == (1.0, 2.0, 3.0)

    one = sr.find_roots(poly, 0, 4, 1)
    assert len(one) == 1 and one[0] in (1.0, 2.0, 3.0)

    assert sr.find_roots(lambda x: x * x + 1, -1, 1, 10) == ()
    assert sr.find_roots(lambda x: x * x - 0.25, -1, 1, 1) == ()
    assert sr.find_roots(lambda x: x * x - 0.25, -1, 1, 4) == (-0.5, 0.5)
    assert sr.find_roots(lambda x: x - 1.5, 1, 2, 7) == (1.5,)
    assert sr.find_roots(lambda x: x, 1.0, math.nextafter(1.0, 2.0), 5) == ()
    assert sr.find_roots(lambda x: x - 1.0, 1.0, 2.0, 3) == (1.0,)
    assert sr.find_roots(lambda x: x - 2.0, 1.0, 2.0, 3) == (2.0,)
