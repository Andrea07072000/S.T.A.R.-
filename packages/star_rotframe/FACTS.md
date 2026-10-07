# Published values the tests of star_rotframe may cite (checked by the reviewer against the computation)

1. WGS-84 defining parameters (NIMA TR8350.2, third edition): angular velocity of the Earth 7292115.0e-11 rad/s; semi-major axis 6378137.0 m.
   EARTH_RATE == 7.292115e-5 exactly. A point fixed on the equator has the inertial speed 6378.137 km * 7.292115e-5 rad/s = 0.46510108... km/s (465.1 m/s).

Definition (any dynamics textbook: the velocity seen from a rotating frame is v - w x r):
  to_rotating(r, v, angle, rate) returns (r', v'), two tuples of three floats, with r' = Rz(angle) r and v' = Rz(angle) v - w x r', w = (0, 0, rate);
  Rz(angle) gives the components in a frame whose x axis is turned by `angle` (radians) about +z: x' = x cos a + y sin a, y' = -x sin a + y cos a, z' = z.
  to_inertial(r', v', angle, rate) is the inverse. The default rate is EARTH_RATE.

Values derivable by hand (write the derivation in a comment; compare within 1e-12 unless stated):
- no rotation: to_rotating((1, 2, 3), (4, 5, 6), 0, 0) == ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)) exactly;
- a quarter turn, no rate: to_rotating((1, 0, 0), (0, 0, 0), math.pi / 2, 0) == ((0, -1, 0), (0, 0, 0)) [the frame turned towards +y sees the old x axis along -y'];
  to_rotating((0, 1, 0), (0, 0, 0), math.pi / 2, 0) == ((1, 0, 0), (0, 0, 0)); a half turn: to_rotating((1, 2, 3), (0, 0, 0), math.pi, 0)[0] == (-1, -2, 3);
  the z components are never changed: r'[2] == r[2] and v'[2] == v[2] exactly;
- the transport term alone (angle 0): to_rotating((1, 0, 0), (0, 0, 0), 0, 2.0) == ((1, 0, 0), (0, -2, 0)) [w x r' = (0, 0, 2) x (1, 0, 0) = (0, 2, 0), subtracted];
  to_rotating((0, 1, 0), (0, 0, 0), 0, 2.0)[1] == (2, 0, 0) [w x r' = (-2, 0, 0)]; to_rotating((3, 4, 5), (0, 0, 0), 0, 0.5)[1] == (2.0, -1.5, 0.0);
  a negative rate reverses it: to_rotating((1, 0, 0), (0, 0, 0), 0, -2.0)[1] == (0, 2, 0);
- a point fixed on the rotating body is at rest in the rotating frame: with R = 6378.137, w = EARTH_RATE and any angle a, the inertial state
  r = (R cos a, R sin a, 0), v = (-w R sin a, w R cos a, 0) gives r' == (R, 0, 0) within 1e-9 and v' == (0, 0, 0) within 1e-12; for a = pi/2: r = (0, R, 0), v = (-w R, 0, 0);
  a geostationary satellite (R = 42164.0 km, the same w) likewise; the speed sqrt(vx^2 + vy^2) of the equator point is w R = 0.46510108... km/s (within 1e-8 of 0.46510108);
- an inertially fixed point is seen moving backwards: to_rotating((7000, 0, 0), (0, 0, 0), 0)[1] == (0, -7000 * EARTH_RATE, 0) = (0, -0.51044805, 0);
- inverse: to_inertial(*to_rotating(r, v, a, w), a, w) returns r and v within 1e-12 relative, and to_rotating(*to_inertial(r, v, a, w), a, w) likewise;
  to_inertial((R, 0, 0), (0, 0, 0), a) == ((R cos a, R sin a, 0), (-w R sin a, w R cos a, 0)); to_inertial((1, 0, 0), (0, 0, 0), 0, 2.0) == ((1, 0, 0), (0, 2, 0));
- lengths: |r'| == |r| within 1e-12 relative for every angle; with rate 0, |v'| == |v| too; adding 2 pi to the angle changes the result by less than 1e-9 relative;
- zeros are +0.0 (math.copysign(1.0, x) == 1.0 for every zero component returned); lists and tuples give the same result; integers are accepted.

Limits (state them): BIG == 1e15, MAX_ANGLE == 1e9, MAX_RATE == 1000.0. Refusals (ValueError), for both functions:
- r or v that is not a list or tuple of exactly 3 numbers ((1, 2), (1, 2, 3, 4), a string, None: "must be a list or tuple of 3 numbers");
- a component that is a bool, a string, None, nan, inf, a complex, or beyond 1e15 (1.0000001e15; 1e15 accepted) ("a component of r" / "a component of v");
- angle that is a bool, a string, None, nan, inf, or beyond 1e9 in size (1e9 accepted) ("angle"); rate that is a bool, a string, None, nan, inf, or beyond 1000 in size
  (1000 and -1000 accepted) ("rate").
