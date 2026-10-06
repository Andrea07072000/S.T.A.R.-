# star_albers — Albers equal-area conic projection

Latitude and longitude to the plane of an Albers equal-area conic with two standard parallels (or one: the tangent
cone), and back, with the two scale factors; on WGS-84 or on an ellipsoid given by the caller.
Standard library only.

```python
import star_albers as sa
C = (6378206.4, 1 / 294.978698214)                                     # Clarke 1866
sa.albers_forward(35.0, -75.0, 29.5, 45.5, 23.0, -96.0, *C)            # (1885472.73, 1535925.00): Snyder's example
sa.albers_scale(35.0, 29.5, 45.5, *C)                                  # (1.0085173, 0.9915546): h along the meridian, k along the parallel
sa.albers_inverse(1885472.7, 1535925.0, 29.5, 45.5, 23.0, -96.0, *C)   # (35.0, -75.0)
```

## Requirements
- R1 `albers_forward` and `albers_inverse`: Snyder's formulas (USGS PP 1395, 14-1 … 14-21), cones in either hemisphere,
  equal parallels for the tangent cone, the central meridian anywhere including across the date line. Reproduce
  Snyder's numerical example to the printed 0.1 m.
- R2 `albers_scale` returns (h, k) with h·k = 1: areas are preserved; k = 1 on the standard parallels. Reproduces
  Snyder's h = 1.0085173 and k = 0.9915546.
- R3 Measured on 600 cones and points on WGS-84 (60 tangent cones): forward within 1.9e-6 m of PROJ and 9.1e-7 m of
  PyGeodesy; inverse within 2.6e-6 m of the starting point; parallel scale within 9e-14 of PyGeodesy and 1.3e-9 of
  PROJ (which differentiates numerically).
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  latitudes beyond ±89, longitudes beyond ±180, standard parallels on opposite sides of the equator or within
  1e-3 deg of it, an ellipsoid outside the stated ranges, a point outside the image of the cone.

## Evidence
- Published: Snyder, Map Projections — A Working Manual, p. 292 (coordinates and both scale factors). The closed form
  on the sphere for a tangent cone, the equal-area identity, the symmetries and the origin, by hand.
- `crosscheck_albers.py`: PROJ (through pyproj) and PyGeodesy (Karney's formulation, not Snyder's), each in its own
  interpreter, each probed on Snyder's example.

## What is NOT claimed
No false easting or northing, no named national grids. The cone constant is computed as a difference between the two
standard parallels: when they are very close (0.04 deg apart in the worst case measured) about four digits are
lost and the difference from the libraries reaches 2 micrometres; PyGeodesy's formulation does not have this loss.
The accuracy stated is agreement with two libraries, not with a survey.
