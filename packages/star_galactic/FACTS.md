# Published values the tests of star_galactic may cite (checked by the reviewer against the computation)

1. Meeus, Astronomical Algorithms (2nd ed.), Example 13.b: Nova Serpentis 1978, B1950.0 equatorial
   alpha = 267.248917 deg (17h48m59.74s), delta = -14.718944 deg (-14 deg 43' 08.2"), has galactic
   l = 12.9593 deg, b = +6.0463 deg in the IAU 1958 system ("b1950"). Printed to 1e-4 deg: tolerance 6e-5 deg per coordinate.
2. IAU 1958 definition (Blaauw et al. 1960): galactic north pole at B1950.0 alpha = 192.25 deg, delta = +27.4 deg;
   galactic longitude of the north celestial pole = 123.0 deg. Exact by definition.
3. Hipparcos definition (ESA 1997, vol. 1, section 1.5.3), ICRS: galactic north pole at alpha = 192.85948 deg,
   delta = +27.12825 deg; galactic longitude of the north celestial pole = 122.93192 deg. Exact by definition.

Consequences that can be derived by hand from 2 and 3 (not "published", write the derivation):
- the galactic north pole maps to b = +90; the north celestial pole maps to (l_ncp, delta_pole);
- galactic_to_equatorial(l_ncp, delta_pole) is the north celestial pole (declination +90);
- the galactic centre direction (l = 0, b = 0) lies 90 deg from the galactic pole;
- the two functions are inverse of each other; a rotation preserves the angle between two directions.
