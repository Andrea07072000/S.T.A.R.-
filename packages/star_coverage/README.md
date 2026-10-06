# star_coverage — what a satellite sees, and from where it is seen

Coverage geometry over a spherical body: Earth-central angle, nadir angle, slant range, covered fraction, footprint
area, and the elevation of the satellite from a ground point. Standard library only.

```python
import star_coverage as sc
sc.central_angle_deg(35786.0)            # 81.30 deg: half-width of the geostationary field of view
sc.slant_range(550.0, 25.0)              # km from a user who needs 25 deg of elevation to a satellite at 550 km
sc.coverage_fraction(550.0, 25.0)        # fraction of the Earth served by one such satellite
```

## Requirements
- R1 `central_angle_deg`, `nadir_angle_deg`, `slant_range`, `coverage_fraction`, `footprint_area` for an altitude and
  a minimum elevation; `elevation_deg(altitude, central_angle)` is the inverse relation (negative below the horizon).
  Default radius 6378.137 km; `radius=` for another body or unit. The three angles add up to 90 degrees.
- R2 Reproduces the textbook geostationary figures (81.3 deg, 8.7 deg, 41 679 km, 42.4 % of the surface, 76.3 deg at
  5 deg of elevation) and the 2294 km horizon of a 400 km orbit.
- R3 Measured against pymap3d and PROJ on a sphere (400 cases, 200 km to 400 000 km): elevation within 8e-14 deg,
  slant range within 4e-15 relative, central angle within 3e-14 deg. The formulas are written to keep precision at
  both ends: 1 mm above the ground the slant range is right to 1e-14 (the textbook form loses seven digits there),
  and at 1e12 km the central angle stays below 90 degrees.
- R4 Every function returns a finite float or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  altitude <= 0, radius <= 0, minimum elevation outside [0, 90], central angle outside [0, 180], an altitude so small
  or so large against the radius that the ratio is not representable.

## Evidence
- Textbook figures; the triangle centre - ground point - satellite solved independently with the laws of cosines and
  sines; the exact cap area 2 pi R^2 h / (R + h) at zero elevation.
- `crosscheck_coverage.py`: pymap3d (spherical ellipsoid) and PROJ (`+proj=topocentric` on a sphere), each in its own
  interpreter, first probed on the geostationary zenith and horizon.

## What is NOT claimed
A sphere: on the real Earth the horizon distance changes by up to about 0.3 % with latitude. No refraction, terrain
or antenna pattern; no constellation design (number of satellites, overlap, revisit).
