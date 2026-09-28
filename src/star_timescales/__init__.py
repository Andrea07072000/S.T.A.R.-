# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""star_timescales: UTC, TAI and TT offsets and Julian dates, with explicit validity domains.

Part of the public S.T.A.R. engineering repository. See README.md.
"""

from .leap_seconds import (
    LEAP_SECONDS,
    LEAP_SECONDS_SOURCE,
    LEAP_SECONDS_VALID_UNTIL,
    TT_MINUS_TAI_S,
    LeapSecondTableError,
    NaiveDatetimeError,
    julian_date,
    jd_to_mjd,
    mjd_to_jd,
    modified_julian_date,
    tai_minus_utc,
    tt_minus_utc,
)

__all__ = [
    "LEAP_SECONDS",
    "LEAP_SECONDS_SOURCE",
    "LEAP_SECONDS_VALID_UNTIL",
    "TT_MINUS_TAI_S",
    "LeapSecondTableError",
    "NaiveDatetimeError",
    "julian_date",
    "jd_to_mjd",
    "mjd_to_jd",
    "modified_julian_date",
    "tai_minus_utc",
    "tt_minus_utc",
]
__version__ = "0.1.0"
