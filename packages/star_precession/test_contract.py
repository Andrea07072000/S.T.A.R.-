"""Refusals of star_precession with hostile inputs (NaN, inf, huge integers, booleans, text, wrong shapes, dates outside
1800-2200).
Verifies: R4 (README).

Every function returns finite floats or raises ValueError: the polynomial is not extrapolated."""
import math
from fractions import Fraction

import pytest

import star_precession as p

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e150, -1e150, True, False, "2451545", None, 1j, [2451545.0], (1.0,)]
BAD_VEC = [None, 5, "abc", b"abc", (1, 2), (1, 2, 3, 4), [], {0: 1, 1: 2, 2: 3}, {1, 2, 3}, iter([1, 2, 3]), [1, 2, "3"], [1, 2, None],
           [1, 2, float("nan")], [float("inf"), 0, 0], [1, True, 0], [[1], [2], [3]], [10 ** 400, 0, 0]]
D, V = 2460000.5, (1.0, 2.0, 3.0)


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(BAD_VEC) == 17 and p.__version__ == "0.1.0"
    assert p.__all__ == ["precession_matrix", "mod_from_j2000", "j2000_from_mod", "precession_angles_arcsec"]
    assert (p.JD_MIN, p.JD_MAX, p.J2000) == (2378496.5, 2524593.5, 2451545.0)


def test_dates_refuse_every_hostile_value():
    for bad in BAD:
        for f in (p.precession_matrix, p.precession_angles_arcsec):
            for args in ((bad,), (D, bad), (bad, 0.0)):
                with pytest.raises(ValueError):
                    f(*args)
        for f in (p.mod_from_j2000, p.j2000_from_mod):
            for args in ((V, bad), (V, D, bad)):
                with pytest.raises(ValueError):
                    f(*args)


@pytest.mark.parametrize("bad", BAD_VEC, ids=lambda b: repr(b)[:20])
def test_vectors_that_are_not_three_finite_numbers_are_refused(bad):
    for f in (p.mod_from_j2000, p.j2000_from_mod):
        with pytest.raises(ValueError, match="three finite real numbers"):
            f(bad, D)


@pytest.mark.parametrize("args", [(2378496.4,), (2524593.6,), (2378496.5, -1e-3), (2524593.5, 1e-3), (0.0,), (-D,), (5e6,)])
def test_dates_outside_the_span_are_refused(args):
    for f in (p.precession_matrix, p.precession_angles_arcsec):
        with pytest.raises(ValueError, match="outside 1800-2200"):
            f(*args)
    for f in (p.mod_from_j2000, p.j2000_from_mod):
        with pytest.raises(ValueError, match="outside 1800-2200"):
            f(V, *args)


def test_limits_and_number_types_are_accepted():
    for day in (p.JD_MIN, p.JD_MAX, 2451545, Fraction(4903091, 2)):
        m = p.precession_matrix(day)
        assert isinstance(m, tuple) and all(type(x) is float and math.isfinite(x) for row in m for x in row)
        out = p.mod_from_j2000([1, 0, 0], day)
        assert isinstance(out, tuple) and all(type(x) is float for x in out)
    assert p.mod_from_j2000((9e149, -9e149, 9e149), D)[0] != 0 and all(map(math.isfinite, p.j2000_from_mod((9e149, -9e149, 9e149), D)))
    assert p.mod_from_j2000((0, 0, 0), D) == (0.0, 0.0, 0.0)
