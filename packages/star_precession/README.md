# star_precession — between J2000 and the mean equator of date (IAU 1976)

The rotation that takes a vector from J2000 to the mean equator and equinox of date, and back. It is the precession
that goes with the low-precision Sun and Moon of `star_sun` and `star_moon`. Standard library only.

```python
import star_precession as sp
r_j2000 = sp.j2000_from_mod(r_mod, 2460589.5)          # e.g. a Sun or Moon vector of date, into J2000
P = sp.precession_matrix(2460589.5)                    # r_mod = P r_j2000
```

## Requirements
- R1 `precession_matrix(jd_day, jd_frac=0)`: P = R3(-z) R2(theta) R3(-zeta) with the Lieske (1979) angles; identity at
  J2000.0. Reproduces the SOFA validation values of `pmat76` to 1e-15.
- R2 `mod_from_j2000(r, ...)`, `j2000_from_mod(r, ...)` (the transpose) and `precession_angles_arcsec`.
- R3 Measured on 500 dates over 1800-2200: every matrix element within 1.2e-16 of ERFA; 1500 directions within
  0.21 arcsec of PyEphem, which carries its own precession code.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input, a
  vector that is not three finite numbers, a date outside 1800-01-01 to 2200-01-01.

## Evidence
- Published: SOFA validation values; the nine Lieske coefficients pinned; the classical annual precession at J2000
  (46.124 arcsec in right ascension, 20.043 arcsec in declination) recovered from the matrix.
- Every matrix checked to be a rotation; `crosscheck_precession.py` with ERFA and PyEphem, each in its own interpreter.

## What is NOT claimed
IAU 1976 only: not the IAU 2006 precession (they differ by about 0.3 arcsec per century), no nutation (up to 17
arcsec), no frame bias between J2000 and GCRF (17 milliarcseconds). Enough for vectors known to a hundredth of a
degree; not for arcsecond astrometry.
