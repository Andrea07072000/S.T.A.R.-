"""Refusals of star_sun with hostile inputs (NaN, inf, huge integers, booleans, text, wrong shapes, out-of-range dates).
Verifies: R5 (README).

Every function returns finite values or raises ValueError: never NaN, never another exception."""
import math
from fractions import Fraction

import pytest

import star_sun as s

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "1", None, 1j, [1.0], (1.0,)]
BAD_VEC = [None, 5, "abc", b"abc", (1, 2), (1, 2, 3, 4), [], {0: 1, 1: 2, 2: 3}, {1, 2, 3}, frozenset((1, 2, 3)), iter([1, 2, 3]),
           [1, 2, "3"], [1, 2, None], [1, 2, 1j], [1, 2, NAN], [INF, 0, 0], [1, True, 0], [[1], [2], [3]], [1e300, 0, 0], [10 ** 400, 0, 0]]
JD = 2453827.5


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(BAD_VEC) == 20 and s.__all__ == ["sun_vector_au", "sun_ra_dec_deg", "beta_angle_deg", "in_shadow"]
    assert (s.JD_1950, s.JD_2050, s.J2000, s.EARTH_RADIUS_KM, s.__version__) == (2433282.5, 2469807.5, 2451545.0, 6378.137, "0.1.0")


@pytest.mark.parametrize("f", [s.sun_vector_au, s.sun_ra_dec_deg])
def test_dates_refuse_every_hostile_value_and_the_years_outside_the_series(f):
    assert all(isinstance(v, float) and math.isfinite(v) for v in f(JD)) and f(JD) == f(JD, 0.0) == f(2453827, 0.5)
    for bad in BAD:
        for args in ((bad,), (JD, bad), (bad, 0.0)):
            with pytest.raises(ValueError):
                f(*args)
    for outside in ((2433282.4999,), (2469807.5001,), (2433282.5, -1e-6), (2469807.5, 1e-6), (0.0,), (-JD,), (2469807.0, 0.51)):
        with pytest.raises(ValueError, match="outside 1950-2050"):
            f(*outside)
    assert f(Fraction(4907655, 2)) == f(JD) and f(2433283.0, -0.5) == f(2433282.5)


@pytest.mark.parametrize("bad", BAD_VEC, ids=lambda b: repr(b)[:24])
def test_vectors_that_are_not_three_finite_numbers_are_refused(bad):
    with pytest.raises(ValueError):
        s.beta_angle_deg(bad, 50.0, 10.0)
    with pytest.raises(ValueError):
        s.in_shadow(bad, (1, 0, 0))
    with pytest.raises(ValueError):
        s.in_shadow((-7000, 0, 0), bad)


def test_scalars_refuse_every_hostile_value():
    for bad in BAD:
        with pytest.raises(ValueError):
            s.beta_angle_deg((1, 0, 0), bad, 10.0)
        with pytest.raises(ValueError):
            s.beta_angle_deg((1, 0, 0), 50.0, bad)
        with pytest.raises(ValueError):
            s.in_shadow((-7000, 0, 0), (1, 0, 0), bad)


@pytest.mark.parametrize("inc, raan", [(-1e-9, 0), (180.000001, 0), (90, 360.000001), (90, -360.000001)])
def test_orbit_angles_outside_their_range_are_refused(inc, raan):
    with pytest.raises(ValueError, match="must be within"):
        s.beta_angle_deg((1, 0, 0), inc, raan)


def test_limits_and_degenerate_geometry():
    assert s.beta_angle_deg((1, 0, 0), 0, 360) == 0.0 and s.beta_angle_deg((0, 0, -1), 180, -360) == 90.0
    assert s.beta_angle_deg((0, 0, 1e-300), 0.0, 0.0) == 90.0 and s.beta_angle_deg((0, 0, 9e299), 0, 0) == 90.0
    for zero in ((0, 0, 0), (0.0, -0.0, 0.0)):
        with pytest.raises(ValueError, match="zero vector"):
            s.beta_angle_deg(zero, 10, 10)
        with pytest.raises(ValueError, match="zero vector"):
            s.in_shadow((-7000, 0, 0), zero)
    for inside in ((0, 0, 0), (6378.136, 0, 0), (-3000, 3000, 3000)):
        with pytest.raises(ValueError, match="inside the body"):
            s.in_shadow(inside, (1, 0, 0))
    assert s.in_shadow((6378.137, 0, 0), (1, 0, 0)) is False                      # on the surface, day side
    for radius in (0, 0.0, -0.0, -1.0, -1e-300):
        with pytest.raises(ValueError, match="positive"):
            s.in_shadow((-7000, 0, 0), (1, 0, 0), radius)


def test_extreme_magnitudes_do_not_overflow_or_underflow():
    assert s.in_shadow((-9e299, 0, 0), (9e299, 0, 0)) is True and s.in_shadow((9e299, 9e299, 0), (9e299, 9e299, 9e299)) is False
    assert s.in_shadow((-1e-200, 0, 0), (1, 0, 0), 1e-300) is True and s.in_shadow((-1e-200, 1e-200, 0), (1, 0, 0), 1e-300) is False
    assert s.in_shadow((-7000, 0, 0), (5e-324, 0, 0)) is True
    u = s._unit((3e299, 4e299, 0.0), "v")
    assert u == pytest.approx((0.6, 0.8, 0.0), abs=1e-15) and s._unit((0.0, 0.0, -5e-324), "v") == (0.0, 0.0, -1.0)
    with pytest.raises(ValueError, match="^v is the zero vector"):
        s._unit((0.0, 0.0, 0.0), "v")
    with pytest.raises(ValueError, match="^r_sat must be a sequence of three numbers$"):
        s.in_shadow(5, (1, 0, 0))
