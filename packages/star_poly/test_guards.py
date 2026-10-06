"""Guard tests of star_poly written by the reviewer after the first mutation run (0.548 on the previous core).

They decide the lines the drafted tests left open: the exact root count of shifted and scaled cubics, the choice of
the nearer float, the ordering of the floats used by the bisection, and the separation of roots by the turning points.
Expected values are derived by hand in the comments; none is taken from the module itself.
"""
import math
from fractions import Fraction

import pytest

import star_poly as sp


def expand(roots, lead):
    """Coefficients of lead * prod(x - r), highest power first; exact for small integers."""
    cs = [Fraction(lead)]
    for r in roots:
        cs = [a - Fraction(r) * b for a, b in zip(cs + [Fraction(0)], [Fraction(0)] + cs)]
    return [float(c) for c in cs]


# ---- the order of the floats ------------------------------------------------------------------------------------------

def test_rank_orders_the_floats_and_unrank_inverts_it():
    xs = [-1e60, -2.5, -1.0, -5e-324, 0.0, 5e-324, 1.0, 1.5, 2.5, 1e60]
    ranks = [sp._rank(x) for x in xs]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
    assert sp._rank(0.0) == 0 and sp._rank(-0.0) == 0
    assert sp._rank(5e-324) == 1 and sp._rank(-5e-324) == -1
    assert sp._rank(1.0) == 0x3FF0000000000000 and sp._rank(-1.0) == -0x3FF0000000000000
    for x in xs:
        assert sp._unrank(sp._rank(x)) == x
        assert sp._rank(math.nextafter(x, math.inf)) == sp._rank(x) + 1      # neighbouring floats are one position apart
    assert sp._unrank(1) == 5e-324 and sp._unrank(-1) == -5e-324 and sp._unrank(0) == 0.0


def test_sign_is_exact_also_where_floats_cancel():
    one = (Fraction(1), Fraction(-2), Fraction(1))                          # (x - 1)^2
    assert sp._sign(one, 1.0) == 0
    assert sp._sign(one, math.nextafter(1.0, 2.0)) == 1                     # 4.9e-32: a float evaluation returns 0
    assert sp._sign((Fraction(1), Fraction(0), Fraction(-2)), 1.5) == 1     # 2.25 - 2
    assert sp._sign((Fraction(1), Fraction(0), Fraction(-2)), 1.25) == -1   # 1.5625 - 2
    assert sp._sign((Fraction(-1), Fraction(3)), Fraction(7, 2)) == -1      # -3.5 + 3: fractions accepted, order of Horner
    assert sp._sign((Fraction(2), Fraction(3), Fraction(5)), 2.0) == 1      # 8 + 6 + 5 = 19
    assert sp._sign((Fraction(2), Fraction(3), Fraction(-14)), 2.0) == 0     # 8 + 6 - 14
    assert sp._sign((Fraction(2), Fraction(3), Fraction(-15)), 2.0) == -1


# ---- one root inside a bracket ----------------------------------------------------------------------------------------

LINE = (Fraction(1), Fraction(-3))                                          # x - 3


def test_between_returns_an_end_that_is_a_root():
    assert sp._between(LINE, 3.0, 10.0) == 3.0
    assert sp._between(LINE, -10.0, 3.0) == 3.0
    assert sp._between(LINE, -1.0, 100.0) == 3.0                            # found inside, exactly
    assert sp._between((Fraction(-1), Fraction(3)), -1.0, 100.0) == 3.0     # decreasing polynomial: the other sign at lo
    assert sp._between((Fraction(1), Fraction(3)), -100.0, 1.0) == -3.0     # negative root, bracket across zero
    assert sp._between((Fraction(1), Fraction(0)), -1.0, 4.0) == 0.0


def test_between_returns_the_nearer_of_the_two_enclosing_floats():
    third = (Fraction(3), Fraction(-1))                                     # root 1/3: not a float; float(1/3) is BELOW 1/3
    assert sp._between(third, 0.0, 1.0) == 1.0 / 3.0
    assert sp._between((Fraction(-3), Fraction(1)), 0.0, 1.0) == 1.0 / 3.0
    assert sp._between((Fraction(3), Fraction(1)), -1.0, 0.0) == -1.0 / 3.0
    two_thirds = (Fraction(3), Fraction(-2))                                # float(2/3) is ABOVE 2/3
    assert sp._between(two_thirds, 0.0, 1.0) == 2.0 / 3.0
    assert sp._between((Fraction(3), Fraction(2)), -1.0, 0.0) == -2.0 / 3.0
    for n in range(1, 60):                                                  # n/7 correctly rounded, both directions occur
        if n % 7:
            assert sp._between((Fraction(7), Fraction(-n)), 0.0, 10.0) == n / 7
            assert sp._between((Fraction(7), Fraction(n)), -10.0, 0.0) == -n / 7


def test_square_roots_are_correctly_rounded():
    for n in (2, 3, 5, 6, 7, 10, 11, 13, 17, 19, 23, 1e-10, 3e20, 0.7):     # math.sqrt is correctly rounded (IEEE 754)
        assert sp.quadratic_roots(1.0, 0.0, -n) == (-math.sqrt(n), math.sqrt(n))
        assert sp.quadratic_roots(-3.0, 0.0, 3.0 * n) == (-math.sqrt(n), math.sqrt(n)) or 3.0 * n != Fraction(3) * Fraction(n)
    assert sp.cubic_roots(1.0, 0.0, 0.0, -2.0) == (2.0 ** (1.0 / 3.0),) or sp.cubic_roots(1.0, 0.0, 0.0, -2.0) == (math.cbrt(2.0),)
    assert sp.cubic_roots(1.0, 0.0, 0.0, -27.0) == (3.0,) and sp.cubic_roots(1.0, 0.0, 0.0, 27.0) == (-3.0,)


# ---- quadratics -------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("r1,r2,lead", [(1, 2, 1), (-7, 3, 2), (-9, -4, -3), (0, 5, 1), (-5, 0, 4), (100, 101, 1), (-1000, 1000, 7), (3, 1024, -1)])
def test_quadratic_from_integer_roots(r1, r2, lead):
    assert sp.quadratic_roots(*expand([r1, r2], lead)) == (float(r1), float(r2))


def test_quadratic_double_root_away_from_zero_and_scaled():
    assert sp.quadratic_roots(*expand([7, 7], 3)) == (7.0,)                 # 3x^2 - 42x + 147
    assert sp.quadratic_roots(*expand([-6, -6], -5)) == (-6.0,)
    assert sp.quadratic_roots(4.0, 4.0, 1.0) == (-0.5,)                     # (2x + 1)^2: vertex -b/(2a) = -0.5
    assert sp.quadratic_roots(1.0, 0.0, 0.0) == (0.0,) and math.copysign(1.0, sp.quadratic_roots(-1.0, 0.0, 0.0)[0]) == 1.0
    assert sp.quadratic_roots(3.0, -42.0, 148.0) == ()                      # discriminant 1764 - 1776 = -12
    assert sp.quadratic_roots(3.0, -42.0, 146.0) != () and len(sp.quadratic_roots(3.0, -42.0, 146.0)) == 2   # +12
    assert sp.quadratic_roots(1.0, 1.0, 0.25) == (-0.5,) and sp.quadratic_roots(1.0, 1.0, 0.26) == ()
    assert sp.quadratic_roots(2.0, 0.0, 0.0) == (0.0,) and sp.quadratic_roots(1.0, 0.0, 1e-300) == ()


def test_quadratic_roots_closer_than_one_float_are_two_neighbours():
    # (x - 1)^2 = 2^-120 has the roots 1 -+ 2^-60, both of which round to 1.0: two distinct floats are returned.
    # Built exactly: a = 2^120, b = -2^121, c = 2^120 - 1 is not a float, so use the symmetric x^2 = tiny around a float cut:
    got = sp.quadratic_roots(1.0, -2.0, 1.0 - 2.0 ** -53)                   # c = the float just below 1: roots 1 -+ 2^-26.5
    assert len(got) == 2 and got[0] < 1.0 < got[1]
    assert got[0] == pytest.approx(1.0 - 2.0 ** -26.5, abs=1e-15) and got[1] == pytest.approx(1.0 + 2.0 ** -26.5, abs=1e-15)
    tiny = sp.quadratic_roots(1.0, 0.0, -5e-324)                            # roots -+ 2.2e-162: far from each other
    assert tiny == (-math.sqrt(5e-324), math.sqrt(5e-324))


def test_separated_distinct_roots_within_one_float_become_neighbours():
    # x (x - h) with h so small that both roots share the cut: the exact roots are 0 and 2^-1074 * 2^-0 ... forced by hand:
    coeffs = (Fraction(1), Fraction(-3, 10 ** 400), Fraction(2, 10 ** 800))  # roots 1e-400 and 2e-400: both round to 0.0
    got = sp._separated(coeffs, [1.5e-400 * 0.0])                           # the cut 0.0 is below both roots
    assert got == (0.0, 5e-324)
    assert all(math.copysign(1.0, r) == 1.0 for r in got)


def test_separated_uses_cuts_in_order_and_bounds_outside():
    coeffs = (Fraction(1), Fraction(-6), Fraction(11), Fraction(-6))        # roots 1, 2, 3
    assert sp._separated(coeffs, [1.5, 2.5]) == (1.0, 2.0, 3.0)
    assert sp._separated((Fraction(1), Fraction(-1000)), []) == (1000.0,)   # Cauchy: 1 + 1000; twice that encloses it
    assert sp._separated((Fraction(1, 1000), Fraction(-1)), []) == (1000.0,)  # the bound divides by the LEADING coefficient
    assert sp._separated((Fraction(2), Fraction(0), Fraction(-5000)), [0.0]) == (-50.0, 50.0)   # max over the other coefficients


# ---- cubics -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("roots,lead", [((1, 2, 3), 1), ((-5, 2, 9), 2), ((-9, -4, -1), -3), ((4, 5, 6), 7), ((-8, 0, 3), 1), ((10, 20, 40), -2),
                                        ((-100, 1, 1000), 5), ((1, 2, 1024), 3), ((-3, -2, 7), 1)])
def test_cubic_three_integer_roots_shifted_and_scaled(roots, lead):
    assert sp.cubic_roots(*expand(roots, lead)) == tuple(float(r) for r in roots)


@pytest.mark.parametrize("double,simple,lead", [(3, 5, 1), (5, 3, 1), (-1, 4, 2), (4, -1, -2), (7, -7, 3), (-6, -2, 1), (2, 9, -5), (10, 1, 4), (1, 0, 1), (0, 6, 2)])
def test_cubic_double_root_is_reported_once_at_its_exact_place(double, simple, lead):
    got = sp.cubic_roots(*expand([double, double, simple], lead))
    assert got == tuple(sorted((float(double), float(simple))))


@pytest.mark.parametrize("r,lead", [(1, 1), (-4, 2), (7, -3), (0, 5), (25, 1), (-13, -7)])
def test_cubic_triple_root(r, lead):
    assert sp.cubic_roots(*expand([r, r, r], lead)) == (float(r),)


@pytest.mark.parametrize("r,s,t,lead", [(2, 0, 1, 1), (-3, 2, 5, 2), (5, -4, 9, -1), (7, 1, 1, 3), (-11, 0, 4, -2), (1, 6, 10, 1)])
def test_cubic_single_real_root(r, s, t, lead):
    """lead (x - r)(x^2 + s x + t) with s^2 < 4 t: the quadratic factor has no real root."""
    assert s * s < 4 * t
    cs = [lead, lead * (s - r), lead * (t - r * s), -lead * r * t]
    assert sp.cubic_roots(*[float(c) for c in cs]) == (float(r),)


def test_cubic_count_changes_exactly_at_the_double_root():
    # x^3 - 3x + d: local maximum 2 + d at x = -1, local minimum d - 2 at x = 1. Three roots iff -2 < d < 2.
    assert len(sp.cubic_roots(1.0, 0.0, -3.0, 2.0)) == 2
    assert len(sp.cubic_roots(1.0, 0.0, -3.0, math.nextafter(2.0, 0.0))) == 3
    assert len(sp.cubic_roots(1.0, 0.0, -3.0, math.nextafter(2.0, 3.0))) == 1
    assert len(sp.cubic_roots(1.0, 0.0, -3.0, -2.0)) == 2
    assert len(sp.cubic_roots(1.0, 0.0, -3.0, math.nextafter(-2.0, 0.0))) == 3
    assert len(sp.cubic_roots(1.0, 0.0, -3.0, math.nextafter(-2.0, -3.0))) == 1
    three = sp.cubic_roots(1.0, 0.0, -3.0, math.nextafter(2.0, 0.0))        # two roots 1 -+ ~8.6e-9 around the turning point 1
    assert three[0] == pytest.approx(-2.0, abs=1e-15) and three[1] < 1.0 < three[2] and three[2] - three[1] < 1e-7
    # the same with a shift and a scale: 2 (x - 10)^3 - 6 (x - 10) + 4 = 2x^3 - 60x^2 + 594x - 1936 has the double root 11 and the root 8
    assert sp.cubic_roots(2.0, -60.0, 594.0, -1936.0) == (8.0, 11.0)
    assert len(sp.cubic_roots(2.0, -60.0, 594.0, -1936.5)) == 3 and len(sp.cubic_roots(2.0, -60.0, 594.0, -1935.5)) == 1


def test_cubic_three_roots_of_very_different_size():
    assert sp.cubic_roots(*expand([Fraction(1, 1024), 1, 1048576], 1)) == (1.0 / 1024.0, 1.0, 1048576.0)
    assert sp.cubic_roots(*expand([-1048576, Fraction(-1, 4096), 8], -2)) == (-1048576.0, -1.0 / 4096.0, 8.0)
    assert sp.cubic_roots(1.0, -1e60, 1e60, -1.0)[1:] == (1.0, 1e60)        # a valid cubic at the limit of the range


def test_results_are_positive_zero_floats_sorted():
    for got in (sp.cubic_roots(1.0, 0.0, -1.0, 0.0), sp.cubic_roots(-1.0, 0.0, 0.0, 0.0), sp.quadratic_roots(1.0, 3.0, 0.0), sp.cubic_roots(1.0, 3.0, 0.0, 0.0)):
        assert list(got) == sorted(got) and all(type(r) is float for r in got)
        assert all(math.copysign(1.0, r) == 1.0 for r in got if r == 0.0)
    assert sp.quadratic_roots(1.0, 3.0, 0.0) == (-3.0, 0.0) and sp.cubic_roots(1.0, 3.0, 0.0, 0.0) == (-3.0, 0.0)


def test_a_root_beyond_the_floats_is_refused():
    with pytest.raises(ValueError, match="overflows"):
        sp.quadratic_roots(5e-324, 1e60, 1.0)                               # the far root is -2e383
    with pytest.raises(ValueError, match="overflows"):
        sp.cubic_roots(5e-324, 0.0, 0.0, 1e60)                              # Cauchy's bound itself is beyond the floats
    assert sp._float(Fraction(1, 3)) == 1.0 / 3.0
    with pytest.raises(ValueError, match="overflows"):
        sp._float(Fraction(10) ** 400)
