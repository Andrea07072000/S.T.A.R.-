# star_lcc — Lambert conformal conic projection

Latitude and longitude to the plane of a Lambert conformal conic with two standard parallels (or one: the tangent
cone), and back, with the point scale factor; on WGS-84 or on an ellipsoid given by the caller.
Standard library only.

```python
import star_lcc as sl
C = (6378206.4, 1 / 294.978698214)                                  # Clarke 1866
sl.lcc_forward(35.0, -75.0, 33.0, 45.0, 23.0, -96.0, *C)            # (1894410.90, 1564649.48): Snyder's example
sl.lcc_scale(35.0, 33.0, 45.0, *C)                                  # 0.9970171
sl.lcc_inverse(1894410.9, 1564649.5, 33.0, 45.0, 23.0, -96.0, *C)   # (35.0, -75.0)
```

## Requirements
- R1 `lcc_forward` and `lcc_inverse`: Snyder's formulas (USGS PP 1395, 15-1 … 15-11) with the isometric latitude
  written without cancellation, cones in either hemisphere, equal parallels for the tangent cone, the central
  meridian anywhere including across the date line. Reproduce Snyder's numerical example to the printed 0.1 m.
- R2 `lcc_scale`: the point scale factor, exactly 1 on the standard parallels. Reproduces Snyder's k = 0.9970171.
- R3 Measured on 600 cones and points on WGS-84 (60 tangent cones): forward within 8e-7 m per Earth radius of plane
  distance of PROJ and 7e-6 m of PyGeodesy; inverse within 7e-7 m (PROJ's plane coordinates) and 6e-6 m
  (PyGeodesy's) of the starting point; scale within 1.2e-9 of PROJ (which differentiates numerically).
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  latitudes beyond ±89, longitudes beyond ±180, standard parallels on opposite sides of the equator or within
  1e-3 deg of it, an ellipsoid outside the stated ranges, a point at or beyond the apex of the cone.

## Evidence
- Published: Snyder, Map Projections — A Working Manual, p. 296 (coordinates and scale factor). The closed form on
  the sphere for a tangent cone, the symmetries and the origin, by hand.
- `crosscheck_lcc.py`: PROJ (through pyproj) and PyGeodesy, each in its own interpreter, each probed on Snyder's example.

## What is NOT claimed
No false easting or northing, no scale reduction k0 (the 1SP variant with k0 ≠ 1 is not offered), no named
national grids. PyGeodesy was compared on 553 of the 600 cases: on the 47 whose longitude and central meridian lie
on opposite sides of the date line its result differs by up to 4.7e7 m while PROJ and this module agree; that is
recorded as a candidate observation about a third-party library, not verified further and not reported. For a
tangent cone PyGeodesy takes the origin latitude as the parallel, so those cases were generated with lat0 = lat1.
