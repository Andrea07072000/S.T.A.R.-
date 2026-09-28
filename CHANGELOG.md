# Changelog

## Unreleased

- Continuous integration on Linux, macOS and Windows with Python 3.10–3.13, including the ERFA cross-check.
- Packaging: require setuptools >= 77 (needed for the SPDX license expression in `pyproject.toml`).
- `CITATION.cff`; an issue form for wrong results that asks for the reference source.

## 0.1.0 — 2026-09-28

First public release.

- `star_timescales`: TAI − UTC from IERS Bulletin C (through Bulletin 72, expires 2027-06-28),
  TT − UTC, Julian and Modified Julian Dates; explicit errors outside the validity domain
  (`LeapSecondTableError`) and for datetimes without timezone (`NaiveDatetimeError`).
- Requirements `TS-REQ-001…006`, 22 tests, independent checks against the IERS-published MJDs and
  against ERFA, and `verification/run_verification.py` to regenerate the evidence record.
