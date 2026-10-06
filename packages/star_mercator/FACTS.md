# Published values the tests of star_mercator may cite (checked by the reviewer against the computation)

1. Snyder, Map Projections - A Working Manual (USGS Professional Paper 1395), Mercator numerical example, p. 266:
   Clarke 1866 ellipsoid a = 6378206.4 m, e^2 = 0.00676866 (use f = 1 / 294.978698214), central meridian 180, point
   35 N 75 W: x = 11688673.7 m (printed to 0.1 m: tolerance 0.06 m) and scale factor k = 1.2194146 (tolerance 6e-8).
   mercator_forward(35, -75, 180, 0, 6378206.4, 1 / 294.978698214)[0]; mercator_scale(35, 0, 1 / 294.978698214).
   Do NOT cite the y of that example as published: the reviewer could not confirm its last digit. (The module gives 4139145.66 m.)
2. EPSG:3857 (Web Mercator): sphere formulas with radius 6378137 m; the map is a square: x = +-pi * 6378137 = +-20037508.342789244 m at
   longitude +-180, and y reaches the same value at latitude 85.0511287798066 deg (= atan(sinh(pi)) in degrees).

Constants (state them): WGS84_A == 6378137.0, WGS84_F == 1 / 298.257223563, MAX_LAT == 89.5, MAX_TS == 80.0.

Values derivable by hand (write the derivation in a comment; do not call them published):
- the origin: mercator_forward(0, lon0, lon0) == (0.0, 0.0) and web_mercator_forward(0, 0) == (0.0, 0.0);
- on a SPHERE (f = 0, lat_ts = 0): x = a * dlon in radians, y = a * asinh(tan(lat)) = a * ln(tan(45 deg + lat / 2)), scale = 1 / cos(lat):
  mercator_forward(45, 90, 0, 0, 6378137.0, 0.0) == (a * pi / 2, a * asinh(1)) within 1e-8 m; mercator_scale(60, 0, 0.0) == 2.0 within 1e-14;
  with a latitude of true scale t on the sphere everything is multiplied by cos(t): mercator_scale(0, 60, 0.0) == 0.5, and the scale is 1 at lat = +-t;
- web_mercator_forward(lat, lon) equals mercator_forward(lat, lon, 0, 0, 6378137.0, 0.0) (the sphere) to 1e-9 m, and differs from the ellipsoidal
  mercator_forward(lat, lon) in y by kilometres at mid-latitudes (the ellipsoidal y is 32196.59 m smaller at 48.86 N, 2.29 E) while x is identical;
- on the ellipsoid the scale is 1 on the parallels +-lat_ts (mercator_scale(45, 45) == 1 == mercator_scale(-45, 45), within 1e-14), below 1 between them
  and above 1 poleward; mercator_scale(0, 0) == 1.0;
- antisymmetry: y(-lat) == -y(lat) exactly; x depends only on the longitude difference and on lat_ts; x and y are proportional to a at fixed f;
- the longitude difference is reduced to [-180, 180): mercator_forward(10, -179, 179) equals mercator_forward(10, 2, 0); a point half a turn away has
  x = -pi a k0 (longitude 180 with lon0 = 0 is reduced to -180); the inverses return longitudes in [-180, 180), so the image of +180 comes back as -180;
- rhumb lines are straight: three points on a line of constant bearing (e.g. computed by stepping psi and longitude in a fixed ratio) are collinear in the plane;
  simpler exact property: y(lat) - y(0) is strictly increasing with lat and its derivative with respect to lat (radians) is a k0 times the
  meridian-to-parallel factor (1 - e^2) / ((1 - e^2 sin^2 lat) cos lat);
- forward then inverse returns the point within 1e-9 deg for latitudes within +-89.5 (the limits themselves included), for the ellipsoid, the sphere and Web Mercator;
- refusals: latitude beyond +-89.5 ("latitude"); longitude or central meridian beyond +-180; lat_ts beyond +-80 ("true scale"); a outside [1e3, 1e9]; f outside
  [0, 0.1]; in the inverses x beyond pi a k0 ("x") and y beyond the image of latitude 89.5 ("y"), e.g. mercator_inverse(0, 1e9) and web_mercator_inverse(0, 1e9).
