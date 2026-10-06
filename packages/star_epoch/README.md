# star_epoch — Julian and Besselian epochs

Conversion between epochs written as years (J2000.0, B1950.0, J2026.76) and Julian Dates, in both directions.
Standard library only.

```python
import star_epoch as ep
ep.jd_from_julian_epoch(2000.0)       # (2451544.5, 0.5): J2000.0 = JD 2451545.0
ep.jd_from_besselian_epoch(1950.0)    # (2433281.5, 0.92345905): B1950.0 = JD 2433282.4235
ep.julian_epoch(2433282.5)            # 1950.0
ep.besselian_epoch(2451545.0)         # 2000.0012775...: J2000.0 as a Besselian epoch
```

## Requirements
- R1 `julian_epoch` and `jd_from_julian_epoch`: J2000.0 = JD 2451545.0 and a Julian year of 365.25 days.
  Reproduce J1900.0, J1950.0, J2000.0 and J2100.0 exactly.
- R2 `besselian_epoch` and `jd_from_besselian_epoch`: B1900.0 = JD 2415020.31352 and a tropical year of
  365.242198781 days (Lieske 1979). Reproduce B1950.0 = JD 2433282.4235 and J2000.0 = B2000.0012775.
- R3 Dates are Julian Dates in two parts; the inverse functions return a day ending in .5 and a fraction in [0, 1).
  Measured on 600 dates and 600 epochs over 1600–2400: epochs within 5e-13 yr of ERFA, Julian epochs within
  5e-13 yr of skyfield, dates identical to ERFA and within 3e-10 day of skyfield and of five SPICE constants.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input, a
  date outside JD 2086302.5 … 2816787.5, a fraction outside [-1, 1], an epoch outside [1000, 3000].

## Evidence
- Published: Lieske (1979) and Meeus, Astronomical Algorithms, ch. 21, for the six epochs above; year lengths and
  round trips checked by hand.
- `crosscheck_epoch.py`: ERFA, skyfield and SPICE, each in its own interpreter, each probed on a published epoch.

## What is NOT claimed
No time-scale conversion: the epoch is in the scale of the date passed (TT for catalogue epochs). Besselian
epochs are compared with one full library (ERFA) and two SPICE constants, not two full libraries. An epoch held
in one float resolves about 17 microseconds near the year 2000; use the two-part date when that matters. The
agreement with ERFA is exact because the arithmetic is the same: it shows the same convention, not an
independent derivation of the constants, which come from the publications above.
