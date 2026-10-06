# star_units — unit conversion with exact definitions and a dimension check

Conversion between the units a space project actually mixes — SI, imperial, astronomical — where every factor is
the exact definition and a conversion between different dimensions is an error instead of a number.
Standard library only.

```python
import star_units as su
su.convert(1.0, "lbf", "N")              # 4.4482216152605 exactly
su.convert(1.0, "lbf*s", "N*s")          # 4.4482216152605: impulse is its own dimension
su.convert(1.0, "lbf", "N*s")            # ValueError: force is not impulse
su.convert(1.0, "pc", "au")              # 206264.80624709636
su.convert_temperature(100.0, "degC", "degF")   # 212.0
```

## Requirements
- R1 `convert(value, from_unit, to_unit)` for 64 units of ten dimensions (length, mass, time, force, pressure, angle,
  speed, energy, power, impulse). Every factor is the exact definition (SI Brochure, NIST SP 811, the 1959 yard and
  pound, standard gravity, IAU 2012 B2 and 2015 B2) held as a fraction; the ratio is exact and rounded once.
- R2 `convert_temperature` for K, °C, °F, °R, exact in rational arithmetic; `dimension(unit)` and `units(dimension)`.
- R3 Measured on ALL 416 ordered pairs of units of the same dimension: within 4.5e-16 relative of SciPy's table on
  every pair; within 2.3e-16 of astropy on 328 pairs; 84 temperature conversions within 2e-12 K of both.
- R4 A conversion between different dimensions raises `ValueError` naming both; so do unknown or mis-cased unit
  names, non-finite or non-numeric values (booleans included), an overflowing result, a temperature below
  absolute zero.

## Evidence
- Published: the exact definitions listed above.
- `crosscheck_units.py`: SciPy and astropy, each in its own interpreter, each probed on exact definitions, on every
  pair of units (no sampling).

## What is NOT claimed
A fixed table, not a unit algebra: no compound units beyond the ones listed, no prefixes generated on the fly, no
parsing of expressions. The calorie is the thermochemical one (4.184 J) and the BTU the International Table one;
other calories and BTUs exist. On the 68 pairs that involve lbf, slug, psi, hp, ft*lbf, lbf*s or BTU, astropy
differs from this module and from SciPy by up to 1.7e-8 relative: it builds the pound-force from a slug rounded to
32.174049 lb and holds the BTU to nine digits; this module follows the exact definitions. That is recorded as a
candidate observation about a third-party library, not reported. astropy has no kgf and no atm: 20 pairs are
compared with SciPy only.
