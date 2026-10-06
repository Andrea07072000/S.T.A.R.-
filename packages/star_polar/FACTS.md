# Published values the tests of star_polar may cite (checked by the reviewer against the computation)

1. Snyder, Map Projections - A Working Manual (USGS Professional Paper 1395), polar stereographic numerical example,
   p. 314: International ellipsoid a = 6378388 m, f = 1 / 297, SOUTH polar aspect, true scale at 71 S, central meridian
   100 W, point 75 S 150 E: x = -1540033.6 m, y = -560526.4 m (printed to 0.1 m: tolerance 0.06 m per coordinate).
   ps_forward(-75, 150, 'S', -100, -71, 1.0, 6378388.0, 1 / 297); ps_inverse of the full-precision result returns (-75, 150)
   within 1e-9 deg. (The scale factor of that example is NOT to be cited: its last printed digit was not confirmed.)
2. UPS definition (DMA TM 8358.2): k0 = 0.994 at the pole, false easting and false northing 2000000 m, central meridian 0.
   The pole itself is (2000000, 2000000) exactly: ups_forward(90, 77) == ('N', 2000000.0, 2000000.0), ups_forward(-90, 5) == ('S', 2000000.0, 2000000.0).

Constants (state them): WGS84_A == 6378137.0, WGS84_F == 1 / 298.257223563, K0_UPS == 0.994, FALSE_UPS == 2000000.0, FAR_SIDE == 60.0.

Values derivable by hand (write the derivation in a comment; do not call them published):
- on a SPHERE (f = 0) with true scale at the pole (lat_ts None) and k0 = 1: rho = 2 a tan(45 deg - |lat| / 2) and the scale is
  1 / cos^2(45 deg - |lat| / 2) = 2 / (1 + sin|lat|). With a = 6378137: ps_forward(60, 0, 'N', 0, None, 1.0, a, 0.0) == (0, -2 a tan(15 deg))
  within 1e-8 m; ps_forward(60, 90, 'N', ...) == (+2 a tan(15 deg), 0); ps_forward(-60, 0, 'S', ...) == (0, +2 a tan(15 deg));
  ps_forward(-60, 90, 'S', ...) == (+2 a tan(15 deg), 0); ps_scale(60, 'N', None, 1.0, a, 0.0) == 1 / cos^2(15 deg); ps_scale(0, 'N', None, 1.0, a, 0.0) == 2.0;
- orientation: from the North pole the central meridian runs towards -y and longitude increases counter-clockwise seen from above (East of the
  central meridian is +x); from the South pole the central meridian runs towards +y and East of it is +x;
- the scale is exactly 1 on the parallel of true scale (ps_scale(71, 'N', 71) == 1, ps_scale(-71, 'S', -71) == 1, within 1e-14), below 1 poleward of
  it and above 1 equatorward; at the pole with lat_ts None it equals k0 (ps_scale(90, 'N') == 1.0, ps_scale(-90, 'S', None, 0.994) == 0.994);
  x, y and the scale are proportional to k0; x and y are proportional to a at fixed f;
- the pole maps to (0, 0) whatever the longitude, and ps_inverse(0, 0, 'N', 45) == (90.0, 45.0), ps_inverse(0, 0, 'S', 45) == (-90.0, 45.0);
- mirror: ps_forward(-lat, lon, 'S', lon0, -lat_ts) has the same x and the opposite y of ps_forward(lat, lon, 'N', lon0, lat_ts) (to 1e-8 m);
- rotating both the longitude and the central meridian by the same angle changes nothing; forward then inverse returns the point within
  1e-9 deg for latitudes from the pole down to 20 deg on its side; the inverse longitude is in [-180, 180);
- UPS: ups_forward picks 'N' for latitude >= 0 and 'S' below; ups_forward(84, 0) is ('N', 2000000.0, n) with n = 1333272.296 within 1e-3 m (south of the
  pole on the page: northing below 2000000); ups_forward(-80, 180) is ('S', 2000000.0, n) with n = 887048.863 within 1e-3 m;
  ups_inverse(pole, *ups_forward(lat, lon)[1:]) returns the point within 1e-9 deg;
- refusals: pole other than 'N' or 'S' ('n', '', None, 1); a latitude more than 60 deg on the far side (ps_forward(-61, 0, 'N') and
  ps_forward(61, 0, 'S') raise; -60 and +60 respectively are accepted); lat_ts in the other hemisphere (-71 with 'N'), on the equator (0) or within
  1 deg of it (0.5 with 'N') raise with "true scale"; longitude or central meridian beyond +-180; k0 outside [0.5, 2]; a outside [1e3, 1e9];
  f outside [0, 0.1]; x or y beyond 10 a.
