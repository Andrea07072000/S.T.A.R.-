# star-geodesy

WGS-84 geodetic coordinates to and from ECEF. Standard library only.

## Requirements
- R1 `geodetic_to_ecef(lat_deg, lon_deg, h_m) -> (x, y, z)` in metres (WGS-84, NIMA TR8350.2 constants).
- R2 `ecef_to_geodetic(x, y, z) -> (lat_deg, lon_deg, h_m)`, iterative to 1e-14 rad at ANY altitude; RuntimeError if
  it does not converge; the forward transform of the result closes to < 1 micrometre.
- R3 Invalid input raises `ValueError` (|lat| > 90, Earth's centre).

## How it is verified
Vallado Example 3-3 (printed value carries ~1e-6 deg; our exact solution closes to 0 m), WGS-84 defining points,
3000 round trips from -500 m to 40,000 km including near-pole points, XC-011 vs PROJ and pymap3d near the surface
(8/8 AGREE at 1e-8 deg / 1 mm). Above ~1000 km those two libraries diverge in default use (DISC-GEO-001).

## Not supported / not claimed
Other datums, geoid heights, geodesic distances (see XC-003), any flight use.
