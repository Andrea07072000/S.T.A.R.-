# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""Verification of star_timescales. Requirement IDs refer to verification/REQUIREMENTS.md."""

from datetime import datetime, timedelta, timezone

import pytest

from star_timescales import (
    LEAP_SECONDS,
    LEAP_SECONDS_VALID_UNTIL,
    LeapSecondTableError,
    NaiveDatetimeError,
    julian_date,
    jd_to_mjd,
    mjd_to_jd,
    modified_julian_date,
    tai_minus_utc,
    tt_minus_utc,
)

UTC = timezone.utc


@pytest.mark.req("TS-REQ-001")
@pytest.mark.parametrize("when, expected", [
    (datetime(1972, 1, 1, tzinfo=UTC), 10),
    (datetime(1972, 6, 30, 23, 59, 59, tzinfo=UTC), 10),
    (datetime(1972, 7, 1, tzinfo=UTC), 11),
    (datetime(2000, 1, 1, 12, tzinfo=UTC), 32),                 # J2000
    (datetime(2016, 12, 31, 23, 59, 59, 999999, tzinfo=UTC), 36),  # last instant before the 2017 step
    (datetime(2017, 1, 1, tzinfo=UTC), 37),
    (datetime(2026, 9, 28, tzinfo=UTC), 37),
])
def test_tai_minus_utc_at_table_boundaries(when, expected):
    assert tai_minus_utc(when) == expected


@pytest.mark.req("TS-REQ-001")
def test_every_table_entry_matches_its_iers_mjd():
    """Independent check of the date arithmetic: IERS publishes the MJD of every step."""
    for effective, mjd, _value in LEAP_SECONDS:
        assert modified_julian_date(effective) == mjd, effective


@pytest.mark.req("TS-REQ-001")
def test_table_shape():
    values = [v for _, _, v in LEAP_SECONDS]
    dates = [d for d, _, _ in LEAP_SECONDS]
    assert values[0] == 10 and values[-1] == 37
    assert all(b - a == 1 for a, b in zip(values, values[1:])), "each leap second adds exactly 1 s"
    assert dates == sorted(dates) and len(set(dates)) == len(dates)


@pytest.mark.req("TS-REQ-002")
def test_epochs_outside_the_domain_are_refused():
    with pytest.raises(LeapSecondTableError, match="1972"):
        tai_minus_utc(datetime(1971, 12, 31, 23, 59, 59, tzinfo=UTC))
    with pytest.raises(LeapSecondTableError, match="update it from IERS"):
        tai_minus_utc(LEAP_SECONDS_VALID_UNTIL + timedelta(seconds=1))
    assert tai_minus_utc(LEAP_SECONDS_VALID_UNTIL) == 37  # the expiry instant itself is still covered


@pytest.mark.req("TS-REQ-003")
@pytest.mark.parametrize("fn", [tai_minus_utc, tt_minus_utc, julian_date, modified_julian_date])
def test_naive_datetimes_are_refused(fn):
    with pytest.raises(NaiveDatetimeError):
        fn(datetime(2020, 1, 1))


@pytest.mark.req("TS-REQ-003")
def test_other_timezones_are_converted_not_misread():
    cet = timezone(timedelta(hours=1))
    # 2017-01-01 00:30 CET is 2016-12-31 23:30 UTC: still before the 2017 leap second.
    assert tai_minus_utc(datetime(2017, 1, 1, 0, 30, tzinfo=cet)) == 36
    assert julian_date(datetime(2000, 1, 1, 13, 0, tzinfo=cet)) == julian_date(datetime(2000, 1, 1, 12, tzinfo=UTC))


@pytest.mark.req("TS-REQ-004")
def test_tt_minus_utc():
    assert tt_minus_utc(datetime(2000, 1, 1, 12, tzinfo=UTC)) == pytest.approx(64.184, abs=1e-12)
    assert tt_minus_utc(datetime(2026, 9, 28, tzinfo=UTC)) == pytest.approx(69.184, abs=1e-12)


@pytest.mark.req("TS-REQ-005")
@pytest.mark.parametrize("when, jd", [
    (datetime(2000, 1, 1, 12, tzinfo=UTC), 2451545.0),   # J2000.0 epoch (UTC reading)
    (datetime(1858, 11, 17, tzinfo=UTC), 2400000.5),     # MJD 0
    (datetime(1970, 1, 1, tzinfo=UTC), 2440587.5),       # Unix epoch
    (datetime(1600, 3, 1, tzinfo=UTC), 2305507.5),       # before and after a Gregorian century leap day
])
def test_julian_date_reference_values(when, jd):
    assert julian_date(when) == pytest.approx(jd, abs=1e-9)


@pytest.mark.req("TS-REQ-005")
def test_mjd_round_trip():
    for jd in (2451545.0, 2400000.5, 2460581.25):
        assert mjd_to_jd(jd_to_mjd(jd)) == pytest.approx(jd, abs=1e-9)


@pytest.mark.req("TS-REQ-006")
def test_agrees_with_an_independent_implementation():
    """Cross-check against ERFA (the open implementation of the IAU SOFA routines, installed with
    Astropy as `pyerfa`; skipped if not installed).

    Note: ``Time.tai.jd - Time.utc.jd`` is NOT a valid reference for TAI - UTC. On a day that
    contains a leap second, Astropy represents that UTC day with 86401 s, so the difference of the
    two Julian dates is not the offset. The first version of this test used it and disagreed at
    1972-06-30T23:59:59; ``erfa.dat`` (the dedicated routine) agrees with this module.
    """
    erfa = pytest.importorskip("erfa")
    for effective, _mjd, _value in LEAP_SECONDS[1:]:
        for when in (effective - timedelta(seconds=1), effective, effective + timedelta(days=100)):
            fd = (when.hour * 3600 + when.minute * 60 + when.second) / 86400.0
            assert tai_minus_utc(when) == erfa.dat(when.year, when.month, when.day, fd), when
            jd1, jd2 = erfa.dtf2d("UTC", when.year, when.month, when.day, when.hour, when.minute, when.second)
            leap_day = (when + timedelta(days=1)).replace(hour=0, minute=0, second=0) == effective \
                and when.date() != effective.date()
            if leap_day:
                # Documented convention difference: ERFA stretches this UTC day to 86401 s,
                # this module uses the civil 86400 s day. At most 1 s (1/86400 day) apart.
                assert 0 < julian_date(when) - (jd1 + jd2) <= 1 / 86400 + 1e-9, when
            else:
                assert julian_date(when) == pytest.approx(jd1 + jd2, abs=1e-8), when


@pytest.mark.req("TS-REQ-002")
def test_command_line_reports_and_refuses(capsys):
    from star_timescales.__main__ import main
    assert main(["2026-09-28T00:00:00Z"]) == 0
    out = capsys.readouterr().out
    assert "TAI - UTC       37 s" in out and "69.184" in out and "2461311.500000" in out
    assert "valid     until 2027-06-28" in out
    assert main(["2030-01-01T00:00:00+00:00"]) == 2
    assert "update it from IERS" in capsys.readouterr().err
    assert main(["2026-09-28T00:00:00"]) == 2          # no timezone: refused, not guessed
    assert "no timezone; add one, e.g. 2026-09-28T00:00:00Z" in capsys.readouterr().err
    assert main(["2026-09-28"]) == 2                    # a date alone is also ambiguous
    assert "e.g. 2026-09-28T00:00:00Z" in capsys.readouterr().err
    assert main(["not-a-date"]) == 2
    assert "is not an ISO-8601 instant" in capsys.readouterr().err
