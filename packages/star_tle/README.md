# star_tle — a strict reader of two-line element sets

Reads the two lines of a NORAD element set into a dictionary, in the units printed on the lines, and refuses anything
that is not a well-formed set. Standard library only.

```python
import star_tle
t = star_tle.parse(line1, line2)          # {"satnum": 25544, "inclination_deg": 51.6416, "bstar": -1.1606e-05, ...}
star_tle.epoch_utc(t)                     # timezone-aware datetime
```

## Requirements
- R1 `parse(line1, line2)`: catalogue number (Alpha-5 included), classification, international designator, epoch
  (four-digit year with the 1957-2056 window, day of year), half the first derivative and a sixth of the second
  derivative of the mean motion, B*, ephemeris type, element number, inclination, right ascension of the node,
  eccentricity, argument of perigee, mean anomaly, mean motion, revolution number. Each number is the nearest double
  of the printed text.
- R2 `checksum(line)`: digits count as themselves, '-' counts 1, everything else 0, modulo 10. `epoch_utc(tle)`.
- R3 Measured on the 29 well-formed sets of the SGP4 verification catalogue: all 14 numeric fields equal to python-sgp4
  and to Orekit within 6e-14 after unit conversion.
- R4 A malformed set raises `TleError` (a `ValueError`) whose `reason` is one of: `length`, `charset`, `line_number`,
  `checksum`, `satnum_mismatch`, `field:<name>`, `range:<name>`. Nothing is repaired. Measured on 174 malformed sets
  in six kinds: star_tle refuses 147, Orekit 145, python-sgp4 none (it is tolerant by design). The two extra refusals
  are sets with a correct checksum whose node or perigee angle is 360 degrees or more.

## Evidence
- Published: the ISS element set used as the worked example of the format (every field, both checksums, the epoch)
  and the SGP4 verification catalogue (`fixtures/SGP4-VER.TLE`).
- `crosscheck_tle.py`: python-sgp4 and Orekit, each in its own interpreter, first probed on the first set of the
  catalogue.
- 61 single-field defects with a recomputed checksum, each refused with the expected reason.

## What is NOT claimed
A reader, not a propagator: the elements are SGP4 mean elements in the TEME frame and mean nothing without SGP4. No
three-line sets (name line), no OMM/XML/JSON, no writer. The strictness is a choice: a set that another tool accepts
may be refused here, with the reason.
