# S.T.A.R. — Systems, Testing, Assurance & Reliability

[![tests](https://github.com/Andrea07072000/S.T.A.R.-/actions/workflows/tests.yml/badge.svg)](https://github.com/Andrea07072000/S.T.A.R.-/actions/workflows/tests.yml)
[![packages](https://github.com/Andrea07072000/S.T.A.R.-/actions/workflows/packages.yml/badge.svg)](https://github.com/Andrea07072000/S.T.A.R.-/actions/workflows/packages.yml)

> **Latest release: [S.T.A.R. packages 2026-10-05](https://github.com/Andrea07072000/S.T.A.R.-/releases/tag/packages-2026.10.05)**
> — 12 packages in [`packages/`](packages/README.md), all Apache-2.0: independent auditors of other space libraries
> (SGP4, frames, time scales, orbital elements, CCSDS, TLE ingestion), CCSDS telemetry in Python and C99, conjunction
> screening, CDM consistency, cross-checking, orbit mechanics. Each is re-tested by GitHub on every push, and its README
> says what it does *not* claim. Defects found and fixed while preparing the release are listed in the release notes.

S.T.A.R. is an engineering platform for verification evidence: every requirement is linked to the tests
that check it, and every result can be reproduced. This repository holds its open components. Each one ships
with its requirements, its tests and a reproducible record of its verification.

The rule behind all of it: **a result is either verified, or it says why it is not.** No plausible number
outside a validity domain, no green check without a test that ran.

## First component: `star_timescales`

UTC is not continuous: 27 leap seconds have been added since 1972, and the official table expires. Code that
converts between time scales usually returns the last known offset forever. This library returns the correct
offset inside the table's validity, and **refuses** outside it.

```python
from datetime import datetime, timezone
from star_timescales import tai_minus_utc, tt_minus_utc, julian_date, gps_week_and_seconds

t = datetime(2026, 9, 28, tzinfo=timezone.utc)
tai_minus_utc(t)   # 37        TAI - UTC, seconds (IERS Bulletin C)
tt_minus_utc(t)    # 69.184    TT - UTC, seconds
julian_date(t)     # 2461311.5
gps_week_and_seconds(t)  # (2438, 86418.0)  full GPS week, seconds of week

tai_minus_utc(datetime(2030, 1, 1, tzinfo=timezone.utc))
# LeapSecondTableError: leap-second table valid until 2027-06-28; update it from IERS Bulletin C ...
tai_minus_utc(datetime(2026, 9, 28))
# NaiveDatetimeError: 2026-09-28T00:00:00 has no timezone; pass an aware datetime ...
```

From a terminal, for any instant or for now:

```text
$ python -m star_timescales 2026-09-28T00:00:00Z
instant (UTC)   2026-09-28T00:00:00+00:00
TAI - UTC       37 s
TT - UTC        69.184 s
JD / MJD        2461311.500000 / 61311.000000
GPS - UTC       18 s
GPS week / SOW  2438 / 86418.000000 s
CCSDS CUC       1E 81 4C 0C A5 00 00  (Level 1, P-field 1E: 4+2 octets, TAI since 1958)
table           IERS Bulletin C, Leap_Second.dat (updated through Bulletin 72, July 2026; expires 2027-06-28)
table valid     until 2027-06-28 (N days from today)

$ python -m star_timescales 2030-01-01T00:00:00Z
refused: leap-second table valid until 2027-06-28; update it from IERS Bulletin C before using later epochs
```

### Spacecraft time: GPS weeks and CCSDS time codes

Telemetry is timestamped in TAI-based codes, ground systems think in UTC, navigation in GPS weeks. The same
verified leap-second table drives all three:

```python
from star_timescales import encode_cuc, decode_cuc, cuc_to_utc, gps_week_and_seconds

t = datetime(2026, 9, 28, tzinfo=timezone.utc)
encode_cuc(t).hex(" ").upper()   # '1E 81 4C 0C A5 00 00'  CCSDS CUC Level 1, 4 coarse + 2 fine octets
decode_cuc(encode_cuc(t))        # Fraction(2169244837, 1)  exact TAI seconds since 1958-01-01
cuc_to_utc(encode_cuc(t, fine_octets=3)) == t   # True: exact round trip to the microsecond
gps_week_and_seconds(t)          # (2438, 86418.0)  full week number, not modulo 1024
```

Across the leap second of 2016-12-31 both scales advance by 2 s between UTC 23:59:59 and 00:00:00, as they
must; a code that falls inside 23:59:60 is refused when converted back to UTC, not silently shifted.

Install and test:

```bash
python -m pip install "git+https://github.com/Andrea07072000/S.T.A.R.-"   # the library, no dependencies
git clone https://github.com/Andrea07072000/S.T.A.R.- && cd S.T.A.R.-
python -m pip install pytest pyerfa && python -m pytest                    # 42 tests
```

Python 3.10 to 3.13; tested on Linux, macOS and Windows (see the badge above).

## How it is verified

- **Requirements.** Nine requirements (`TS-REQ-001` to `009`) in [`verification/REQUIREMENTS.md`](verification/REQUIREMENTS.md),
  each linked to the tests that verify it.
- **Primary source.** IERS publishes the Modified Julian Date of every leap-second step. Every calendar date in
  the table, converted by this library, must give exactly the published MJD.
- **Independent implementation.** Results are compared with ERFA, the open implementation of the IAU SOFA
  routines: TAI − UTC one second before, at, and 100 days after every step. The one convention difference
  (ERFA stretches a leap-second day to 86 401 s for Julian dates) is measured and bounded, not hidden.
  CCSDS codes are checked the same way against ERFA's `utctai`, at every leap-second step and at 300 random instants.
- **Published values.** GPS weeks are checked against the week-number rollovers of 1999-08-21T23:59:47Z (week
  1024) and 2019-04-06T23:59:42Z (week 2048); the CUC P-field against the layout of CCSDS 301.0-B-4.
- **Evidence.** `python verification/run_verification.py` regenerates [`verification/evidence/`](verification/evidence/):
  test results, environment and SHA-256 digests. The committed copy records the commit it was produced from.

The first version of the cross-check used a wrong reference and reported an error that was not there. The
account of how that was found is in [`verification/REQUIREMENTS.md`](verification/REQUIREMENTS.md#what-was-found-while-writing-these-tests).

## Status

| | Status |
|---|---|
| `star_timescales` 0.2.0 | Implemented, verified as above |
| Further open components | Published one at a time, only once verified |
| The S.T.A.R. assurance tooling (requirement-to-evidence traceability) | In development, not open source, not in this repository |

## What is not claimed

S.T.A.R. is not affiliated with, endorsed or certified by NASA, ESA, SpaceX, CCSDS, IERS, the IAU or any regulatory or
mission authority; those names appear only to cite public data and algorithms. Nothing here is flight-certified
or a statement of compliance with a standard.

## Sources

Leap seconds: IERS Earth Orientation Centre, Bulletin C, `Leap_Second.dat` (through Bulletin 72, July 2026;
expires 2027-06-28). Julian date: J. Meeus, *Astronomical Algorithms*, reimplemented. CCSDS 301.0-B-4,
*Time Code Formats* (section 3.2, Unsegmented Time Code). GPS time: IS-GPS-200 (GPS = TAI − 19 s).

## Also from this author

[**nightshift-skills**](https://github.com/Andrea07072000/nightshift-skills) — skills for AI coding agents that work
unattended (preflight before overnight runs, honest status reports), each one benchmarked with and without the skill.

## License, security, contributing

[Apache-2.0](LICENSE) · [Security policy](SECURITY.md) · [Contributing](CONTRIBUTING.md) ·
[Changelog](CHANGELOG.md) · Cite: [`CITATION.cff`](CITATION.cff)

Andrea Cavazzini — cavazziniandrea515@gmail.com
