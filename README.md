# S.T.A.R. — Systems, Testing, Assurance & Reliability

**S.T.A.R. is an evidence-first engineering platform for building, testing, and verifying complex
systems. It connects requirements, execution, verification, and reproducible evidence into a
traceable workflow built for rigorous engineering.**

This repository is the **public engineering surface** of S.T.A.R.: selected open components, each
published with its requirements, its tests, and a reproducible record of its verification. It is not
the commercial product and not a marketing demo. Everything here can be checked by running it.

---

## In one minute (for non-specialists)

Engineering software fails in expensive ways when a number is silently wrong: a unit mix-up, a
time offset off by one second, a test that "passed" but never ran. Industries such as space, energy
and transport handle this with *verification evidence*: for every requirement, proof that it was
tested, how, and with what result.

S.T.A.R. builds tooling for that job, with one rule above all: **a result is either verified, or it
says why it is not.** No green checkmark without a test that ran, no plausible number outside its
domain of validity, no status that is guessed.

This repository shows that rule applied to real, useful code, small enough to audit in an afternoon.

---

## What is in this repository

| Component | Status | What it does |
|---|---|---|
| [`star_timescales`](src/star_timescales/) | **IMPLEMENTED** (v0.1.0) | TAI − UTC from the IERS leap-second table, TT − UTC, Julian and Modified Julian Dates. It **refuses** epochs outside the table's validity (before 1972, after the published expiry) and datetimes without a timezone. |
| [`verification/`](verification/) | **IMPLEMENTED** | Requirements (`TS-REQ-001…006`), the tests that verify each one, and a script that regenerates the evidence record. |

That is deliberately all, for now: a small amount of verified material rather than a large amount of
unfinished material. The repository will grow one verified component at a time (see Roadmap).

### Why time scales

Every test campaign, telemetry archive and orbit computation depends on converting between time
scales. UTC is not continuous: 27 leap seconds have been inserted since 1972, and the table has an
expiry date after which a new one may exist. A converter that silently keeps returning the last known
value after the expiry is wrong in exactly the way that is hardest to notice. This one raises an error
and tells you to update the table.

## Reproduce it

```bash
python -m pip install pytest            # optional cross-check: python -m pip install astropy
python -m pytest                        # 22 tests (1 skipped without astropy/pyerfa)
python verification/run_verification.py # regenerate verification/evidence/
```

Python ≥ 3.10, no runtime dependencies.

```python
from datetime import datetime, timezone
from star_timescales import tai_minus_utc, tt_minus_utc, julian_date

t = datetime(2026, 9, 28, tzinfo=timezone.utc)
tai_minus_utc(t)   # 37
tt_minus_utc(t)    # 69.184
julian_date(t)     # 2461311.5

tai_minus_utc(datetime(2030, 1, 1, tzinfo=timezone.utc))  # LeapSecondTableError: update the table
tai_minus_utc(datetime(2026, 9, 28))                       # NaiveDatetimeError: no timezone
```

## How it is verified

Two checks that do not depend on the code under test:

1. **Primary source.** IERS publishes the Modified Julian Date of every leap-second step. Each calendar
   date converted by this module must give exactly the IERS value.
2. **Independent implementation.** Results are compared with ERFA, the open implementation of the IAU
   SOFA routines. They agree, with one convention difference that is measured and bounded in the test
   rather than hidden: on a UTC day that ends with a leap second, ERFA's Julian date uses an 86401 s day.

While writing the cross-check, the first "reference" turned out to be wrong, not the code. The story is
in [`verification/REQUIREMENTS.md`](verification/REQUIREMENTS.md). We publish it because a verification
is only as good as its reference.

## Engineering principles

- **Evidence grows faster than claims.** Nothing is described as implemented unless it is here and tested.
- **Explicit validity domains.** Outside them: an error, never a plausible number.
- **Honest status vocabulary.** A requirement is `VERIFIED`, `FAILED`, `NOT_VERIFIED`, `BLOCKED` or
  `REVIEW_REQUIRED`, never simply "OK".
- **Reproducibility.** Every published result comes with the command that regenerates it.
- **Failures are results.** When a check fails, the failure is what gets reported.

## Status of the wider S.T.A.R. program

| Capability | Status | Where |
|---|---|---|
| Time-scale conversions with validity domains | IMPLEMENTED | this repository |
| Requirement → test → evidence traceability (STAR-Assure) | IMPLEMENTED, early version | private, not in this repository; not verifiable from here |
| Orbit mechanics, unit-safe physical quantities | EXPERIMENTAL | private |
| A public, runnable STAR-Assure example project | PLANNED | this repository |
| Everything else in the long-term vision | PLANNED / UNKNOWN | — |

Long-term direction: an engineering digital thread from requirement to model, tool, simulation, test,
verification, evidence and release.

## Roadmap for this repository

Published only when verified, in no fixed order:
- a small example project showing the requirement → test → evidence workflow end to end;
- reproducible benchmarks and technical notes, each with its evidence;
- further open components that are useful on their own.

## Boundaries

**Not included, on purpose:** commercial components, customer-specific or confidential material,
internal architecture, and unreleased work. They are not in this repository or its history.

**No affiliation or certification.** S.T.A.R. is not affiliated with, endorsed by, or certified by
NASA, ESA, SpaceX, IERS, the IAU or any regulatory or mission authority. Names of organizations appear
only to cite public data sources. Nothing here is flight-certified, and nothing here is a statement of
compliance with any standard.

**Data sources.** Leap-second values: IERS Earth Orientation Centre, Bulletin C, `Leap_Second.dat`
(updated through Bulletin 72, July 2026; expires 2027-06-28). Julian date algorithm: J. Meeus,
*Astronomical Algorithms*, reimplemented, no code copied.

## License

[Apache License 2.0](LICENSE). Security reports: see [SECURITY.md](SECURITY.md). Contributions:
[CONTRIBUTING.md](CONTRIBUTING.md). Contact: cavazziniandrea515@gmail.com
