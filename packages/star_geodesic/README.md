# star_geodesic — distance and azimuth on the WGS-84 ellipsoid

The inverse problem (distance and azimuths between two points) and the direct problem (point reached from a start,
azimuth and distance). Standard library only.

```python
import star_geodesic
distance_m, az1, az2 = star_geodesic.inverse(lat1, lon1, lat2, lon2)
lat2, lon2, az2 = star_geodesic.direct(lat1, lon1, az1, distance_m)
```

## Requirements
- R1 `inverse(lat1, lon1, lat2, lon2)`: geodesic length in metres and its azimuth at both ends in the direction of
  travel (degrees from North towards East, in [0, 360)). Reproduces the published line Flinders Peak - Buninyong
  (54972.271 m) within 0.2 mm and 0.004 arcsec.
- R2 `direct(lat1, lon1, azimuth1_deg, distance_m)`: latitude, longitude in [-180, 180) and azimuth at the point
  reached, for distances from 0 to 20 000 km.
- R3 Measured against PROJ, GeographicLib and PyGeodesy (exact) on 840 problems: distance within 0.08 mm at any
  length, 2 nm below 1 km; azimuth within 0.0003 arcsec; direct position within 0.07 mm. Two iterations are run after
  the 1e-12 rad tolerance is met: without them a 0.7 m line was 2.7 micrometres off.
- R4 Every call returns three finite floats or raises: `ValueError` for non-numeric, boolean, NaN, infinite input,
  latitude outside [-90, 90], longitude or azimuth outside [-360, 360], distance outside [0, 20 000 km];
  `RuntimeError` for antipodal points (the geodesic is not unique) and when the iteration does not converge within
  200 steps (nearly antipodal points). An unconverged value is never returned. Coincident points give (0, 0, 0).

## Evidence
- Published: Flinders Peak - Buninyong (Geoscience Australia / ICSM GDA technical manual), inverse and direct.
- Three independent implementations, each in its own interpreter and first probed on the published line
  (`crosscheck_geodesic.py`): PROJ (C), GeographicLib (Python port), PyGeodesy GeodesicExact (elliptic integrals).
- Equator and meridian quadrant checked against closed forms.

## What is NOT claimed
Vincenty's method, not Karney's: points closer than about half a degree to the antipode are refused, not solved (the
40 pairs within 2 degrees of the antipode in the corpus all converged). No geoid, no height: lines on the ellipsoid.
