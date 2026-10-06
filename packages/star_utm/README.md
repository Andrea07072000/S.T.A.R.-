# star_utm — transverse Mercator and UTM coordinates

Latitude and longitude to transverse Mercator x, y and to UTM zone, easting and northing, and back, on WGS-84 or on
an ellipsoid given by the caller. Standard library only.

```python
import star_utm as su
su.utm_forward(48.8582, 2.2945)                     # (31, 'N', 448251.795, 5411932.678)
su.utm_inverse(31, 'N', 448251.795, 5411932.678)    # (48.8582, 2.2945)
su.tm_forward(40.5, -73.5, -75.0, 6378206.4, 1 / 294.978698214)   # (127106.47, 4484124.43): Snyder's example
```

## Requirements
- R1 `tm_forward` and `tm_inverse`: Krueger's series to n^4 (Karney 2011) about a central meridian, with scale k0
  and no false origin, for any ellipsoid with flattening up to 0.1. Reproduces Snyder's numerical example
  (USGS PP 1395, p. 269) to the printed 0.1 m.
- R2 `utm_zone`, `utm_forward`, `utm_inverse`: WGS-84, k0 = 0.9996, false easting 500000 m, false northing
  10000000 m in the South, 6-degree zones from 180 W; a zone can be forced.
- R3 Measured: 600 points in their zone within 2e-7 m (forward) and 6e-8 m (inverse) of PROJ and PyGeodesy; 300
  points 3 to 12 deg from the central meridian within 2.5e-7 m of PROJ.
- R4 Every function returns its result or raises `ValueError`: non-numeric, boolean, NaN or infinite input, latitude
  outside [-90, 90] (UTM: [-80, 84]), longitude outside [-180, 180], a point more than 12 deg from the central
  meridian, an ellipsoid or scale outside the stated ranges, a zone not an integer in 1…60, a hemisphere other
  than 'N' or 'S', coordinates beyond the pole of the projection.

## Evidence
- Published: Snyder, Map Projections — A Working Manual, p. 269. Closed forms on the sphere (f = 0), the origin, the
  pole, the symmetries, by hand.
- `crosscheck_utm.py`: PROJ (through pyproj) and PyGeodesy, each in its own interpreter, each probed first.

## What is NOT claimed
The Norway and Svalbard exceptions of the MGRS grid are NOT applied: `utm_zone` is the plain 6-degree rule (one of
600 random points fell in an exception zone and was compared in the other library's zone). No MGRS letters, no UPS
for the polar caps, no datum transformation. Beyond 12 deg from the central meridian the functions refuse: the
accuracy there was not measured. The accuracy stated is agreement with two libraries, not with a survey.
