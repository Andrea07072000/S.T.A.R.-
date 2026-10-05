# star-cdm

Strict parser for CCSDS 508.0-B-1 Conjunction Data Messages in KVN. Standard library only.

## Requirements
- R1 `parse_cdm(text) -> {"header", "object1", "object2", "warnings"}`: dates as datetimes (CCSDS 502.0 formats only),
  numbers as floats, units checked against the standard, exactly OBJECT1 then OBJECT2, all obligatory keywords
  (the set of the standard's example 3.6.2).
- R2 Every malformation raises `CdmFormatError` (unknown keyword, missing obligatory keyword, wrong unit, duplicate,
  non-numeric, malformed date, wrong object count). Typographic minus signs (U+2212) are normalised and REPORTED.
- R3 `covariance_rtn(obj)` -> symmetric 6x6; `consistency_report(cdm)` compares MISS_DISTANCE with the state vectors
  and RELATIVE_POSITION_R/T/N and flags inconsistencies without editing values.

## How it is verified
The three official KVN examples (extracted verbatim from the public PDF), 9 malformed messages, and Orekit 13.1
CdmParser as independent oracle (3/3 examples, 6 fields identical). Three typos found in the standard's examples are
documented in 09_DISCOVERIES (DISC-CCSDS-001..003).

## Not supported / not claimed
XML CDM, CDM 2.0 (508.0-B-2 draft/updates), collision probability computation, any operational use.

## 0.2.0 — component-level consistency (`deep_consistency`, 2026-10-05)
- RELATIVE_POSITION_R/T/N and RELATIVE_VELOCITY_R/T/N checked component by component against r2-r1 / v2-v1 projected
  on object-1 RTN axes (R along r, N along r x v); RELATIVE_SPEED against |v2-v1|; both 6x6 RTN covariances checked
  positive semi-definite (cyclic Jacobi, tolerance 1e-4 of the largest variance, sized for 4-5 printed digits).
- The RTN projection matches Orekit 13.1 `LOFType.QSW` to < 1e-6 m on the official examples (`orekit_rtn_probe.py`).
- Official example 3.6.3: R, speed and T/N norms agree with the states, but the T and N components do not (a ~1.9 deg
  rotation about R) — recorded as candidate DISC-CCSDS-004, not reported.
