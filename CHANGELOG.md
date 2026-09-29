# Changelog

## Unreleased

- GPS time: `gps_minus_utc`, `gps_week_and_seconds` (full week number, not modulo 1024), `GPS_EPOCH`,
  `GpsTimeError`; requirement `TS-REQ-007`, checked against the published week-number rollovers.
  The command line prints GPS - UTC and GPS week / seconds of week.

## 0.1.0 — 2026-09-28

First public release.

- `star_timescales`: TAI − UTC from IERS Bulletin C (through Bulletin 72, expires 2027-06-28),
  TT − UTC, Julian and Modified Julian Dates; explicit errors outside the validity domain
  (`LeapSecondTableError`) and for datetimes without timezone (`NaiveDatetimeError`).
- Command line: `python -m star_timescales [instant]` prints the offsets, the Julian dates and how long
  the table remains valid; exit code 2 when the instant is refused.
- Requirements `TS-REQ-001…006`, 23 tests, independent checks against the IERS-published MJDs and
  against ERFA, and `verification/run_verification.py` to regenerate the evidence record.
- Continuous integration on Linux, macOS and Windows with Python 3.10–3.13, including the ERFA cross-check.
- `CITATION.cff`; an issue form for wrong results that asks for the reference source.
