# Values the tests of star_coords may cite (checked by the reviewer against the computation)

There is NO published numerical example for this module: do not call any number published. The definition is the
standard one (Explanatory Supplement to the Astronomical Almanac): x = r cos(lat) cos(lon), y = r cos(lat) sin(lon),
z = r sin(lat); cylindrical: x = rho cos(lon), y = rho sin(lon), z = z.

Values derivable by hand (write the derivation in a comment; use the tolerance stated):
- spherical_to_xyz(0, 0) == (1.0, 0.0, 0.0) exactly; spherical_to_xyz(60, 0, 2) is (1, sqrt(3), 0) within 1e-15 * 2;
- spherical_to_xyz(90, 0) is (0, 1, 0) within 1e-16 (cos 90 deg is 6e-17 in floating point); spherical_to_xyz(0, 90) is (0, 0, 1) within 1e-16;
- spherical_to_xyz(45, asin(1/sqrt(3)) in degrees, sqrt(3)) is (1, 1, 1) within 1e-15;
- xyz_to_spherical(1, 1, 1) == (45.0, 35.264389682754654, sqrt(3)) within 1e-13 (the latitude is atan(1/sqrt(2)) in degrees);
- xyz_to_spherical(0, -2, 0) == (270.0, 0.0, 2.0); xyz_to_spherical(-3, 0, 0) == (180.0, 0.0, 3.0); xyz_to_spherical(3, 4, 0)[2] == 5.0; xyz_to_spherical(1, 2, 2)[2] == 3.0;
- on the z axis the longitude is returned as 0: xyz_to_spherical(0, 0, 5) == (0.0, 90.0, 5.0); xyz_to_spherical(0, 0, -5) == (0.0, -90.0, 5.0);
  xyz_to_spherical(0, 0, 0) == (0.0, 0.0, 0.0); xyz_to_cylindrical(0, 0, -7) == (0.0, 0.0, -7.0);
- negative zero components behave as zero: xyz_to_spherical(-0.0, -0.0, 1.0)[0] == 0.0;
- a longitude just below the x axis wraps to 0, never 360: xyz_to_spherical(1.0, -1e-300, 0.0)[0] == 0.0 (atan2 gives -1e-300 rad; modulo 360 would give 360.0);
- cylindrical_to_xyz(2, 90, 5) is (0, 2, 5) within 2e-16 in x; xyz_to_cylindrical(0, -2, 5) == (2.0, 270.0, 5.0); xyz_to_cylindrical(3, 4, -1) == (5.0, 53.13010235415598, -1.0) within 1e-13;
- no overflow or underflow in the length: xyz_to_spherical(3e200, 4e200, 0)[2] == 5e200 (relative 1e-15); xyz_to_spherical(3e-200, 4e-200, 0)[2] == 5e-200 (relative 1e-15);
- r = 0 gives the zero vector whatever the angles; a negative longitude is accepted: spherical_to_xyz(-90, 0) is (0, -1, 0) within 1e-16;
- the two directions are inverse of each other (compare the longitude as a displacement: times cos(latitude), or times rho for cylindrical);
- limits: longitude within [-360, 360], latitude within [-90, 90], radius and rho within [0, 1e300], components within [-1e300, 1e300]; BIG == 1e300.
