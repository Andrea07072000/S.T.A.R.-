# star_polar — polar stereographic projection and UPS

Latitude and longitude to the plane of a polar stereographic projection centred on either pole, and back, with the
point scale factor; and the Universal Polar Stereographic grid on WGS-84. Standard library only.

```python
import star_polar as sp
I = (6378388.0, 1 / 297.0)                                     # International ellipsoid
sp.ps_forward(-75.0, 150.0, 'S', -100.0, -71.0, 1.0, *I)       # (-1540033.61, -560526.39): Snyder's example
sp.ups_forward(85.0, 30.0)                                     # ('N', 2277728.696, 1518959.788)
sp.ups_inverse('N', 2277728.696, 1518959.788)                  # (85.0, 30.0)
```

## Requirements
- R1 `ps_forward`, `ps_inverse`: Snyder's formulas (USGS PP 1395, 21-33 … 21-41) for either pole, with the parallel of
  true scale given by the caller (or the pole) and a scale multiplier k0; the isometric latitude is written without
  cancellation. Reproduce Snyder's numerical example to the printed 0.1 m.
- R2 `ps_scale`: point scale factor, exactly 1 on the parallel of true scale. `ups_forward`, `ups_inverse`: UPS on
  WGS-84 (k0 = 0.994, 2,000,000 m false easting and northing).
- R3 Measured on 600 cases at both poles (latitudes 20 to 89.999 deg, true scale at 50 to 90 deg): forward within
  7e-8 m and inverse within 5e-8 m of PROJ, scale within 6e-11; UPS within 5e-9 m of PyGeodesy (forward and inverse)
  and 4.4e-5 m of PROJ's `ups`.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input, a pole
  other than 'N' or 'S', a latitude more than 60 deg beyond the equator, a parallel of true scale in the other
  hemisphere or within 1 deg of the equator, an ellipsoid or scale outside the stated ranges.

## Evidence
- Published: Snyder, Map Projections — A Working Manual, p. 314; the UPS definition (DMA TM 8358.2). Closed forms
  on the sphere, the orientation of the axes at each pole, the mirror between the hemispheres, by hand.
- `crosscheck_polar.py`: PROJ (through pyproj) and PyGeodesy, each in its own interpreter, each probed first.

## What is NOT claimed
Polar aspect only: no oblique or equatorial stereographic. `ups_forward` does not restrict the latitude to the UPS
zones (north of 84 N, south of 80 S): it is the caller's choice of grid. No MGRS letters. PROJ's `+proj=ups` differs
from PyGeodesy and from this module by up to 4.4e-5 m while PROJ's `+proj=stere` agrees to 7e-8 m: recorded as a
candidate observation about a third-party library, not investigated and not reported.
