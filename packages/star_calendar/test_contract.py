"""Refusals of star_calendar: dates that do not exist, non-integers, unknown calendars, times outside the day.
Verifies: R4 (README).

Every function returns integers (or the documented pair) or raises ValueError: a date is never rounded or wrapped."""
import math
from fractions import Fraction

import pytest

import star_calendar as c

NOT_INT = [1.0, 2.5, float("nan"), float("inf"), True, False, "1", None, 1j, [1], (1,), Fraction(1, 2), b"1"]
BAD_CAL = ["", "Gregorian", "GREGORIAN", "greg", "mixed", None, 1, ("auto",), b"auto"]


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(NOT_INT) == 13 and len(BAD_CAL) == 9 and c.__version__ == "0.1.0"
    assert c.CALENDARS == ("auto", "gregorian", "julian") and c.GREGORIAN_START_JDN == 2299161 and c.MAX_JDN == 5373484
    assert c.__all__ == ["jdn", "calendar_date", "julian_date", "weekday", "day_of_year", "CALENDARS"]


def test_non_integers_are_refused_everywhere():
    for bad in NOT_INT:
        for args in ((bad, 1, 1), (2000, bad, 1), (2000, 1, bad)):
            for f in (c.jdn, c.day_of_year, c.julian_date):
                with pytest.raises(ValueError):
                    f(*args)
        for f in (c.calendar_date, c.weekday):
            with pytest.raises(ValueError):
                f(bad)
        for kw in ({"hour": bad}, {"minute": bad}):
            with pytest.raises(ValueError):
                c.julian_date(2000, 1, 1, **kw)
    for bad in (float("nan"), float("inf"), True, "1", None, 1j, [1.0]):
        with pytest.raises(ValueError, match="second"):
            c.julian_date(2000, 1, 1, 0, 0, bad)


@pytest.mark.parametrize("bad", BAD_CAL, ids=repr)
def test_unknown_calendars_are_refused(bad):
    for call in (lambda: c.jdn(2000, 1, 1, bad), lambda: c.calendar_date(2451545, bad), lambda: c.day_of_year(2000, 1, 1, bad),
                 lambda: c.julian_date(2000, 1, 1, calendar=bad)):
        with pytest.raises(ValueError, match="calendar must be one of"):
            call()


@pytest.mark.parametrize("date, calendar", [
    ((2023, 2, 29), "auto"), ((1900, 2, 29), "gregorian"), ((2100, 2, 29), "auto"), ((2024, 2, 30), "auto"), ((2024, 4, 31), "auto"),
    ((2024, 1, 0), "auto"), ((2024, 1, 32), "auto"), ((2024, 0, 1), "auto"), ((2024, 13, 1), "auto"), ((2024, -1, 1), "auto"),
    ((2024, 1, -1), "auto"), ((1582, 10, 5), "auto"), ((1582, 10, 10), "auto"), ((1582, 10, 14), "auto"),
    ((-4713, 12, 31), "julian"), ((10000, 1, 1), "gregorian"), ((-5000, 1, 1), "auto")])
def test_dates_that_do_not_exist_are_refused(date, calendar):
    for f in (c.jdn, c.day_of_year, c.julian_date):
        with pytest.raises(ValueError):
            f(*date, calendar=calendar) if f is c.julian_date else f(*date, calendar)


def test_dates_that_exist_only_in_one_calendar():
    assert c.jdn(1900, 2, 29, "julian") == c.jdn(1900, 3, 13, "gregorian") and c.jdn(1500, 2, 29) == c.jdn(1500, 2, 29, "julian")
    assert c.jdn(1582, 10, 10, "gregorian") == c.jdn(1582, 9, 30, "julian") and c.jdn(1582, 10, 10, "julian") == 2299166
    with pytest.raises(ValueError, match=r"day must be within \[1, 28\] for 1900-02 in the Gregorian calendar"):
        c.jdn(1900, 2, 29, "gregorian")
    with pytest.raises(ValueError, match="do not exist in the civil calendar"):
        c.jdn(1582, 10, 9)


@pytest.mark.parametrize("n", [-1, -2299161, 5373485, 10 ** 30])
def test_day_numbers_outside_the_range_are_refused(n):
    for f in (c.calendar_date, c.weekday):
        with pytest.raises(ValueError, match="outside the valid range"):
            f(n)


def test_limits_are_accepted():
    assert c.calendar_date(0) == (-4712, 1, 1) and c.calendar_date(c.MAX_JDN) == (9999, 12, 31) and c.weekday(c.MAX_JDN) in range(7)
    assert c.calendar_date(c.GREGORIAN_START_JDN - 1) == (1582, 10, 4) and c.calendar_date(c.GREGORIAN_START_JDN) == (1582, 10, 15)
    assert c.jdn(-4712, 1, 1, "julian") == 0 and c.jdn(9999, 12, 31) == c.MAX_JDN and c.jdn(2000, 2, 29) == 2451604


@pytest.mark.parametrize("h, m, s", [(24, 0, 0), (-1, 0, 0), (0, 60, 0), (0, -1, 0), (0, 0, 60.0), (0, 0, -1e-9), (23, 59, 60)])
def test_times_outside_the_day_are_refused(h, m, s):
    with pytest.raises(ValueError, match="time of day"):
        c.julian_date(2000, 1, 1, h, m, s)


def test_the_fraction_never_reaches_one():
    day, frac = c.julian_date(2000, 1, 1, 23, 59, math.nextafter(60.0, 0.0))
    assert day == 2451544.5 and frac < 1.0 and type(frac) is float and type(day) is float
    assert c.julian_date(2000, 1, 1, 23, 59, Fraction(119, 2))[1] == (23 * 3600 + 59 * 60 + 59.5) / 86400
