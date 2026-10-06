# star_mercator — Mercator on the ellipsoid, and Web Mercator

Latitude and longitude to the Mercator plane and back, with the point scale factor, on WGS-84 or on an ellipsoid
given by the caller; and the Web Mercator of online maps, kept separate because it is a different projection.
Standard library only.

```python
import star_mercator as sm
C = (6378206.4, 1 / 294.978698214)                       # Clarke 1866
sm.mercator_forward(35.0, -75.0, 180.0, 0.0, *C)         # (11688673.72, 4139145.66): Snyder's example
sm.mercator_scale(35.0, 0.0, C[1])                       # 1.2194146
sm.web_mercator_forward(48.8582, 2.2945)                 # (255422.57, 6250835.06): EPSG:3857
```

## Requirements
- R1 `mercator_forward`, `mercator_inverse`: the conformal Mercator of the ellipsoid, y = a·k0·ψ with ψ the isometric
  latitude written without cancellation, any central meridian, an optional latitude of true scale. Reproduce the x of
  Snyder's numerical example (USGS PP 1395, p. 266) to the printed 0.1 m.
- R2 `mercator_scale`: point scale factor, 1 on the parallels of true scale. Reproduces Snyder's k = 1.2194146.
  `web_mercator_forward`, `web_mercator_inverse`: EPSG:3857.
- R3 Measured on 600 cases on WGS-84 (latitudes to ±89, true scale to ±80): forward within 5.5e-8 m and inverse within
  6e-8 m of PROJ; y within 7.5e-9 m of PyGeodesy's isometric latitude; Web Mercator within 3e-8 m of PROJ and
  PyGeodesy; scale within 7.5e-8 of PROJ (whose factors are numerical).
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  latitude beyond ±89.5, latitude of true scale beyond ±80, longitudes beyond ±180, an ellipsoid outside the stated
  ranges, plane coordinates beyond the image. Inverse longitudes are in [-180, 180).

## Evidence
- Published: Snyder, Map Projections — A Working Manual, p. 266 (x and k); the EPSG:3857 square. Closed forms on the
  sphere, the antisymmetry, the parallels of true scale, by hand.
- `crosscheck_mercator.py`: PROJ (through pyproj) and PyGeodesy, each in its own interpreter, each probed first.

## What is NOT claimed
Web Mercator is not conformal and its y differs from the ellipsoidal Mercator by tens of kilometres at
mid-latitudes: do not mix them. PyGeodesy has no ellipsoidal Mercator: it confirms the isometric latitude (hence y)
and Web Mercator, not x or the scale; and it refuses Web Mercator beyond 85.05 deg, so 19 of the 600 cases were
compared with PROJ only. The y of Snyder's example is not cited: its last printed digit could not be confirmed.
At longitude 180 exactly `web_mercator_forward` returns the East edge (+20037508.34 m) while `mercator_forward`
reduces the difference from its central meridian to [-180, 180) and returns the West edge. No rhumb-line distances or bearings.
