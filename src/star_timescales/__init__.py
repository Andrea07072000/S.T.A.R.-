# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""star_timescales: UTC, TAI, TT and GPS offsets, GPS weeks and Julian dates, with explicit validity domains.

Part of the public S.T.A.R. engineering repository. See README.md.
"""

from .leap_seconds import (
    GPS_EPOCH,
    LEAP_SECONDS,
    LEAP_SECONDS_SOURCE,
    LEAP_SECONDS_VALID_UNTIL,
    TAI_MINUS_GPS_S,
    TT_MINUS_TAI_S,
    GpsTimeError,
    LeapSecondTableError,
    NaiveDatetimeError,
    gps_minus_utc,
    gps_week_and_seconds,
    julian_date,
    jd_to_mjd,
    mjd_to_jd,
    modified_julian_date,
    tai_minus_utc,
    tt_minus_utc,
)

__all__ = [
    "GPS_EPOCH",
    "LEAP_SECONDS",
    "LEAP_SECONDS_SOURCE",
    "LEAP_SECONDS_VALID_UNTIL",
    "TAI_MINUS_GPS_S",
    "TT_MINUS_TAI_S",
    "GpsTimeError",
    "LeapSecondTableError",
    "NaiveDatetimeError",
    "gps_minus_utc",
    "gps_week_and_seconds",
    "julian_date",
    "jd_to_mjd",
    "mjd_to_jd",
    "modified_julian_date",
    "tai_minus_utc",
    "tt_minus_utc",
]
__version__ = "0.1.0"
