# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Andrea Cavazzini
"""star_timescales: UTC, TAI, TT and GPS offsets, GPS weeks, CCSDS CUC time codes and Julian dates, with explicit validity domains.

Part of the public S.T.A.R. engineering repository. See README.md.
"""

from .ccsds import CUC_EPOCH_TAI, CucFormatError, cuc_p_field, cuc_to_utc, decode_cuc, encode_cuc
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
    "CUC_EPOCH_TAI",
    "CucFormatError",
    "cuc_p_field",
    "cuc_to_utc",
    "decode_cuc",
    "encode_cuc",
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
__version__ = "0.2.0"
