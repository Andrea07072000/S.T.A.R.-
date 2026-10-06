# star_ecliptic — mean obliquity and equatorial ⇄ ecliptic directions

The mean obliquity of the ecliptic (IAU 2006 and IAU 1980 polynomials) and the rotation between equatorial
(right ascension, declination) and ecliptic (longitude, latitude) directions for an obliquity chosen by the caller.
Standard library only.

```python
import star_ecliptic as se
eps = se.mean_obliquity_arcsec(2451545.0)                    # 84381.406 arcsec (IAU 2006) at J2000.0
se.mean_obliquity_arcsec(2446895.5, 0.0, "iau1980")          # 84387.407 arcsec: Meeus Example 22.a
se.equatorial_to_ecliptic(116.328942, 28.026183, 84381.448)  # (113.215630, 6.684170): Pollux, Meeus Example 13.a
se.ecliptic_to_equatorial(113.215630, 6.684170, 84381.448)   # back to right ascension and declination
```

## Requirements
- R1 `mean_obliquity_arcsec(jd_day, jd_frac, model)` evaluates the IAU 2006 (default) or IAU 1980 polynomial in TT
  Julian centuries from J2000.0, with the date split in day and fraction. Reproduces Meeus Example 22.a.
- R2 `equatorial_to_ecliptic` and `ecliptic_to_equatorial` are one rotation about the equinox by the obliquity
  passed by the caller, and are inverse of each other; longitudes out are in [0, 360). Reproduce Meeus Example 13.a.
- R3 Measured on 600 cases (dates 1800–2200, 100 directions down to 1e-6 deg from the pole of the ecliptic):
  directions within 1.1e-13 deg of ERFA, astropy and SPICE; IAU 2006 obliquity within 1.5e-11 arcsec of ERFA and
  skyfield; IAU 1980 obliquity within 1.5e-11 arcsec of ERFA.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input, a
  date outside JD 2086302.5 … 2816787.5 (years 1000–3000), a fraction outside [-1, 1], an unknown model,
  declination or latitude outside [-90, 90], right ascension or longitude outside [-360, 360], obliquity outside
  [0, 324000] arcsec.

## Evidence
- Published: Meeus, Astronomical Algorithms, Examples 13.a and 22.a; both polynomials summed by hand at T = +1 and
  T = −2; rotations of the equinoxes, the solstice points and the two poles done by hand.
- `crosscheck_ecliptic.py`: ERFA, astropy, SPICE and skyfield, each in its own interpreter, each probed on a
  published value before being compared.

## What is NOT claimed
Mean obliquity only: no nutation (pass a true obliquity if you have one). No precession: the directions stay
referred to the equinox they were given in. The IAU 1980 polynomial is compared with one library (ERFA) and one
published example, not two libraries. At a pole of the target frame the longitude is undefined and the value
returned there is arbitrary (within [0, 360)). The time argument is TT; using UTC instead changes the result by
less than 1e-6 arcsec.
