# star_galactic — equatorial ⇄ galactic directions

Galactic longitude and latitude from right ascension and declination, and back, in the two definitions in use:
the Hipparcos one for ICRS directions and the IAU 1958 one for B1950.0 directions. Standard library only.

```python
import star_galactic as sg
sg.equatorial_to_galactic(266.405, -28.936)                      # ICRS direction near the galactic centre -> l ~ 0, b ~ 0
sg.equatorial_to_galactic(267.248917, -14.718944, "b1950")       # (12.9593, 6.0463): Meeus Example 13.b
sg.galactic_to_equatorial(0.0, 90.0)                             # (192.85948, 27.12825): the galactic pole, ICRS
```

## Requirements
- R1 System "icrs": galactic pole at ICRS 192.85948, +27.12825 and longitude of the celestial pole 122.93192
  (ESA 1997, Hipparcos, vol. 1, 1.5.3).
- R2 System "b1950": galactic pole at B1950.0 192.25, +27.4 and longitude of the celestial pole 123.0 (IAU 1958).
  Reproduces Meeus Example 13.b.
- R3 The two functions are inverse of each other; longitudes out are in [0, 360). Measured on 600 directions (100
  down to 1e-6 deg from a galactic pole), in both directions: within 9e-14 deg of ERFA ("icrs") and within
  1.1e-13 deg of astropy and SPICE ("b1950").
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  latitude or declination outside [-90, 90], longitude or right ascension outside [-360, 360], an unknown system.

## Evidence
- Published: the two definitions above and Meeus, Astronomical Algorithms, Example 13.b.
- `crosscheck_galactic.py`: ERFA, astropy and SPICE, each in its own interpreter, each probed on a published value.
  The probe excluded a first SPICE driver that used the frame named B1950 (0.525 arcsec from FK4, on which the
  galactic system is defined): 1.4e-4 deg from the published example.

## What is NOT claimed
No precession and no FK4 → FK5 conversion: a J2000 direction passed with "b1950" gives a wrong answer by degrees,
and an FK5 J2000 direction passed with "icrs" differs from other libraries' FK5-based galactic frames by about
0.02 arcsec. The "icrs" system is compared with one library (ERFA) plus its published definition, not two
libraries. At a galactic pole the longitude is undefined and the value returned is arbitrary within [0, 360).
