# star_sun — Sun direction, beta angle and eclipse test

Low-precision geocentric Sun vector (Astronomical Almanac series, Vallado Algorithm 29), the beta angle of an orbit
and a cylindrical-shadow test. Standard library only.

```python
import star_sun
sun = star_sun.sun_vector_au(2460589.5)                 # AU, mean equator and equinox of date
beta = star_sun.beta_angle_deg(sun, inc_deg=97.8, raan_deg=250.0)
dark = star_sun.in_shadow(r_sat_km, sun)                # True inside the Earth's cylindrical shadow
```

## Requirements
- R1 `sun_vector_au(jd_day, jd_frac=0.0)` and `sun_ra_dec_deg`: geocentric Sun in AU, mean equator and equinox of date,
  for UT1 Julian dates from 1950-01-01 to 2050-01-01 (inclusive); outside, `ValueError`. Reproduces Vallado
  Example 5-1 within 1.2e-6 AU.
- R2 Measured accuracy (402 dates): direction within 0.0097 deg of JPL DE440 *apparent* and of astropy, distance within
  7e-5 AU. The series includes aberration: against *geometric* positions the difference reaches 0.014 deg.
- R3 `beta_angle_deg(sun, inc_deg, raan_deg)`: angle between the Sun direction and the orbit plane, in [-90, 90],
  positive on the side of the angular momentum; only the direction of `sun` is used.
- R4 `in_shadow(r_sat, sun, body_radius=6378.137)`: True when the satellite is behind the body and closer than one
  body radius to the Sun-body axis (cylinder, parallel rays, no penumbra); `r_sat` and `body_radius` in the same unit.
- R5 Every function returns finite values or raises `ValueError`: non-numeric, boolean, NaN, infinite or
  |value| >= 1e300 input; a vector that is not three numbers; a zero Sun vector; a satellite inside the body; a
  non-positive body radius; inclination outside [0, 180]; node outside [-360, 360]; a date outside 1950-2050.

## Evidence
- Published: Vallado Example 5-1; equinoxes, solstices, perihelion and aphelion at the instants published by the USNO.
- Three independent ephemerides, each in its own interpreter and first probed on the published example
  (`crosscheck_sun.py`): JPL DE440 through NAIF SPICE (geometric and apparent), astropy (ERFA series), PyEphem (VSOP87).
- Beta angle and shadow checked on cases solvable by hand.

## What is NOT claimed
Not an ephemeris: 0.01 deg is about 36 arcseconds. No nutation (mean equator of date, about 0.7 deg from J2000 in
2050: rotate before mixing with J2000/GCRF vectors). The shadow is a cylinder: no penumbra, no oblateness, no
atmosphere; near the shadow edge the answer can differ from a conical model by tens of seconds of orbit.
