# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""GPS time: offsets and week numbers, checked against published rollover instants."""

from datetime import datetime, timedelta, timezone

import pytest

from star_timescales import (
    GPS_EPOCH,
    GpsTimeError,
    NaiveDatetimeError,
    gps_minus_utc,
    gps_week_and_seconds,
    tai_minus_utc,
)

UTC = timezone.utc


@pytest.mark.req("TS-REQ-007")
@pytest.mark.parametrize("when, week, offset", [
    (datetime(1980, 1, 6, tzinfo=UTC), 0, 0),                    # GPS epoch
    (datetime(1999, 8, 21, 23, 59, 47, tzinfo=UTC), 1024, 13),  # first week-number rollover
    (datetime(2019, 4, 6, 23, 59, 42, tzinfo=UTC), 2048, 18),   # second week-number rollover
])
def test_published_week_boundaries(when, week, offset):
    assert gps_minus_utc(when) == offset
    assert gps_week_and_seconds(when) == (week, 0.0)
    if week:  # the last second of the previous week
        assert gps_week_and_seconds(when - timedelta(seconds=1)) == (week - 1, 604799.0)


@pytest.mark.req("TS-REQ-007")
def test_gps_minus_utc_is_tai_minus_utc_minus_19_at_every_step():
    assert gps_minus_utc(datetime(2016, 12, 31, 23, 59, 59, tzinfo=UTC)) == 17
    assert gps_minus_utc(datetime(2017, 1, 1, tzinfo=UTC)) == 18
    for day in range(0, 17000, 97):
        t = GPS_EPOCH + timedelta(days=day)
        assert gps_minus_utc(t) == tai_minus_utc(t) - 19


@pytest.mark.req("TS-REQ-007")
def test_gps_scale_is_continuous_across_a_leap_second():
    # UTC inserted 2016-12-31T23:59:60: between these two UTC labels two SI seconds elapse.
    before = gps_week_and_seconds(datetime(2016, 12, 31, 23, 59, 59, tzinfo=UTC))
    after = gps_week_and_seconds(datetime(2017, 1, 1, tzinfo=UTC))
    assert after[0] == before[0] and after[1] - before[1] == 2.0


@pytest.mark.req("TS-REQ-007")
def test_microseconds_are_kept():
    assert gps_week_and_seconds(GPS_EPOCH + timedelta(microseconds=1)) == (0, 1e-06)


@pytest.mark.req("TS-REQ-007")
def test_instants_outside_the_domain_are_refused():
    with pytest.raises(GpsTimeError):
        gps_minus_utc(GPS_EPOCH - timedelta(microseconds=1))
    with pytest.raises(GpsTimeError):
        gps_week_and_seconds(datetime(1979, 12, 31, tzinfo=UTC))
    with pytest.raises(NaiveDatetimeError):
        gps_week_and_seconds(datetime(2020, 1, 1))
