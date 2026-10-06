# Published values the tests of star_lcc may cite (checked by the reviewer against the computation)

1. Snyder, Map Projections - A Working Manual (USGS Professional Paper 1395), Lambert conformal conic numerical
   example, p. 296: Clarke 1866 ellipsoid a = 6378206.4 m, e^2 = 0.00676866 (use f = 1 / 294.978698214), standard
   parallels 33 N and 45 N, origin 23 N 96 W, point 35 N 75 W: x = 1894410.9 m, y = 1564649.5 m (printed to 0.1 m:
   tolerance 0.06 m per coordinate) and scale factor k = 0.9970171 (printed to 7 decimals: tolerance 6e-8).
   lcc_forward(35, -75, 33, 45, 23, -96, 6378206.4, 1 / 294.978698214), lcc_scale(35, 33, 45, 6378206.4, 1 / 294.978698214);
   lcc_inverse of the full-precision forward result returns (35, -75) within 1e-9 deg.

Constants (state them): WGS84_A == 6378137.0, WGS84_F == 1 / 298.257223563, MAX_LAT == 89.0, MIN_PARALLEL == 1e-3.

Values derivable by hand (write the derivation in a comment; do not call them published):
- the origin maps to (0, 0): lcc_forward(lat0, lon0, lat1, lat2, lat0, lon0) == (0.0, 0.0) exactly for any cone;
- the scale is exactly 1 on both standard parallels (within 1e-14), below 1 between them and above 1 outside them:
  lcc_scale(33, 33, 45) and lcc_scale(45, 33, 45) are 1; lcc_scale(39, 33, 45) < 1; lcc_scale(60, 33, 45) > 1; lcc_scale(20, 33, 45) > 1;
  for a tangent cone (lat1 == lat2) the scale is 1 on the parallel and above 1 on both sides;
- symmetry about the central meridian: a longitude difference of +d and -d gives x and -x with the same y (to 1e-9 m);
  on the central meridian x == 0 and y increases with latitude for a northern cone;
- the order of the standard parallels does not matter: swapping lat1 and lat2 gives the same result (to 1e-8 m);
- southern cones mirror northern ones: lcc_forward(-lat, lon, -lat1, -lat2, -lat0, lon0) == (x, -y) of the northern case (to 1e-8 m);
- x and y scale linearly with a (at fixed f) (relative 1e-14);
- on a SPHERE (f = 0) with a tangent cone at latitude p (lat1 = lat2 = p): n = sin(p), psi(lat) = asinh(tan(lat)),
  rho(lat) = a cos(p) / n * exp(n * (psi(p) - psi(lat))), and on the central meridian y = rho(lat0) - rho(lat), x = 0;
  rho(p) = a / tan(p) (the cone is tangent). Example to compute in the test: p = lat0 = 40, lat = 50, a = 6378137;
  off the meridian: x = rho sin(n dlon), y = rho(lat0) - rho cos(n dlon);
- the central meridian may sit across the date line: lcc_forward(10, -179, 33, 45, 23, 179) equals lcc_forward(10, 2, 33, 45, 23, 0)
  (a longitude difference of +2 deg), and lcc_inverse returns a longitude in [-180, 180);
- forward then inverse returns the point within 1e-9 deg for points within 60 deg of the central meridian and latitudes from 60 deg on the
  far side of the equator to 85 deg on the near side;
- refusals: standard parallels on opposite sides of the equator (33, -45), on the equator (0, 0), closer than 1e-3 deg to it (0.0005, 10):
  ValueError mentioning "standard parallels"; latitude, lat0 or a parallel beyond +-89; longitude or lon0 beyond +-180; a outside [1e3, 1e9];
  f outside [0, 0.1]; lcc_inverse(0, 1e8, 33, 45, 23, -96) raises with "pole" (the point is behind the cone's apex);
  x or y beyond 1e3 * a in absolute value.
