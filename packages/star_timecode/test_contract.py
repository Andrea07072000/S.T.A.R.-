"""Refusals and limits of star_timecode for every public function argument and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_timecode as st

HOSTILE = [2026.0, True, "2026", None]


def test_pinned_module_constants_and_exports():
    assert st.__version__ == "0.1.0"
    assert st.__all__ == ["parse", "format_a", "format_b", "day_of_year", "month_day"]
    assert st.MAX_FRACTION_DIGITS == 12


@pytest.mark.parametrize("bad", [None, 20261007, b"2026-10-07T02:45:10Z"])
def test_parse_non_str_refused(bad):
    with pytest.raises(ValueError, match="str"):
        st.parse(bad)


@pytest.mark.parametrize(
    "text",
    [
        "2026-10-07t02:45:10Z", "2026-10-07T02:45:10z", "2026-10-07 02:45:10Z",
        " 2026-10-07T02:45:10Z", "2026-10-07T02:45:10Z ", "2026-10-07T02:45:10Z\n",
        "2026-10-07T02:45Z", "2026-1-07T02:45:10Z", "2026-10-7T02:45:10Z", "2026-10-07T2:45:10Z",
        "20261007T024510Z", "2026-10-07T02:45:10+00:00", "ZZ", "+2026-10-07T02:45:10Z",
        "2026-10-07", "2026-10-07T02:45:10.Z", "2026-10-07T02:45:10.1234567890123Z",
        "2026-10-07T02:45:10,25Z", "2026/10/07T02:45:10Z", "2026-W41-3T02:45:10Z",
        "26-10-07T02:45:10Z", "12026-10-07T02:45:10Z", "2026-0280T02:45:10Z",
        "２０２６-10-07T02:45:10Z",
    ],
)
def test_parse_wrong_shape_refused(text):
    with pytest.raises(ValueError, match="CCSDS ASCII time code"):
        st.parse(text)


@pytest.mark.parametrize(
    "text, part",
    [
        ("2026-02-29T00:00:00Z", "day"),
        ("1900-02-29T00:00:00Z", "day"),
        ("2026-04-31T00:00:00Z", "day"),
        ("2026-13-01T00:00:00Z", "month"),
        ("2026-00-10T00:00:00Z", "month"),
        ("2026-10-00T00:00:00Z", "day"),
        ("2026-366T00:00:00Z", "day of year"),
        ("2026-000T00:00:00Z", "day of year"),
        ("0000-01-01T00:00:00Z", "year"),
        ("2026-10-07T24:00:00Z", "hour"),
        ("2026-10-07T02:60:10Z", "minute"),
        ("2026-10-07T12:00:60Z", "second"),
        ("2026-10-07T23:58:60Z", "second"),
        ("2026-10-07T23:59:61Z", "second"),
    ],
)
def test_parse_impossible_value_refused(text, part):
    with pytest.raises(ValueError, match=part):
        st.parse(text)


def test_range_edges_inside_and_outside():
    assert st.parse("0001-01-01T00:00:00Z") == (1, 1, 1, 0, 0, 0, "")
    assert st.parse("9999-12-31T23:59:59Z")[:3] == (9999, 12, 31)
    with pytest.raises(ValueError, match="year"):
        st.parse("0000-12-31T23:59:59Z")
    with pytest.raises(ValueError, match="year"):
        st.format_a(10000, 1, 1, 0, 0, 0)

    assert st.parse("2024-366T00:00:00Z")[:3] == (2024, 12, 31)
    with pytest.raises(ValueError, match="day of year"):
        st.parse("2026-366T00:00:00Z")

    assert st.parse("2026-10-07T23:59:60Z")[5] == 60
    with pytest.raises(ValueError, match="second"):
        st.parse("2026-10-07T23:58:60Z")


@pytest.mark.parametrize("bad", HOSTILE)
def test_day_of_year_argument_types_refused(bad):
    with pytest.raises(ValueError):
        st.day_of_year(bad, 1, 1)
    with pytest.raises(ValueError):
        st.day_of_year(2026, bad, 1)
    with pytest.raises(ValueError):
        st.day_of_year(2026, 1, bad)


@pytest.mark.parametrize("bad", HOSTILE)
def test_month_day_argument_types_refused(bad):
    with pytest.raises(ValueError):
        st.month_day(bad, 1)
    with pytest.raises(ValueError):
        st.month_day(2026, bad)


@pytest.mark.parametrize("bad", HOSTILE)
def test_formatters_integer_arguments_refused(bad):
    with pytest.raises(ValueError):
        st.format_a(bad, 1, 1, 0, 0, 0)
    with pytest.raises(ValueError):
        st.format_a(2026, bad, 1, 0, 0, 0)
    with pytest.raises(ValueError):
        st.format_a(2026, 1, bad, 0, 0, 0)
    with pytest.raises(ValueError):
        st.format_a(2026, 1, 1, bad, 0, 0, 0)
    with pytest.raises(ValueError):
        st.format_a(2026, 1, 1, 0, bad, 0)
    with pytest.raises(ValueError):
        st.format_a(2026, 1, 1, 0, 0, bad)


def test_formatter_and_day_functions_out_of_range_refused():
    with pytest.raises(ValueError):
        st.format_b(2026, 2, 29, 0, 0, 0)
    with pytest.raises(ValueError):
        st.day_of_year(2026, 4, 31)
    with pytest.raises(ValueError):
        st.month_day(2026, 366)
    with pytest.raises(ValueError):
        st.month_day(2026, 0)
    with pytest.raises(ValueError):
        st.format_a(0, 1, 1, 0, 0, 0)
    with pytest.raises(ValueError):
        st.format_b(10000, 1, 1, 0, 0, 0)


@pytest.mark.parametrize("f", [25, "2.5", "-5", " 5", "１２", "1234567890123"])
def test_fraction_contract_refused(f):
    with pytest.raises(ValueError, match="fraction must be a string"):
        st.format_a(2026, 10, 7, 2, 45, 10, f)
    with pytest.raises(ValueError, match="fraction must be a string"):
        st.format_b(2026, 10, 7, 2, 45, 10, f)
