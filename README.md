# S.T.A.R. — Systems, Testing, Assurance & Reliability

[![tests](https://github.com/Andrea07072000/S.T.A.R.-/actions/workflows/tests.yml/badge.svg)](https://github.com/Andrea07072000/S.T.A.R.-/actions/workflows/tests.yml)

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
from star_timescales import tai_minus_utc, tt_minus_utc, julian_date

t = datetime(2026, 9, 28, tzinfo=timezone.utc)
tai_minus_utc(t)   # 37        TAI - UTC, seconds (IERS Bulletin C)
tt_minus_utc(t)    # 69.184    TT - UTC, seconds
julian_date(t)     # 2461311.5

tai_minus_utc(datetime(2030, 1, 1, tzinfo=timezone.utc))
# LeapSecondTableError: leap-second table valid until 2027-06-28; update it from IERS Bulletin C ...
tai_minus_utc(datetime(2026, 9, 28))
# NaiveDatetimeError: 2026-09-28T00:00:00 has no timezone; pass an aware datetime ...
```

Install and test:

```bash
python -m pip install "git+https://github.com/Andrea07072000/S.T.A.R.-"   # the library, no dependencies
git clone https://github.com/Andrea07072000/S.T.A.R.- && cd S.T.A.R.-
python -m pip install pytest pyerfa && python -m pytest                    # 22 tests
```

Python 3.10 to 3.13; tested on Linux, macOS and Windows (see the badge above).

## How it is verified

- **Requirements.** Six requirements (`TS-REQ-001` to `006`) in [`verification/REQUIREMENTS.md`](verification/REQUIREMENTS.md),
  each linked to the tests that verify it.
- **Primary source.** IERS publishes the Modified Julian Date of every leap-second step. Every calendar date in
  the table, converted by this library, must give exactly the published MJD.
- **Independent implementation.** Results are compared with ERFA, the open implementation of the IAU SOFA
  routines: TAI − UTC one second before, at, and 100 days after every step. The one convention difference
  (ERFA stretches a leap-second day to 86 401 s for Julian dates) is measured and bounded, not hidden.
- **Evidence.** `python verification/run_verification.py` regenerates [`verification/evidence/`](verification/evidence/):
  test results, environment and SHA-256 digests. The committed copy records the commit it was produced from.

The first version of the cross-check used a wrong reference and reported an error that was not there. The
account of how that was found is in [`verification/REQUIREMENTS.md`](verification/REQUIREMENTS.md#what-was-found-while-writing-these-tests).

## Status

| | Status |
|---|---|
| `star_timescales` 0.1.0 | Implemented, verified as above |
| Further open components | Published one at a time, only once verified |
| The S.T.A.R. assurance tooling (requirement-to-evidence traceability) | In development, not open source, not in this repository |

## What is not claimed

S.T.A.R. is not affiliated with, endorsed or certified by NASA, ESA, SpaceX, IERS, the IAU or any regulatory or
mission authority; those names appear only to cite public data and algorithms. Nothing here is flight-certified
or a statement of compliance with a standard.

## Sources

Leap seconds: IERS Earth Orientation Centre, Bulletin C, `Leap_Second.dat` (through Bulletin 72, July 2026;
expires 2027-06-28). Julian date: J. Meeus, *Astronomical Algorithms*, reimplemented.

## License, security, contributing

[Apache-2.0](LICENSE) · [Security policy](SECURITY.md) · [Contributing](CONTRIBUTING.md) ·
[Changelog](CHANGELOG.md) · Cite: [`CITATION.cff`](CITATION.cff)

Andrea Cavazzini — cavazziniandrea515@gmail.com
