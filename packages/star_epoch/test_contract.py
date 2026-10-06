"""Refusals of star_epoch with hostile inputs (NaN, inf, huge integers, booleans, text, values outside their ranges).
Verifies: R4 (README).

Every function returns finite floats or raises ValueError: nothing is clamped silently."""
import math
from fractions import Fraction

import pytest

import star_epoch as ep

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "2000", None, 1j, [2000.0], (2000.0,)]
TO_EPOCH = [ep.julian_epoch, ep.besselian_epoch]
TO_DATE = [ep.jd_from_julian_epoch, ep.jd_from_besselian_epoch]


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and ep.__version__ == "0.1.0"
    assert ep.__all__ == ["julian_epoch", "besselian_epoch", "jd_from_julian_epoch", "jd_from_besselian_epoch"]
    assert (ep.JD_MIN, ep.JD_MAX, ep.EPOCH_MIN, ep.EPOCH_MAX) == (2086302.5, 2816787.5, 1000.0, 3000.0)
    assert (ep.J2000, ep.JULIAN_YEAR, ep.TROPICAL_YEAR, ep.B1900_MJD, ep.MJD0) == (2451545.0, 365.25, 365.242198781, 15019.81352, 2400000.5)


@pytest.mark.parametrize("f", TO_EPOCH, ids=lambda f: f.__name__)
def test_dates_refuse_every_hostile_value(f):
    assert type(f(2460000.5, 0.5)) is float and math.isfinite(f(2460000.5, 0.5))
    for bad in BAD:
        with pytest.raises(ValueError, match="jd_day"):
            f(bad)
        with pytest.raises(ValueError, match="jd_frac"):
            f(2460000.5, bad)
    for day in (2086302.4, 2816787.6, 0.0, 2026.0, -2460000.5):
        with pytest.raises(ValueError, match="jd_day"):
            f(day)
    for frac in (1.0000001, -1.0000001, 2460000.5):
        with pytest.raises(ValueError, match="jd_frac"):
            f(2460000.5, frac)


@pytest.mark.parametrize("f", TO_DATE, ids=lambda f: f.__name__)
def test_epochs_refuse_every_hostile_value(f):
    assert all(type(v) is float and math.isfinite(v) for v in f(2026.76))
    for bad in BAD + [999.9999999, 3000.0000001, 2451545.0, -2000.0, 0.0]:
        with pytest.raises(ValueError, match="epoch"):
            f(bad)


def test_limits_are_accepted():
    for f in TO_EPOCH:
        assert 999.0 < f(ep.JD_MIN, -1.0) < 1001.0 and 2999.0 < f(ep.JD_MAX, 1.0) < 3001.0
        assert f(2460000, Fraction(1, 2)) == f(2460000.5)
    for f in TO_DATE:
        assert 2086000.0 < sum(f(1000)) < 2087000.0 and 2816000.0 < sum(f(3000)) < 2817000.0
        assert f(Fraction(4001, 2)) == f(2000.5)
