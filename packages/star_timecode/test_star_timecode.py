"""star_timecode against published examples, hand-derivable values, inverses and edge invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import random


import star_timecode as st


def test_published_ccsds_examples_and_formats():
    a = "1988-01-18T17:20:43.123456Z"
    b = "1988-018T17:20:43.123456Z"
    fields = (1988, 1, 18, 17, 20, 43, "123456")
    assert st.parse(a) == fields
    assert st.parse(b) == fields
    assert st.format_a(*fields) == a
    assert st.format_b(*fields) == b


def test_parsing_hand_derivable_values_and_optional_z():
    assert st.parse("2026-10-07T02:45:10.250Z") == (2026, 10, 7, 2, 45, 10, "250")
    assert st.parse("2026-10-07T02:45:10") == (2026, 10, 7, 2, 45, 10, "")
    # 2026-10-07 is day 280: 31+28+31+30+31+30+31+31+30 = 273; 273 + 7 = 280
    assert st.parse("2026-280T02:45:10Z") == (2026, 10, 7, 2, 45, 10, "")
    assert st.parse("2026-10-07T02:45:10.000Z")[6] == "000"
    assert st.parse("2024-366T00:00:00.000000000001")[6] == "000000000001"
    assert st.parse("2024-366T00:00:00Z")[:3] == (2024, 12, 31)
    assert st.parse("2024-060T00:00:00Z")[:3] == (2024, 2, 29)
    assert st.parse("2023-060T00:00:00Z")[:3] == (2023, 3, 1)
    assert st.parse("0001-001T00:00:00Z") == (1, 1, 1, 0, 0, 0, "")
    assert st.parse("9999-12-31T23:59:59Z")[:3] == (9999, 12, 31)


def test_leap_second_and_time_guard():
    assert st.parse("2016-12-31T23:59:60Z") == (2016, 12, 31, 23, 59, 60, "")
    assert st.format_a(2016, 12, 31, 23, 59, 60) == "2016-12-31T23:59:60Z"


def test_formatters_hand_derivable_values():
    assert st.format_a(2026, 10, 7, 2, 45, 10, "250") == "2026-10-07T02:45:10.250Z"
    assert st.format_a(2026, 10, 7, 2, 45, 10) == "2026-10-07T02:45:10Z"
    assert st.format_b(2026, 10, 7, 2, 45, 10) == "2026-280T02:45:10Z"
    assert st.format_b(2024, 3, 1, 0, 0, 0) == "2024-061T00:00:00Z"
    assert st.format_b(2023, 3, 1, 0, 0, 0) == "2023-060T00:00:00Z"
    assert st.format_a(1, 1, 1, 0, 0, 0) == "0001-01-01T00:00:00Z"
    assert st.format_b(1, 1, 1, 0, 0, 0) == "0001-001T00:00:00Z"


def test_day_of_year_and_month_day_hand_derivable_values():
    assert st.day_of_year(2026, 1, 1) == 1
    assert st.day_of_year(2026, 12, 31) == 365
    assert st.day_of_year(2024, 12, 31) == 366
    assert st.day_of_year(2024, 3, 1) == 61
    assert st.day_of_year(2023, 3, 1) == 60
    assert st.day_of_year(2000, 3, 1) == 61
    assert st.day_of_year(1900, 3, 1) == 60
    assert st.day_of_year(2100, 3, 1) == 60
    assert st.day_of_year(2026, 10, 7) == 280

    assert st.month_day(2026, 280) == (10, 7)
    assert st.month_day(2024, 60) == (2, 29)
    assert st.month_day(2023, 60) == (3, 1)
    assert st.month_day(2026, 1) == (1, 1)
    assert st.month_day(2026, 365) == (12, 31)
    assert st.month_day(2024, 366) == (12, 31)


def test_round_trips_and_inverse_invariant():
    samples = [
        (1, 1, 1, 0, 0, 0, ""),
        (2026, 10, 7, 2, 45, 10, "250"),
        (2024, 2, 29, 23, 59, 59, "000000000001"),
        (2016, 12, 31, 23, 59, 60, ""),
        (9999, 12, 31, 23, 59, 59, "9"),
    ]
    for f in samples:
        assert st.parse(st.format_a(*f)) == f
        assert st.parse(st.format_b(*f)) == f
    ta = "2026-10-07T02:45:10.250Z"
    assert st.format_a(*st.parse(ta)) == ta


def test_month_day_day_of_year_inverse_for_random_valid_dates():
    rnd = random.Random(7)
    for _ in range(200):
        y = rnd.randint(1, 9999)
        lim = 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365
        ddd = rnd.randint(1, lim)
        m, d = st.month_day(y, ddd)
        assert st.day_of_year(y, m, d) == ddd
