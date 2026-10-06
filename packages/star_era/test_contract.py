"""Refusals of star_era with hostile inputs (NaN, inf, huge integers, booleans, text, dates outside 1800-2200).
Verifies: R4 (README).

Every function returns a finite angle in [0, 360) or raises ValueError: a date outside the span is not extrapolated."""
import math
from fractions import Fraction

import pytest

import star_era as s

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "2451545", None, 1j, [2451545.0], (1.0,)]
D = 2460000.5


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and s.__all__ == ["era_deg", "gmst06_deg"] and s.__version__ == "0.1.0"
    assert (s.JD_MIN, s.JD_MAX) == (2378496.5, 2524593.5) and len(s.GMST_POLY) == 6


def test_every_argument_refuses_every_hostile_value():
    for bad in BAD:
        for args in ((bad,), (D, bad), (bad, 0.0)):
            with pytest.raises(ValueError):
                s.era_deg(*args)
        for i in range(4):
            args = [D, 0.1, D, 0.1008]
            args[i] = bad
            with pytest.raises(ValueError):
                s.gmst06_deg(*args)


@pytest.mark.parametrize("day, frac", [(2378496.4, 0.0), (2524593.6, 0.0), (2378496.5, -1e-3), (2524593.5, 1e-3), (0.0, 0.0), (-D, 0.0), (D, 1e6), (5e6, 0.0)])
def test_dates_outside_the_span_are_refused(day, frac):
    with pytest.raises(ValueError, match="UT1 date outside 1800-2200"):
        s.era_deg(day, frac)
    with pytest.raises(ValueError, match="UT1 date outside 1800-2200"):
        s.gmst06_deg(day, frac, D, 0.0)
    with pytest.raises(ValueError, match="TT date outside 1800-2200"):
        s.gmst06_deg(D, 0.0, day, frac)


def test_limits_and_number_types_are_accepted():
    for day in (s.JD_MIN, s.JD_MAX, 2451545, Fraction(4903091, 2)):
        out = s.era_deg(day)
        assert type(out) is float and 0.0 <= out < 360.0
        g = s.gmst06_deg(day, 0, day, 0)
        assert type(g) is float and 0.0 <= g < 360.0
    assert s.era_deg(2451545) == s.era_deg(2451545.0) and s.era_deg(s.JD_MAX - 1, 1.0) == pytest.approx(s.era_deg(s.JD_MAX), abs=1e-9)
    assert math.isfinite(s._era_turns(2451545.0, 0.0)) and 0.0 <= s._era_turns(0.3, 2451545.0) < 1.0
