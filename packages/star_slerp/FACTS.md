# Values the tests of star_slerp may cite (checked by the reviewer against the computation)

Definition (Shoemake, "Animating rotation with quaternion curves", SIGGRAPH 1985): for unit quaternions q0, q1 at angle W (cos W = q0 . q1),
slerp(q0, q1, t) = [sin((1 - t) W) q0 + sin(t W) q1] / sin W. No numerical table is cited from that paper: the values below follow from the definition by hand.
Convention: a quaternion is (w, x, y, z), scalar first; a rotation by the angle a about the unit axis (ax, ay, az) is (cos(a/2), ax sin(a/2), ay sin(a/2), az sin(a/2)).
Write I = (1, 0, 0, 0) and Rz(a) = (cos(a/2), 0, 0, sin(a/2)), Rx(a) = (cos(a/2), sin(a/2), 0, 0); compare components within 1e-15 unless stated.

- slerp returns a tuple of four floats of unit length (math.hypot of the result is 1 within 4e-16), for every valid input;
- the fraction t of a rotation about a fixed axis: slerp(I, Rz(90 deg), 0.5) == Rz(45 deg) == (0.9238795325112867, 0, 0, 0.3826834323650898);
  slerp(I, Rx(1 rad), 0.25) == Rx(0.25 rad) == (cos 0.125, sin 0.125, 0, 0); slerp(Rz(30 deg), Rz(90 deg), 1/3) == Rz(50 deg);
  slerp(Rx(0.2), Rx(1.0), 0.5) == Rx(0.6) (angles in radians);
- end points: slerp(q0, q1, 0) == q0 and slerp(q0, q1, 1) == q1 within 2e-16 per component (when q0 . q1 >= 0);
- the shorter way: -q1 is the same attitude as q1, and slerp(q0, -q1, t) == slerp(q0, q1, t) when q0 . q1 > 0; so slerp(I, (-cos 0.5, -sin 0.5, 0, 0), 0.25) ==
  (cos 0.125, sin 0.125, 0, 0), and at t = 1 the result is (cos 0.5, sin 0.5, 0, 0): the hemisphere of q0, not the q1 that was passed;
  a rotation of 270 degrees about z is reached as -90 degrees: slerp(I, Rz(270 deg), 0.5) == (cos 22.5 deg, 0, 0, -sin 22.5 deg) [Rz(270) = (-0.7071, 0, 0, 0.7071),
  negated to (0.7071, 0, 0, -0.7071) = Rz(-90 deg)];
- equal attitudes: slerp(q, q, t) == q and slerp(q, -q, t) == q for every t (for q = I exactly (1.0, 0.0, 0.0, 0.0));
- a rotation of exactly 180 degrees (q0 . q1 == 0) is not negated: slerp(I, (0, 0, 0, 1), 0.5) == (sqrt(1/2), 0, 0, sqrt(1/2)) and slerp(I, (0, 0, 0, -1), 0.5) ==
  (sqrt(1/2), 0, 0, -sqrt(1/2)): the path follows the q1 that was given;
- tiny rotations keep their digits: slerp(I, (cos 1e-10, 0, sin 1e-10, 0), 0.5) has y == 5e-11 within 1e-25 and w == 1.0;
- symmetry: slerp(q0, q1, t) equals slerp(q1, q0, 1 - t) within 1e-15 (up to the sign of the whole quaternion);
- constant rate: the rotation angle between q0 and slerp(q0, q1, t) is t times the angle between q0 and q1 (2 acos|q0 . q|, compare within 1e-12 for angles of order 1);
- interpolate(times, quaternions, t): with times [0, 10, 20] and attitudes [I, Rx(1), Rx(2)]: at t = 15 the result is Rx(1.5) == (cos 0.75, sin 0.75, 0, 0); at t = 10 it is
  Rx(1) within 2e-16; at t = 0 it is I; at t = 20 it is Rx(2); at t = 5 it is Rx(0.5); with attitudes [I, Rx(1), I] at t = 15 it is Rx(0.5) (back half-way);
  interpolate([0, 1], [q0, q1], t) == slerp(q0, q1, t) exactly; the table need not be uniform: interpolate([0, 1, 5], [I, Rx(1), Rx(2)], 3) == Rx(1.5).

Limits (state them): UNIT_TOLERANCE == 1e-9, SMALL_ANGLE == 1e-8, BIG_TIME == 1e15, MAX_ROWS == 100000. Refusals (ValueError):
- a quaternion that is not a list or tuple of exactly 4 numbers ((1, 0, 0), a string, None: "must be a list or tuple of 4 numbers"); a component that is a bool, a string,
  None, nan, inf, a complex ("a component of"); a quaternion that is not of unit length: (1, 1, 0, 0), (0, 0, 0, 0), (1 + 1e-8, 0, 0, 0) ("unit length");
  (1 + 1e-10, 0, 0, 0) is accepted;
- slerp: t = -0.1, 1.0000001, nan, inf, a bool, a string, None ("t must be a finite real number from 0 to 1"); 0 and 1 accepted, also as ints;
- interpolate: times that are not a list or tuple, or fewer than 2 ("times must be a list or tuple"); a time that is nan, inf, a bool, beyond 1e15 ("a time");
  times not strictly increasing: [0, 0], [1, 0] ("strictly increasing"); a number of quaternions different from the number of times, or quaternions that are not a list or
  tuple ("one quaternion for each time"); a row that is not a unit quaternion ("a quaternion of the table"); t before the first time or after the last
  (no extrapolation: "t must be a finite real number from").
