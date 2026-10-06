"""Refusals of star_moon with hostile inputs (NaN, inf, huge integers, booleans, text, dates outside 1950-2050).
Verifies: R4 (README).

Every function returns finite floats or raises ValueError: the series is not extrapolated outside its century."""
import math
from fractions import Fraction

import pytest

import star_moon as m

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "2451545", None, 1j, [2451545.0], (1.0,)]
FUNCS = (m.moon_vector_km, m.moon_ra_dec_deg, m.moon_distance_km)


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and m.__all__ == ["moon_vector_km", "moon_ra_dec_deg", "moon_distance_km"] and m.__version__ == "0.1.0"
    assert (m.JD_1950, m.JD_2050, m.J2000) == (2433282.5, 2469807.5, 2451545.0)
    assert (len(m.LONGITUDE), len(m.LATITUDE), len(m.PARALLAX)) == (6, 4, 4)


@pytest.mark.parametrize("f", FUNCS, ids=lambda f: f.__name__)
def test_every_argument_refuses_every_hostile_value(f):
    for bad in BAD:
        for args in ((bad,), (2451545.0, bad), (bad, 0.0)):
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("f", FUNCS, ids=lambda f: f.__name__)
def test_dates_outside_the_century_are_refused(f):
    for args in ((2433282.4999,), (2469807.5001,), (2433282.5, -1e-6), (2469807.5, 1e-6), (0.0,), (-2451545.0,), (2469807.0, 0.51)):
        with pytest.raises(ValueError, match="outside 1950-2050"):
            f(*args)


@pytest.mark.parametrize("f", FUNCS, ids=lambda f: f.__name__)
def test_limits_and_number_types_are_accepted(f):
    for args in ((m.JD_1950,), (m.JD_2050,), (2451545,), (Fraction(4903091, 2),), (2469807.0, 0.5), (2433283.0, -0.5)):
        out = f(*args)
        values = out if isinstance(out, tuple) else (out,)
        assert all(type(v) is float and math.isfinite(v) for v in values)
    assert f(2451545) == f(2451545.0) == f(2451545.0, 0.0) and f(2469807.0, 0.5) == f(m.JD_2050)
