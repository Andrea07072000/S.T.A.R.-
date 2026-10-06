"""Guard tests of star_quadrature written by the reviewer: they decide the internal steps the drafted tests reach
only through the final result. Expected values are derived by hand in the comments; none comes from the module."""
import math
from fractions import Fraction as F

import pytest

import star_quadrature as sq


def nearest_to_sqrt(x: float, q: F) -> bool:
    """True when x is the float nearest to sqrt(q): q lies between the squares of the two midpoints around x."""
    half = F(math.ulp(x)) / 2
    return (F(x) - half) ** 2 < q < (F(x) + half) ** 2


def test_nearest_to_sqrt_is_a_real_check():
    assert nearest_to_sqrt(math.sqrt(2.0), F(2)) and not nearest_to_sqrt(math.nextafter(math.sqrt(2.0), 2.0), F(2))
    assert not nearest_to_sqrt(math.nextafter(math.sqrt(2.0), 0.0), F(2)) and nearest_to_sqrt(1.5, F(9, 4))


def test_exact_coefficients_of_the_first_polynomials():
    assert sq._coefficients(0) == (F(1),)
    assert sq._coefficients(1) == (F(1), F(0))
    assert sq._coefficients(2) == (F(3, 2), F(0), F(-1, 2))                         # (3x^2 - 1)/2
    assert sq._coefficients(3) == (F(5, 2), F(0), F(-3, 2), F(0))                   # (5x^3 - 3x)/2
    assert sq._coefficients(4) == (F(35, 8), F(0), F(-30, 8), F(0), F(3, 8))        # (35x^4 - 30x^2 + 3)/8
    assert sq._coefficients(5) == (F(63, 8), F(0), F(-70, 8), F(0), F(15, 8), F(0))  # (63x^5 - 70x^3 + 15x)/8
    for n in range(33):                                                             # P_n(1) = 1: the coefficients sum to 1
        assert sum(sq._coefficients(n)) == 1 and len(sq._coefficients(n)) == n + 1


def test_integer_polynomials_keep_roots_and_signs():
    assert sq._integers(1) == (1, 0)
    assert sq._integers(2) == (3, 0, -1)
    assert sq._integers(3) == (5, 0, -3, 0)
    assert sq._integers(4) == (35, 0, -30, 0, 3)
    assert sq._integers(5) == (63, 0, -70, 0, 15, 0)
    assert all(type(c) is int for c in sq._integers(7)) and sq._integers(7)[0] > 0


def test_sign_of_an_integer_polynomial_at_a_fraction():
    p2 = (3, 0, -1)                                                                 # 3x^2 - 1
    assert sq._sign(p2, F(1, 2)) == -1                                              # 3/4 - 1
    assert sq._sign(p2, F(3, 4)) == 1                                               # 27/16 - 1
    assert sq._sign(p2, F(0)) == -1 and sq._sign(p2, F(1)) == 1
    assert sq._sign((2, -3), F(3, 2)) == 0                                          # 2x - 3 at 3/2
    assert sq._sign((2, -3), F(7, 5)) == -1 and sq._sign((2, -3), F(8, 5)) == 1     # 14/5 - 3, 16/5 - 3
    assert sq._sign((1, -1, -1), F(5, 3)) == 1                                      # 25/9 - 15/9 - 9/9 = 1/9
    assert sq._sign((1, -1, -1), F(8, 5)) == -1                                     # 64/25 - 40/25 - 25/25 = -1/25
    assert sq._sign((1, 1, 1, -4), F(11, 10)) == -1                                 # 1.331 + 1.21 + 1.1 - 4 = -0.359
    assert sq._sign((1, 1, 1, -3), F(11, 10)) == 1                                  # 0.641


def test_float_positions_are_consecutive():
    assert sq._bits(0.0) == 0 and sq._bits(5e-324) == 1 and sq._bits(1.0) == 0x3FF0000000000000
    for x in (0.0, 5e-324, 0.25, 1.0 / 3.0, 0.999, 1.0):
        assert sq._float(sq._bits(x)) == x
        assert sq._bits(math.nextafter(x, 2.0)) == sq._bits(x) + 1
    assert sq._float(1) == 5e-324 and sq._float(0x3FF0000000000000) == 1.0


def test_root_is_the_nearest_float_in_both_directions():
    assert sq._root((3, -1), 0.0, 1.0) == 1.0 / 3.0                                 # float(1/3) lies below 1/3
    assert sq._root((3, -2), 0.0, 1.0) == 2.0 / 3.0                                 # float(2/3) lies above 2/3
    assert sq._root((-3, 1), 0.0, 1.0) == 1.0 / 3.0 and sq._root((-3, 2), 0.0, 1.0) == 2.0 / 3.0   # decreasing polynomials
    for k in range(1, 40):
        if k % 7:
            assert sq._root((7, -k), 0.0, 8.0) == k / 7                             # a correctly rounded division
    assert sq._root((4, -3), 0.0, 1.0) == 0.75 and sq._root((2, -1), 0.25, 1.0) == 0.5   # a root that is a float is returned exactly
    assert sq._root((4, -1), 0.125, 1.0) == 0.25
    assert sq._root((1, 0, -2), 1.0, 2.0) == math.sqrt(2.0)                         # math.sqrt is correctly rounded
    assert sq._root((1, 0, -3), 1.0, 2.0) == math.sqrt(3.0)
    assert nearest_to_sqrt(sq._root((3, 0, -1), 0.0, 1.0), F(1, 3))


def test_positive_roots_interlace():
    assert sq._positive_roots(0) == () and sq._positive_roots(1) == ()
    assert len(sq._positive_roots(2)) == 1 and nearest_to_sqrt(sq._positive_roots(2)[0], F(1, 3))
    assert len(sq._positive_roots(3)) == 1 and nearest_to_sqrt(sq._positive_roots(3)[0], F(3, 5))
    r4 = sq._positive_roots(4)                                                      # x^2 = (15 -+ 2 sqrt 30)/35
    assert r4 == pytest.approx((math.sqrt((15 - 2 * math.sqrt(30)) / 35), math.sqrt((15 + 2 * math.sqrt(30)) / 35)), abs=2e-16)
    for n in range(2, 33):
        low, high = sq._positive_roots(n - 1), sq._positive_roots(n)
        assert len(high) == n // 2 and all(0.0 < r < 1.0 for r in high) and list(high) == sorted(high)
        cuts = ((0.0,) if n % 2 == 0 else ()) + low + (1.0,)
        assert all(cuts[k] < high[k] < cuts[k + 1] for k in range(len(high)))       # exactly one root between consecutive cuts


def test_rules_in_closed_form():
    assert sq.gauss_legendre(1) == ((0.0,), (2.0,))
    x, w = sq.gauss_legendre(2)
    assert len(x) == 2 and x[0] == -x[1] and nearest_to_sqrt(x[1], F(1, 3)) and w == (1.0, 1.0)
    x, w = sq.gauss_legendre(3)
    assert len(x) == 3 and x[0] == -x[2] and x[1] == 0.0 and nearest_to_sqrt(x[2], F(3, 5)) and w == (5 / 9, 8 / 9, 5 / 9)
    x, w = sq.gauss_legendre(4)                                                     # weights (18 -+ sqrt 30)/36
    assert w == pytest.approx(((18 - math.sqrt(30)) / 36, (18 + math.sqrt(30)) / 36, (18 + math.sqrt(30)) / 36, (18 - math.sqrt(30)) / 36), abs=2e-16)
    x, w = sq.gauss_legendre(5)                                                     # centre 128/225; (322 -+ 13 sqrt 70)/900
    assert w[2] == 128 / 225 and x[2] == 0.0 and math.copysign(1.0, x[2]) == 1.0
    assert w == pytest.approx(((322 - 13 * math.sqrt(70)) / 900, (322 + 13 * math.sqrt(70)) / 900, 128 / 225, (322 + 13 * math.sqrt(70)) / 900,
                               (322 - 13 * math.sqrt(70)) / 900), abs=2e-16)
    assert x[4] == pytest.approx(math.sqrt(5 + 2 * math.sqrt(10 / 7)) / 3, abs=2e-16) and x[3] == pytest.approx(math.sqrt(5 - 2 * math.sqrt(10 / 7)) / 3, abs=2e-16)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 24, 32])
def test_every_weight_is_the_exact_formula_at_the_node(n):
    """w = 2 / ((1 - x^2) P_n'(x)^2), with P_n' from the exact coefficients written here and the node refined by Newton steps."""
    coeffs = sq._coefficients(n)
    nodes, weights = sq.gauss_legendre(n)
    assert len(nodes) == n and len(weights) == n
    for node, weight in zip(nodes, weights):
        x = F(node)
        for _ in range(2):                                                          # two Newton steps, kept to 300 binary digits
            p = sum(c * x ** (n - i) for i, c in enumerate(coeffs))
            dp = sum((n - i) * c * x ** (n - i - 1) for i, c in enumerate(coeffs[:-1]))
            x = F(round((x - p / dp) * 2 ** 300), 2 ** 300)
        dp = sum((n - i) * c * x ** (n - i - 1) for i, c in enumerate(coeffs[:-1]))
        exact = 2 / ((1 - x * x) * dp * dp)
        assert abs(F(weight) - exact) <= abs(exact) * F(1, 2 ** 52)                 # within one unit of the last place
        assert abs(F(node) - x) <= F(math.ulp(node) if node else 5e-324) / 2        # the node is the nearest float
    assert nodes == tuple(-v for v in reversed(nodes)) and weights == tuple(reversed(weights))
    assert all(math.copysign(1.0, v) == 1.0 for v in nodes if v == 0.0)


def test_legendre_small_orders_everywhere():
    for x in (-1.0, -0.75, -0.3, 0.0, 0.2, 0.5, 0.9, 1.0):
        assert sq.legendre(0, x) == (1.0, 0.0)
        assert sq.legendre(1, x) == (x, 1.0)
        assert sq.legendre(2, x) == pytest.approx(((3 * x * x - 1) / 2, 3 * x), rel=1e-14, abs=1e-15)
        assert sq.legendre(3, x) == pytest.approx(((5 * x ** 3 - 3 * x) / 2, (15 * x * x - 3) / 2), rel=1e-14, abs=1e-15)
        assert sq.legendre(4, x) == pytest.approx(((35 * x ** 4 - 30 * x * x + 3) / 8, (140 * x ** 3 - 60 * x) / 8), rel=1e-14, abs=1e-15)
        assert sq.legendre(5, x) == pytest.approx(((63 * x ** 5 - 70 * x ** 3 + 15 * x) / 8, (315 * x ** 4 - 210 * x * x + 15) / 8), rel=1e-14, abs=1e-15)
    for n in (1, 3, 5, 31):                                                         # an odd order vanishes at 0 as +0.0
        assert sq.legendre(n, 0.0)[0] == 0.0 and math.copysign(1.0, sq.legendre(n, 0.0)[0]) == 1.0
    for n in (2, 4, 32):                                                            # the derivative of an even order vanishes at 0 as +0.0
        assert sq.legendre(n, 0.0)[1] == 0.0 and math.copysign(1.0, sq.legendre(n, 0.0)[1]) == 1.0
    for n in range(33):
        exact = sum(c * F(3, 8) ** (n - i) for i, c in enumerate(sq._coefficients(n)))
        dexact = sum((n - i) * c * F(3, 8) ** (n - i - 1) for i, c in enumerate(sq._coefficients(n)[:-1])) if n else F(0)
        assert sq.legendre(n, 0.375) == pytest.approx((float(exact), float(dexact)), rel=1e-13, abs=1e-14)


def test_integrate_maps_the_rule_onto_the_interval():
    seen = []
    assert sq.integrate(lambda t: seen.append(t) or 1.0, 10.0, 14.0, 3) == pytest.approx(4.0, abs=1e-15)
    assert seen == pytest.approx([12.0 - 2.0 * math.sqrt(0.6), 12.0, 12.0 + 2.0 * math.sqrt(0.6)], abs=1e-14) and seen[1] == 12.0
    assert sq.integrate(lambda t: t, 10.0, 14.0, 1) == 48.0                         # 4 * 12
    assert sq.integrate(lambda t: t, 14.0, 10.0, 1) == -48.0
    assert sq.integrate(lambda t: t * t * t, -2.0, 6.0, 2) == pytest.approx(320.0, abs=1e-12)   # (1296 - 16)/4
    assert sq.integrate(lambda t: 3 * t * t, -5.0, -1.0, 2) == pytest.approx(124.0, abs=1e-12)  # -1 + 125
    assert sq.integrate(lambda t: 1, -1e150, 1e150, 1) == 2e150 and sq.integrate(lambda t: 2.5, 7.0, 7.0, 4) == 0.0
    with pytest.raises(ValueError, match="overflows"):
        sq.integrate(lambda t: 1e300, -1e150, 1e150, 1)
    with pytest.raises(ValueError, match="finite real"):
        sq.integrate(lambda t: math.inf if t > 0.5 else 1.0, 0.0, 1.0, 2)           # only the last point is refused
    with pytest.raises(ValueError, match="finite real"):
        sq.integrate(lambda t: math.nan if t < 0.5 else 1.0, 0.0, 1.0, 2)           # only the first
