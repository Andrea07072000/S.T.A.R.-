"""Guard tests of star_timecode written by the reviewer: every date of several years against an independent count,
each field at both ends of its range, and the shape of the text character by character."""
import pytest

import star_timecode as tc

LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


@pytest.mark.parametrize("year", [1, 4, 100, 400, 1900, 2000, 2023, 2024, 2100, 2400, 9996, 9999])
def test_every_day_of_the_year_counted_independently(year):
    count = 0
    for month in range(1, 13):
        last = LENGTHS[month - 1] + (1 if month == 2 and is_leap(year) else 0)
        for day in range(1, last + 1):
            count += 1
            assert tc.day_of_year(year, month, day) == count
            assert tc.month_day(year, count) == (month, day)
            a, b = tc.format_a(year, month, day, 0, 0, 0), tc.format_b(year, month, day, 0, 0, 0)
            assert a == "%04d-%02d-%02dT00:00:00Z" % (year, month, day) and b == "%04d-%03dT00:00:00Z" % (year, count)
            assert tc.parse(a) == (year, month, day, 0, 0, 0, "") and tc.parse(b) == (year, month, day, 0, 0, 0, "")
        with pytest.raises(ValueError, match="day"):
            tc.day_of_year(year, month, last + 1)
        with pytest.raises(ValueError, match="day"):
            tc.parse("%04d-%02d-%02dT00:00:00Z" % (year, month, last + 1))
        with pytest.raises(ValueError, match="day"):
            tc.format_a(year, month, 0, 0, 0, 0)
    assert count == (366 if is_leap(year) else 365)
    with pytest.raises(ValueError, match="day of year"):
        tc.month_day(year, count + 1)
    with pytest.raises(ValueError, match="day of year"):
        tc.parse("%04d-%03dT00:00:00Z" % (year, count + 1))
    with pytest.raises(ValueError, match="day of year"):
        tc.month_day(year, 0)


def test_time_fields_at_both_ends():
    assert tc.parse("2026-10-07T00:00:00Z")[3:] == (0, 0, 0, "") and tc.parse("2026-10-07T23:59:59Z")[3:] == (23, 59, 59, "")
    assert tc.format_a(2026, 10, 7, 23, 59, 59) == "2026-10-07T23:59:59Z" and tc.format_a(2026, 10, 7, 0, 0, 0) == "2026-10-07T00:00:00Z"
    assert tc.format_a(2026, 10, 7, 9, 8, 7, "06") == "2026-10-07T09:08:07.06Z" and tc.format_b(2026, 1, 9, 9, 8, 7, "0") == "2026-009T09:08:07.0Z"
    for bad, word in (((24, 0, 0), "hour"), ((-1, 0, 0), "hour"), ((0, 60, 0), "minute"), ((0, -1, 0), "minute"), ((0, 0, 60), "second"), ((0, 0, -1), "second"),
                      ((23, 59, 61), "second"), ((23, 58, 60), "second"), ((22, 59, 60), "second"), ((0, 59, 60), "second"), ((23, 0, 60), "second")):
        with pytest.raises(ValueError, match=word):
            tc.format_a(2026, 10, 7, *bad)
        with pytest.raises(ValueError, match=word):
            tc.format_b(2026, 10, 7, *bad)
    for text, word in (("2026-10-07T24:00:00Z", "hour"), ("2026-10-07T00:60:00Z", "minute"), ("2026-10-07T00:00:60Z", "second"), ("2026-10-07T23:59:61Z", "second"),
                       ("2026-10-07T22:59:60Z", "second"), ("2026-10-07T23:58:60Z", "second"), ("2026-280T23:58:60Z", "second"), ("2026-280T24:00:00Z", "hour")):
        with pytest.raises(ValueError, match=word):
            tc.parse(text)
    assert tc.parse("2026-10-07T23:59:60Z")[5] == 60 and tc.parse("2026-280T23:59:60.5")[5:] == (60, "5")
    assert tc.format_a(2026, 10, 7, 23, 59, 60, "999") == "2026-10-07T23:59:60.999Z" and tc.format_b(2016, 12, 31, 23, 59, 60) == "2016-366T23:59:60Z"


def test_year_and_month_at_both_ends():
    assert tc.format_a(1, 1, 1, 0, 0, 0) == "0001-01-01T00:00:00Z" and tc.format_a(9999, 12, 31, 0, 0, 0) == "9999-12-31T00:00:00Z"
    assert tc.format_b(9999, 12, 31, 0, 0, 0) == "9999-365T00:00:00Z" and tc.month_day(1, 365) == (12, 31) and tc.day_of_year(9999, 1, 1) == 1
    for f in (lambda y: tc.format_a(y, 1, 1, 0, 0, 0), lambda y: tc.format_b(y, 1, 1, 0, 0, 0), lambda y: tc.day_of_year(y, 1, 1), lambda y: tc.month_day(y, 1)):
        for bad in (0, 10000, -1):
            with pytest.raises(ValueError, match="year"):
                f(bad)
    for text in ("0000-01-01T00:00:00Z", "0000-001T00:00:00Z"):
        with pytest.raises(ValueError, match="year"):
            tc.parse(text)
    for bad in (0, 13):
        with pytest.raises(ValueError, match="month"):
            tc.day_of_year(2026, bad, 1)
    for text in ("2026-00-01T00:00:00Z", "2026-13-01T00:00:00Z"):
        with pytest.raises(ValueError, match="month"):
            tc.parse(text)


def test_types_are_checked_for_every_argument():
    good = [2026, 10, 7, 2, 45, 10]
    for k in range(6):
        for bad in (True, 2.0, "2", None, 2 + 0j):
            args = list(good)
            args[k] = bad
            with pytest.raises(ValueError, match="must be an integer"):
                tc.format_a(*args)
            with pytest.raises(ValueError, match="must be an integer"):
                tc.format_b(*args)
    for bad in (True, 1.0, "1", None):
        with pytest.raises(ValueError):
            tc.day_of_year(bad, 1, 1)
        with pytest.raises(ValueError):
            tc.day_of_year(2026, bad, 1)
        with pytest.raises(ValueError):
            tc.day_of_year(2026, 1, bad)
        with pytest.raises(ValueError):
            tc.month_day(bad, 1)
        with pytest.raises(ValueError):
            tc.month_day(2026, bad)
    for bad in (25, None, b"25", ["2", "5"], "2.5", "-5", " 5", "5 ", "1234567890123", "٢٥", "5\n"):
        with pytest.raises(ValueError, match="fraction must be a string"):
            tc.format_a(*good, bad)
        with pytest.raises(ValueError, match="fraction must be a string"):
            tc.format_b(*good, bad)
    assert tc.format_a(*good, "123456789012") == "2026-10-07T02:45:10.123456789012Z" and tc.MAX_FRACTION_DIGITS == 12


def test_shape_one_character_at_a_time():
    good = "2026-10-07T02:45:10.250Z"
    assert tc.parse(good) == (2026, 10, 7, 2, 45, 10, "250")
    for position in range(len(good)):                        # no character may be removed, and none replaced by a space or a letter
        for text in (good[:position] + good[position + 1:], good[:position] + " " + good[position + 1:], good[:position] + "x" + good[position + 1:]):
            if text in ("2026-10-07T02:45:10.250", "2026-10-07T02:45:10.25Z", "2026-10-07T02:45:10.20Z", "2026-10-07T02:45:10.50Z"):
                continue                                     # dropping the Z or one fraction digit leaves a valid code
            with pytest.raises(ValueError):
                tc.parse(text)
    b = "2026-280T02:45:10Z"
    for position in range(len(b) - 1):
        for text in (b[:position] + b[position + 1:], b[:position] + " " + b[position + 1:]):
            with pytest.raises(ValueError):
                tc.parse(text)
    for text in (good + "Z", good + "\n", "\n" + good, good.lower(), good.replace("T", "t"), good.replace("Z", "z"), good.replace(".", ","), good.replace("-", "/"),
                 good.replace(":", "."), "2026-10-07T02:45:10.Z", "2026-10-07T02:45:10.", "2026-10-07T02:45:10.1234567890123", "２026-10-07T02:45:10Z",
                 "2026-10-07T02:45:1٠Z", "2026-2800T02:45:10Z", "2026-28T02:45:10Z", "2026-10-07T02:45:10+00:00", "2026-10-07T02:45:10-00:00", ""):
        with pytest.raises(ValueError, match="not a CCSDS ASCII time code"):
            tc.parse(text)
    for bad in (None, 20261007, b"2026-10-07T02:45:10Z", ["2026-10-07T02:45:10Z"]):
        with pytest.raises(ValueError, match="must be a str"):
            tc.parse(bad)


def test_fraction_is_text_never_a_number():
    for digits in ("0", "5", "50", "500", "05", "000", "123456789012", "000000000001", "999999999999"):
        for text in ("2026-10-07T02:45:10." + digits + "Z", "2026-280T02:45:10." + digits + "Z"):
            fields = tc.parse(text)
            assert fields[6] == digits and type(fields[6]) is str
            assert tc.format_a(*fields) == "2026-10-07T02:45:10." + digits + "Z" and tc.format_b(*fields) == "2026-280T02:45:10." + digits + "Z"
    assert tc.parse("2026-10-07T02:45:10")[6] == "" and tc.format_a(2026, 10, 7, 2, 45, 10, "") == "2026-10-07T02:45:10Z"
    assert all(type(v) is int for v in tc.parse("2026-10-07T02:45:10.5Z")[:6])
