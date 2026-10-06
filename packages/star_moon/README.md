# star_moon — where the Moon is, to a third of a degree

Low-precision geocentric Moon position from the Astronomical Almanac series (Vallado, Algorithm 31).
Standard library only.

```python
import star_moon
x, y, z = star_moon.moon_vector_km(2460589.5)         # km, mean equator and equinox of date
ra, dec = star_moon.moon_ra_dec_deg(2460589.5)
```

## Requirements
- R1 `moon_vector_km(jd_day, jd_frac=0)`, `moon_ra_dec_deg`, `moon_distance_km` for Julian dates (TDB) from 1950-01-01
  to 2050-01-01; outside, `ValueError`. Reproduces Vallado Example 5-3 within 0.4 m.
- R2 Measured accuracy of the series (2002 dates, three ephemerides): direction within 0.36 deg of JPL DE440 (95 % of
  the dates within 0.20 deg), distance within 1200 km (288 km on average). astropy and PyEphem give the same envelope.
- R3 Frame: mean equator and equinox of DATE, like `star_sun`; rotate before mixing with J2000/GCRF vectors.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input, a date
  outside 1950-2050.

## Evidence
- Published: Vallado Example 5-3 (all three components); the fourteen terms of the series pinned in the tests.
- Known facts of the lunar orbit over a century: distance range, maximum declination, one turn per sidereal month.
- `crosscheck_moon.py`: JPL DE440 through NAIF SPICE, astropy and PyEphem, each in its own interpreter.

## What is NOT claimed
Not an ephemeris: 0.36 deg is about 2300 km at the Moon's distance. Good for eclipse and illumination geometry,
third-body direction and visibility planning; not for navigation, occultation timing or tide-accurate work.
