# Published values the tests of star_albers may cite (checked by the reviewer against the computation)

1. Snyder, Map Projections - A Working Manual (USGS Professional Paper 1395), Albers equal-area conic numerical example,
   p. 292: Clarke 1866 ellipsoid a = 6378206.4 m, e^2 = 0.00676866 (use f = 1 / 294.978698214), standard parallels 29.5 N
   and 45.5 N, origin 23 N 96 W, point 35 N 75 W: x = 1885472.7 m, y = 1535925.0 m (printed to 0.1 m: tolerance 0.06 m per
   coordinate), meridian scale h = 1.0085173 and parallel scale k = 0.9915546 (printed to 7 decimals: tolerance 6e-8).
   albers_forward(35, -75, 29.5, 45.5, 23, -96, 6378206.4, 1 / 294.978698214); albers_scale(35, 29.5, 45.5, 6378206.4, 1 / 294.978698214) == (h, k);
   albers_inverse of the full-precision forward result returns (35, -75) within 1e-9 deg.

Constants (state them): WGS84_A == 6378137.0, WGS84_F == 1 / 298.257223563, MAX_LAT == 89.0, MIN_PARALLEL == 1e-3.

Values derivable by hand (write the derivation in a comment; do not call them published):
- the origin maps to (0, 0): albers_forward(lat0, lon0, lat1, lat2, lat0, lon0) == (0.0, 0.0) exactly for any cone;
- equal area: albers_scale returns (h, k) with h * k == 1 within 1e-14 at every latitude; k == 1 (and h == 1) on both standard parallels within 1e-14;
  between the standard parallels k < 1 < h, outside them k > 1 > h (e.g. latitudes 39, 60 and 20 with parallels 29.5 and 45.5);
- symmetry about the central meridian: a longitude difference of +d and -d gives x and -x with the same y (to 1e-9 m); on the central meridian x == 0
  and y increases with latitude for a northern cone;
- the order of the standard parallels does not matter (to 1e-8 m); southern cones mirror northern ones:
  albers_forward(-lat, lon, -lat1, -lat2, -lat0, lon0) == (x, -y) of the northern case (to 1e-8 m); x and y scale linearly with a at fixed f;
- on a SPHERE (f = 0) with a tangent cone at latitude p (lat1 = lat2 = p): n = sin(p), rho(lat) = a sqrt(1 + sin^2(p) - 2 sin(p) sin(lat)) / sin(p),
  and on the central meridian y = rho(lat0) - rho(lat), x = 0; rho(p) = a / tan(p); off the meridian x = rho sin(n dlon), y = rho(lat0) - rho cos(n dlon).
  Example to compute in the test: p = lat0 = 40, lat = 50, a = 6378137 (tolerance 1e-7 m);
- equal area can be checked numerically on the sphere: the area of the image of a small latitude-longitude cell equals the area of the cell on
  the sphere, a^2 dlon (sin(lat_b) - sin(lat_a)): the image is an annular sector of area (n dlon / 2) (rho_a^2 - rho_b^2); this identity is exact;
- the central meridian may sit across the date line: albers_forward(10, -179, 29.5, 45.5, 23, 179) equals albers_forward(10, 2, 29.5, 45.5, 23, 0),
  and albers_inverse returns a longitude in [-180, 180);
- forward then inverse returns the point within 1e-9 deg for points within 60 deg of the central meridian and latitudes from 60 deg on the far side
  of the equator to 85 deg on the near side;
- refusals: standard parallels on opposite sides of the equator (29.5, -45.5), on the equator (0, 0), closer than 1e-3 deg to it (0.0005, 10): ValueError
  mentioning "standard parallels"; latitude, lat0 or a parallel beyond +-89; longitude or lon0 beyond +-180; a outside [1e3, 1e9]; f outside [0, 0.1];
  albers_inverse(0, 5e7, 29.5, 45.5, 23, -96) raises with "outside the image"; x or y beyond 10 a in absolute value.
