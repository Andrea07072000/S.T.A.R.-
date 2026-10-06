# Published values the tests of star_horizon may cite (checked by the reviewer against the computation)

1. Meeus, Astronomical Algorithms (2nd ed.), Example 13.b: Venus, local hour angle H = 64.352133 deg, declination
   delta = -6.719892 deg, observer latitude phi = +38.921389 deg, has azimuth A = 68.0337 deg measured from the
   SOUTH westward, i.e. 248.0337 deg from North through East, and altitude h = 15.1249 deg.
   Printed to 1e-4 deg: tolerance 6e-5 deg per coordinate.

Conventions of the module (not "published": state them): azimuth from North through East in [0, 360); hour angle
positive West of the meridian, returned in (-180, 180]; parallactic angle in (-180, 180], positive West of the meridian
for an observer in northern mid-latitudes looking at an object south of the zenith.

Values that can be derived by hand (write the derivation in a comment, do not call them published):
- an object on the meridian (H = 0) south of the zenith at latitude phi has azimuth 180 and elevation 90 - phi + delta;
  north of the zenith (delta > phi) it has azimuth 0 and elevation 90 + phi - delta;
- the celestial pole (delta = +90) has azimuth 0 and elevation phi for phi > 0;
- an object on the celestial equator (delta = 0) at H = +90 deg is exactly at the West point: azimuth 270, elevation 0;
  at H = -90 deg it is at the East point: azimuth 90, elevation 0;
- at the zenith (H = 0, delta = phi) the elevation is 90 and the azimuth is returned as 0;
- on the meridian the parallactic angle is 0 for an object south of the zenith (phi > delta, northern observer) and
  180 for an object between the zenith and the pole;
- the parallactic angle is odd in the hour angle: q(-H) = -q(H);
- the two conversions are the same construction and are inverse of each other; the elevation obeys
  sin(el) = sin(phi) sin(delta) + cos(phi) cos(delta) cos(H).
