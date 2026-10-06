# star_era — Earth Rotation Angle and IAU 2006 sidereal time

The angle the Earth has turned (IAU 2000 definition) and the Greenwich Mean Sidereal Time consistent with the
IAU 2006 precession. Standard library only.

```python
import star_era
star_era.era_deg(2460000.5, 0.25)                             # degrees, UT1 as day + fraction
star_era.gmst06_deg(2460000.5, 0.25, 2460000.5, 0.2508)       # UT1 pair, then TT pair
```

## Requirements
- R1 `era_deg(ut1_day, ut1_frac=0)`: ERA in degrees in [0, 360), IERS Conventions (2010) eq. 5.15. Reproduces the SOFA
  validation value to 1e-13 rad.
- R2 `gmst06_deg(ut1_day, ut1_frac, tt_day, tt_frac)`: ERA plus the IAU 2006 polynomial in TT (eq. 5.32). Reproduces
  the SOFA validation value to 1e-13 rad.
- R3 Dates are two-part Julian Dates (any split); a nanosecond of UT1 stays visible. Measured on 1000 dates over
  1800-2200: within 2.4e-8 arcsec of ERFA (ERA and GMST) and 3.6e-8 arcsec of Skyfield (ERA).
- R4 Every function returns a finite angle in [0, 360) or raises `ValueError`: non-numeric, boolean, NaN or infinite
  input, a date outside 1800-01-01 to 2200-01-01.

## Evidence
- Published: SOFA validation values for `era00` and `gmst06`; the constants of the IERS Conventions pinned in the tests.
- The definition evaluated in exact rational arithmetic in the tests.
- `crosscheck_era.py`: ERFA and Skyfield, each in its own interpreter, first probed on the SOFA value.

## What is NOT claimed
Mean sidereal time only: no equation of the equinoxes (apparent sidereal time), no polar motion, and UT1 is an input
(UT1 - UTC comes from the IERS, not from here). For the 1982 GMST model see `star_sidereal`.
