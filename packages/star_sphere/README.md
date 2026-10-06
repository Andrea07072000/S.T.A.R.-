# star_sphere — angles between directions on the sphere

Separation, position angle and the point at a given angle and distance, for any pair of (longitude, latitude)
directions: right ascension and declination, azimuth and elevation, or places on a spherical body.
Standard library only.

```python
import star_sphere as ss
ss.separation_deg(213.9154, 19.1825, 201.2983, -11.1614)     # 32.7930 deg: Arcturus to Spica
ss.position_angle_deg(213.9154, 19.1825, 201.2983, -11.1614) # direction of Spica seen from Arcturus, North through East
ss.offset(10.0, 20.0, 45.0, 2.5)                             # the point 2.5 deg away towards North-East
```

## Requirements
- R1 `separation_deg` in [0, 180] with the arc-tangent formula: nearby directions (1e-12 deg) and nearly antipodal
  ones keep their digits. Reproduces Meeus Example 17.a (32.7930 deg).
- R2 `position_angle_deg` in [0, 360), from North through East; `offset(lon, lat, position_angle, distance)` returns
  (longitude in [0, 360), latitude) and is the inverse of the two.
- R3 Measured on 600 pairs (300 random, 150 down to 1e-6 deg apart, 150 down to 1e-6 deg from the antipode):
  separation within 3e-14 deg of ERFA and astropy, position angle within 1e-15 rad of displacement, offset points
  within 4e-13 deg of astropy.
- R4 Every function returns finite floats in those ranges or raises `ValueError`: non-numeric, boolean, NaN or
  infinite input, latitude outside [-90, 90], longitude or position angle outside [-360, 360], distance outside
  [0, 180]. For coincident directions the position angle is undefined and returned as 0.

## Evidence
- Published: Meeus, Astronomical Algorithms, Example 17.a. Spherical triangles solved by hand (quarter circles,
  right-angled triangles with Napier's rule, the antipode, a path over the pole).
- `crosscheck_sphere.py`: ERFA and astropy, each in its own interpreter, first probed on the published example.

## What is NOT claimed
A sphere: for distances on the Earth's ellipsoid use `star_geodesic` (the difference reaches 0.5 %). No proper motion,
aberration or refraction: the directions are taken as given.
