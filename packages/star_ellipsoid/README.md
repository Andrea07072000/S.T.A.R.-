# star_ellipsoid — the WGS-84 ellipsoid as a surface

Radii of curvature, geocentric radius, auxiliary latitudes and the meridian arc at a geodetic latitude.
Standard library only.

```python
import math, star_ellipsoid as se
se.meridian_radius(45.0) * math.pi / 180                                # metres in one degree of latitude at 45 N
se.prime_vertical_radius(45.0) * math.cos(math.radians(45.0)) * math.pi / 180   # metres in one degree of longitude there
se.meridian_arc(45.0)                                                   # metres from the equator along the meridian
```

## Requirements
- R1 `meridian_radius`, `prime_vertical_radius`, `gaussian_radius`, `geocentric_radius` (metres) at a geodetic latitude
  in degrees; WGS-84 constants as published.
- R2 `geocentric_latitude`, `parametric_latitude`, `rectifying_latitude` (degrees); `meridian_arc` (metres from the
  equator, negative in the south; Helmert's series to n^5) and `MERIDIAN_QUADRANT` = 10 001 965.729 m.
- R3 Measured on 505 latitudes against pymap3d and PyGeodesy: radii within 5e-16 relative, auxiliary latitudes within
  5e-14 deg, meridian arc within 4e-9 m.
- R4 Every function returns a finite float or raises `ValueError`: non-numeric, boolean, NaN or infinite input, and
  any latitude outside [-90, 90] (not wrapped).

## Evidence
- Published WGS-84 constants (b, e^2, polar radius of curvature, meridian quadrant).
- The meridian arc integrated numerically from the meridian radius in the tests (no series involved).
- `crosscheck_ellipsoid.py`: pymap3d and PyGeodesy, each in its own interpreter, first probed on published constants.
  It found a real defect in the first version: the sine terms of the arc were scaled by the wrong factor (1.1 cm off).

## What is NOT claimed
The ellipsoid, not the Earth: no geoid, no terrain height. WGS-84 only (GRS80 differs in the tenth digit of f).
