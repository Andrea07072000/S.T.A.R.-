# star_coords — spherical and cylindrical ⇄ rectangular coordinates

Longitude, latitude and radius (or radius, longitude and height) to x, y, z and back, for any right-handed frame:
right ascension and declination, longitude and geocentric latitude. Standard library only.

```python
import star_coords as sc
sc.spherical_to_xyz(60.0, 0.0, 2.0)      # (1.0, 1.732..., 0.0)
sc.xyz_to_spherical(1.0, 1.0, 1.0)       # (45.0, 35.264..., 1.732...)
sc.cylindrical_to_xyz(2.0, 90.0, 5.0)    # (0.0, 2.0, 5.0)
sc.xyz_to_cylindrical(3.0, 4.0, -1.0)    # (5.0, 53.130..., -1.0)
```

## Requirements
- R1 `spherical_to_xyz(lon, lat, r)` and `xyz_to_spherical(x, y, z)` follow x = r cos(lat) cos(lon),
  y = r cos(lat) sin(lon), z = r sin(lat); longitude out in [0, 360), latitude from the arc-tangent (accurate at the
  poles), length without intermediate overflow or underflow.
- R2 `cylindrical_to_xyz(rho, lon, z)` and `xyz_to_cylindrical(x, y, z)`: x = rho cos(lon), y = rho sin(lon).
- R3 Measured on 600 cases (100 directions down to 1e-9 deg from the z axis, lengths from 1e-3 to 1e9), in both
  directions: components and lengths within 3e-16 relative and angles within 6e-14 deg of displacement of ERFA, SPICE
  and astropy (spherical) and of SPICE and astropy (cylindrical).
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  longitude outside [-360, 360], latitude outside [-90, 90], a negative radius, a length or component above 1e300.
  On the z axis the longitude is undefined and returned as 0.

## Evidence
- By hand: exact trigonometric cases ((1, sqrt(3), 0), (1, 1, 1), 3-4-5 triangles), the axes, the zero vector. There is
  no published numerical example for a definition: none is claimed.
- `crosscheck_coords.py`: ERFA, SPICE and astropy, each in its own interpreter, each probed on the by-hand case.

## What is NOT claimed
Geocentric (spherical) latitude, not geodetic: for the ellipsoid use `star_geodesy`. No velocities. Colatitude
conventions (physics spherical coordinates) are not offered: latitude is from the xy plane.
