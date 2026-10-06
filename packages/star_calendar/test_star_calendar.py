"""star_calendar against published day numbers and the structure of the two calendars.
Verifies: R1, R2, R3 (README).

Published (Meeus, Astronomical Algorithms, chapter 7, and the definition of the Julian period): noon of -4712-01-01
(Julian) is JD 0; 333-01-27 (Julian) noon is JD 1842713; 1582-10-04 (Julian) is followed by 1582-10-15 (Gregorian),
JD 2299161 at noon; 1957-10-04 noon is JD 2436116 (Sputnik 1, a Friday); 2000-01-01 noon is JD 2451545 (a Saturday).
The comparison with ERFA, CPython datetime and NAIF SPICE on 9014 dates is in crosscheck_calendar.py."""
import datetime

import pytest

import star_calendar as c


@pytest.mark.parametrize("date, calendar, jdn", [
    ((-4712, 1, 1), "julian", 0), ((-4712, 1, 1), "auto", 0), ((333, 1, 27), "julian", 1842713), ((333, 1, 27), "auto", 1842713),
    ((1582, 10, 4), "auto", 2299160), ((1582, 10, 15), "auto", 2299161), ((1582, 10, 15), "gregorian", 2299161),
    ((1582, 10, 5), "julian", 2299161), ((1957, 10, 4), "auto", 2436116), ((2000, 1, 1), "auto", 2451545), ((2000, 1, 1), "gregorian", 2451545),
    ((9999, 12, 31), "gregorian", 5373484), ((1858, 11, 17), "auto", 2400001)])
def test_published_day_numbers_both_ways(date, calendar, jdn):
    assert c.jdn(*date, calendar) == jdn and c.calendar_date(jdn, calendar) == date
    assert type(c.jdn(*date, calendar)) is int and all(type(v) is int for v in c.calendar_date(jdn, calendar))


def test_weekdays_of_known_dates():
    assert c.weekday(c.jdn(1957, 10, 4)) == 4 and c.weekday(c.jdn(2000, 1, 1)) == 5         # Friday, Saturday
    assert c.weekday(c.jdn(1582, 10, 4)) == 3 and c.weekday(c.jdn(1582, 10, 15)) == 4       # Thursday was followed by Friday
    assert c.weekday(0) == 0 and [c.weekday(n) for n in range(7, 14)] == list(range(7))
    for d in (datetime.date(1970, 1, 1), datetime.date(2026, 10, 6), datetime.date(2400, 2, 29)):
        assert c.weekday(c.jdn(d.year, d.month, d.day, "gregorian")) == d.weekday()


@pytest.mark.parametrize("calendar, start, days", [("gregorian", 2415021, 1500), ("julian", 0, 1500), ("julian", 2299000, 800),
                                                   ("gregorian", 2299000, 800), ("auto", 2298900, 600), ("gregorian", 5373484 - 800, 801)])
def test_every_day_number_has_one_date_and_dates_follow_each_other(calendar, start, days):
    previous = None
    for n in range(start, start + days):
        y, m, d = c.calendar_date(n, calendar)
        assert c.jdn(y, m, d, calendar) == n
        if previous is not None:
            py, pm, pd = previous
            same_month = (y, m) == (py, pm) and d == pd + 1
            new_month = d == 1 and ((y, m) == (py, pm + 1) or (y, m) == (py + 1, 1) and pm == 12)
            switch = calendar == "auto" and previous == (1582, 10, 4) and (y, m, d) == (1582, 10, 15)
            assert same_month or new_month or switch
        previous = (y, m, d)


def test_leap_years_of_the_two_calendars():
    for year, greg, jul in ((1600, True, True), (1700, False, True), (1900, False, True), (2000, True, True), (2023, False, False),
                            (2024, True, True), (2100, False, True), (0, True, True), (-4, True, True), (-100, False, True)):
        for calendar, leap in (("gregorian", greg), ("julian", jul)):
            assert c.jdn(year, 3, 1, calendar) - c.jdn(year, 2, 28, calendar) == (2 if leap else 1)
            assert c.day_of_year(year, 12, 31, calendar) == (366 if leap else 365)
    assert c.jdn(1900, 3, 1, "julian") - c.jdn(1900, 3, 1, "gregorian") == 13 and c.jdn(1582, 10, 15, "julian") - c.jdn(1582, 10, 15, "gregorian") == 10


def test_the_year_1582_had_355_days():
    assert c.day_of_year(1582, 10, 4) == 277 and c.day_of_year(1582, 10, 15) == 278 and c.day_of_year(1582, 12, 31) == 355
    assert c.day_of_year(1582, 12, 31, "gregorian") == 365 and c.day_of_year(1582, 12, 31, "julian") == 365
    assert c.day_of_year(2024, 1, 1) == 1 and c.day_of_year(2024, 3, 1) == 61 and c.day_of_year(1500, 3, 1) == 61   # 1500: leap in the Julian calendar


def test_julian_date_pair_keeps_the_time_of_day():
    day, frac = c.julian_date(2000, 1, 1, 12)
    assert (day, frac) == (2451544.5, 0.5) and day + frac == 2451545.0
    assert c.julian_date(1957, 10, 4, 19, 26, 24) == (2436115.5, (19 * 3600 + 26 * 60 + 24) / 86400)      # Meeus: 1957 Oct 4.81 = 2436116.31
    assert abs(sum(c.julian_date(1957, 10, 4, 19, 26, 24)) - 2436116.31) < 1e-9
    assert c.julian_date(2026, 10, 6) == (c.jdn(2026, 10, 6) - 0.5, 0.0)
    a, b = c.julian_date(2026, 10, 6, 23, 59, 59.999999)
    assert a == 2461319.5 and 0.99999 < b < 1.0 and b == (86399.999999) / 86400
    assert c.julian_date(2026, 10, 6, 0, 0, 1e-9)[1] == 1e-9 / 86400              # a nanosecond is not lost in the pair
