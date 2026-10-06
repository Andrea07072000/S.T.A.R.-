# star_topo — look angles from a ground site

ECEF ↔ local East-North-Up ↔ azimuth / elevation / range on WGS-84. Standard library only.

```python
import star_topo
az, el, rng = star_topo.ecef_to_aer(x, y, z, site_lat_deg, site_lon_deg, site_h_m)   # deg, deg, m
x, y, z = star_topo.aer_to_ecef(az, el, rng, site_lat_deg, site_lon_deg, site_h_m)
```

## Requirements
- R1 `ecef_to_enu` / `enu_to_ecef`: East, North, Up in metres at a site given by geodetic latitude, longitude (deg)
  and ellipsoidal height (m) on WGS-84; "up" is the ellipsoid normal. Reproduces the EPSG Guidance Note 7-2 example
  (method 9836) to the printed millimetre.
- R2 `enu_to_aer` / `aer_to_enu`: azimuth from North towards East in [0, 360), elevation from the horizontal plane in
  [-90, 90], range in metres. At the zenith or nadir the azimuth is returned as 0.0.
- R3 `ecef_to_aer` / `aer_to_ecef` compose the two; a round trip returns the starting point and the range equals the
  ECEF distance between site and target.
- R4 Every function returns three finite floats or raises `ValueError`: non-numeric, boolean, NaN, infinite or
  |value| >= 1e300 input; latitude or elevation outside [-90, 90]; longitude or azimuth outside [-360, 360]; site
  height at or below -b (the Earth's centre under the poles); zero or negative range; target on the site; overflow.

## Evidence
- Published: EPSG Guidance Note 7-2 example, forward, reverse and origin (tests).
- Three independent libraries, each in its own interpreter, first probed on the published example
  (`crosscheck_topo.py`, 400 site/target pairs over the globe, poles and antimeridian included, targets from 1 m to
  40 000 km): pymap3d within 7.5e-9 m, PROJ (`+proj=topocentric`) within 1.5e-8 m, PyGeodesy within 1.8e-8 m.
- Axes checked by hand at the equator and at both poles.

## What is NOT claimed
Geometry only: no atmospheric refraction, no light-time, no Earth rotation during signal travel, no terrain mask.
The target must already be in the same Earth-fixed frame as the site.
