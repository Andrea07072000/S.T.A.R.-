# Changelog

## 0.1.0 — 2026-09-28

First public release.

- `star_timescales`: TAI − UTC from IERS Bulletin C (through Bulletin 72, expires 2027-06-28),
  TT − UTC, Julian and Modified Julian Dates; explicit errors outside the validity domain
  (`LeapSecondTableError`) and for datetimes without timezone (`NaiveDatetimeError`).
- Requirements `TS-REQ-001…006`, 22 tests, independent checks against the IERS-published MJDs and
  against ERFA, and `verification/run_verification.py` to regenerate the evidence record.
