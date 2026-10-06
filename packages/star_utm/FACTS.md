# Published values the tests of star_utm may cite (checked by the reviewer against the computation)

1. Snyder, Map Projections - A Working Manual (USGS Professional Paper 1395), transverse Mercator numerical example,
   p. 269: Clarke 1866 ellipsoid a = 6378206.4 m, e^2 = 0.00676866 (use f = 1 / 294.978698214), central meridian
   75 deg W, k0 = 0.9996, latitude 40.5 N, longitude 73.5 W: x = 127106.5 m, y = 4484124.4 m (printed to 0.1 m:
   tolerance 0.06 m per coordinate). tm_forward(40.5, -73.5, -75.0, 6378206.4, 1 / 294.978698214) reproduces it, and
   tm_inverse of the full-precision result returns the latitude and longitude within 1e-9 deg.

Constants (exact by definition, state them): WGS84_A == 6378137.0, WGS84_F == 1 / 298.257223563, K0_UTM == 0.9996,
FALSE_EASTING == 500000.0, FALSE_NORTHING == 10000000.0, MAX_DLON == 12.0.

Values derivable by hand (write the derivation in a comment; do not call them published):
- on a SPHERE (f = 0) with k0 = 1 the transverse Mercator has closed forms: on the central meridian y = a * latitude in
  radians (tm_forward(45, 0, 0, 6378137.0, 0.0, 1.0) == (0.0, 6378137 * pi / 4) within 1e-8 m), and on the equator
  x = a * atanh(sin(dlon)) (tm_forward(0, 1, 0, 6378137.0, 0.0, 1.0)[0] == 6378137 * atanh(sin(1 deg)) within 1e-8 m, y == 0);
  in general, for the sphere: x = a * atanh(cos(lat) sin(dlon)), y = a * atan2(tan(lat), cos(dlon));
- the origin: tm_forward(0, 3, 3) == (0.0, 0.0); tm_inverse(0, 0, 3) == (0.0, 3.0);
- symmetry: changing the sign of the longitude difference changes the sign of x only; changing the sign of the latitude
  changes the sign of y only (to 1e-9 m); x and y scale linearly with k0 and with a (at fixed f);
- the pole: tm_forward(90, 0, 0) has x == 0 within 1e-6 m and y = 9997964.943 m within 1e-3 m (k0 times the WGS-84 quarter
  meridian 10001965.729 m, a well-known length); tm_forward(-90, 10, 3) has the opposite y; tm_inverse(0, 9997964.943021, 3)
  has latitude 90 within 1e-6 deg;
- UTM: utm_forward(0, 3) == (31, 'N', 500000.0, 0.0) (within 1e-9 m); utm_inverse(31, 'N', 500000, 0) == (0.0, 3.0);
  a point just south of the equator is 'S' with northing just below 10000000: utm_forward(-1e-9, 3.0) is (31, 'S', 500000.0, n)
  with 9999999.9998 < n < 10000000; utm_inverse(31, 'S', 500000, 10000000) == (0.0, 3.0);
  at the equator on a zone boundary the easting is 166021.443 m within 1e-3 m (utm_forward(0, 0) is zone 31, 'N');
  utm_forward and utm_inverse are inverse of each other within 1e-9 deg anywhere in a zone;
- zones: utm_zone(-180) == 1, utm_zone(-174.0000001) == 1, utm_zone(-174) == 2, utm_zone(-0.0000001) == 30, utm_zone(0) == 31,
  utm_zone(179.999) == 60, utm_zone(180) == 60; the central meridian of zone z is 6 z - 183;
  a forced zone is honoured: utm_forward(60, 9, 31) has zone 31 and easting 834359.668 m within 1e-3 m (9 deg E is 6 deg from 3 deg E);
- the central meridian may sit across the date line: tm_forward(10, -179, 179) equals tm_forward(10, 2, 0) (a longitude difference of +2 deg);
  tm_inverse then returns a longitude in [-180, 180);
- limits: 12 deg from the central meridian accepted, 12.0001 refused ("central meridian"); UTM latitude -80 and 84 accepted,
  -80.0000001 and 84.0000001 refused; tm latitude +-90 accepted; a in [1e3, 1e9], f in [0, 0.1], k0 in [0.5, 2];
  zone must be an int in 1..60 (True, 0, 61, 31.0 refused; None means "from the longitude" in utm_forward only);
  hemisphere exactly 'N' or 'S' ('n', '', None refused); northing in [0, 10000000]; tm_inverse refuses y beyond the pole
  (tm_inverse(0, 1.0005e7, 3) raises with "pole") and x beyond 0.25 a k0, y beyond 1.6 a k0.
