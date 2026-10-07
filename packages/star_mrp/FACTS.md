# Published values the tests of star_mrp may cite (checked by the reviewer against the computation)

1. Definition and properties of the modified Rodrigues parameters (Schaub and Junkins, Analytical Mechanics of Space Systems, section on MRPs; Marandi and Modi 1987):
   sigma = e tan(phi / 4), e the principal axis and phi the principal angle; in terms of the unit quaternion (w, v), sigma = v / (1 + w) and
   w = (1 - s2) / (1 + s2), v = 2 sigma / (1 + s2) with s2 = |sigma|^2; the shadow set sigma_s = -sigma / s2 is the same attitude (it corresponds to -q);
   |sigma| = 1 is a rotation of 180 degrees; the kinematic equation is d(sigma)/dt = 1/4 [(1 - s2) I + 2 [sigma x] + 2 sigma sigma^T] omega.
   No numerical table is cited: the numbers below follow from these formulas by hand.

Values derivable by hand (write the derivation in a comment):
- quaternions are (w, x, y, z), scalar first; every function returns a tuple of floats (dcm_from_mrp: a tuple of three rows);
- 120 degrees about (1, 1, 1): mrp_from_quaternion((0.5, 0.5, 0.5, 0.5)) == (1/3, 1/3, 1/3) exactly [0.5 / 1.5]; quaternion_from_mrp((1/3, 1/3, 1/3)) == (0.5, 0.5, 0.5, 0.5)
  within 2e-16; dcm_from_mrp((1/3, 1/3, 1/3)) is ((0, 1, 0), (0, 0, 1), (1, 0, 0)) within 2e-16 (a cyclic permutation of the axes);
- 90 degrees about x: sigma = (tan(22.5 deg), 0, 0) = (0.41421356237309503, 0, 0), written T = math.tan(math.pi / 8) below (as a float sqrt(2) - 1 is 0.41421356237309515, a hair beyond: do not use it); mrp_from_rotation_vector((pi / 2, 0, 0)) is (T, 0, 0) within 1e-16;
  dcm_from_mrp((0, 0, T)) is ((0, 1, 0), (-1, 0, 0), (0, 0, 1)) within 5e-16 (a frame turned +90 deg about z: reference x is seen along body -y);
- 180 degrees about z: sigma = (0, 0, 1): quaternion_from_mrp((0, 0, 1)) == (0.0, 0.0, 0.0, 1.0) exactly; rotation_vector_from_mrp((0, 0, 1)) == (0, 0, pi);
- identity: the zero MRP is no rotation: quaternion_from_mrp((0, 0, 0)) == (1.0, 0.0, 0.0, 0.0); dcm is the identity; rotation vector (0, 0, 0); mrp_from_quaternion((2, 0, 0, 0)) ==
  (0.0, 0.0, 0.0) (a quaternion that is not unit is normalised);
- shadow set: shadow((0, 0, 3)) == (0, 0, -1/3); shadow((0.5, 0, 0)) == (-2.0, 0, 0); shadow(shadow(s)) == s within 2e-16; a vector of norm 1 maps to its opposite;
  sigma and its shadow give the same matrix (within 1e-15) and the same quaternion with w >= 0: quaternion_from_mrp((0, 0, 3)) == quaternion_from_mrp((0, 0, -1/3)) ==
  (0.8, 0, 0, -0.6) within 2e-16 [s2 = 1/9: w = (8/9)/(10/9), z = (-2/3)/(10/9)];
- q and -q are one attitude: mrp_from_quaternion((-0.5, 0.5, 0.5, 0.5)) == (-1/3, -1/3, -1/3) (the short rotation: 240 degrees about (1,1,1) is 120 degrees about the opposite axis);
  mrp_from_quaternion always has norm <= 1; for w = 0 (a half turn) the norm is exactly 1: mrp_from_quaternion((0, 1, 0, 0)) == (1.0, 0.0, 0.0);
- switch(s, threshold=1.0) returns s when |s| <= threshold and the shadow otherwise: switch((2, 0, 0)) == (-0.5, 0, 0); switch((0.6, 0, 0), 0.5) == (-1/0.6, 0, 0) = (-1.6666666666666667, 0, 0);
  switch((0.5, 0, 0), 0.5) == (0.5, 0, 0) (the threshold itself is kept); switch((1, 0, 0)) == (1.0, 0.0, 0.0);
- compose(first, second) is the rotation first, then second, on the short rotation: two quarter turns about z make a half turn: compose((0, 0, T), (0, 0, T)) ==
  (0, 0, 1) within 2e-16 (with a quarter turn a hair too long the answer is the other MRP of norm 1, (0, 0, -1): compare absolute values at a half turn); two half turns make a full turn, i.e. nothing: compose((0, 0, 1), (0, 0, 1)) == (0, 0, 0); a rotation and its opposite cancel: compose(s, (-s)) == (0, 0, 0)
  within 1e-16; compose(s, (0, 0, 0)) == s within 2e-16 for |s| <= 1; rotations about different axes do not commute: compose(a, b) != compose(b, a);
  dcm_from_mrp(compose(a, b)) equals the matrix product dcm(b) dcm(a) within 1e-14;
- rotation vectors: the angle is 4 atan(|sigma|) in [0, pi]: rotation_vector_from_mrp((1/3, 1/3, 1/3)) has norm 2 pi / 3 within 1e-15; a rotation vector of 270 degrees about z is the
  short rotation of -90 degrees: mrp_from_rotation_vector((0, 0, 3 pi / 2)) == (0, 0, -T) within 1e-15; a full turn is nothing: mrp_from_rotation_vector((0, 2 pi, 0)) ==
  (0, 0, 0) within 1e-16; rotation_vector_from_mrp((3, 0, 0)) == (-4 atan(1/3), 0, 0) = (-1.2870022175865687, 0, 0) (through the shadow set);
- kinematics: at the zero attitude the rate is omega / 4: mrp_rate((0, 0, 0), (0.4, 0, 0)) == (0.1, 0, 0); along the rotation axis the rate is (1 + s2) / 4 times omega:
  mrp_rate((0, 0, 1), (0, 0, 0.4)) == (0, 0, 0.2); a perpendicular case by the formula: mrp_rate((0.5, 0, 0), (0, 0.4, 0)) == (0, 0.075, 0.1) within 1e-16
  [(1 - 0.25) * 0.4 / 4 = 0.075 on y; the cross product (0.5, 0, 0) x (0, 0.4, 0) = (0, 0, 0.2), times 2 / 4 = 0.1 on z]; the rate is linear in omega;
  integrating the rate over a small step agrees with composing the small rotation: sigma + mrp_rate(sigma, omega) dt equals compose(sigma, mrp_from_rotation_vector(omega dt))
  within 2 |omega dt|^2.

Refusals (ValueError):
- an MRP, rotation vector or angular velocity that is not a list or tuple of 3 numbers; a quaternion that is not 4 numbers; a component that is a bool, a string, None, a complex,
  nan, inf or beyond 1e150;
- mrp_from_quaternion((0, 0, 0, 0)) ("zero quaternion"); shadow((0, 0, 0)) ("no shadow set");
- switch with a threshold that is 0, negative, nan or a bool ("threshold").
