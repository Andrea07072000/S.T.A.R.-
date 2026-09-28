# Requirements: star_timescales

Each requirement is verified by the tests that carry its ID (`@pytest.mark.req("TS-REQ-…")` in
`tests/test_leap_seconds.py`). Method: **T** = test.

| ID | Requirement | Method | Verified by |
|---|---|---|---|
| TS-REQ-001 | TAI − UTC equals the IERS Bulletin C value in force at the given instant, including the last instant before each step and the instant of the step. | T | `test_tai_minus_utc_at_table_boundaries`, `test_every_table_entry_matches_its_iers_mjd`, `test_table_shape` |
| TS-REQ-002 | An epoch before 1972-01-01 or after the table's published expiry raises `LeapSecondTableError`; no value is returned. | T | `test_epochs_outside_the_domain_are_refused` |
| TS-REQ-003 | A datetime without timezone raises `NaiveDatetimeError`; datetimes in other timezones are converted, not misread. | T | `test_naive_datetimes_are_refused`, `test_other_timezones_are_converted_not_misread` |
| TS-REQ-004 | TT − UTC = TAI − UTC + 32.184 s. | T | `test_tt_minus_utc` |
| TS-REQ-005 | Julian and Modified Julian Dates match published reference epochs (J2000.0, MJD 0, Unix epoch, a Gregorian century boundary). | T | `test_julian_date_reference_values`, `test_mjd_round_trip` |
| TS-REQ-006 | Results agree with an independent implementation (ERFA, the open implementation of the IAU SOFA routines); the one convention difference is measured and bounded, not hidden. | T | `test_agrees_with_an_independent_implementation` (skipped if `pyerfa` is not installed) |

## Two independent checks

1. **The published MJDs.** IERS publishes the Modified Julian Date of every leap-second step
   next to the calendar date. The test converts each calendar date with this module and must obtain
   exactly the IERS value. This checks the date arithmetic against the primary source, not against the
   code under test.
2. **ERFA.** `erfa.dat` gives TAI − UTC and `erfa.dtf2d` the Julian date. TAI − UTC agrees at every step,
   one second before every step, and 100 days after. The Julian dates agree everywhere except on the UTC
   days that end with a leap second: there ERFA uses an 86401 s day and this module a civil 86400 s
   day, so they differ by at most 1 s. The test asserts that bound.

## What was found while writing these tests

The first version of the cross-check computed the "reference" TAI − UTC as the difference of two Astropy
Julian dates. On leap-second days that is not the offset (see point 2), and the check wrongly reported
11 s at 1972-06-30T23:59:59. The code was right; the reference was wrong. The test now uses `erfa.dat`
and keeps a note of the mistake, because a verification method is only as good as its reference.

## Evidence

`python verification/run_verification.py` regenerates `verification/evidence/`. The committed copy was
produced from the commit recorded in `environment.json`.
