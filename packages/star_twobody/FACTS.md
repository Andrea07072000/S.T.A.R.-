# Published values the tests of star_twobody may cite (checked by the reviewer against the computation)

1. The geostationary orbit (e.g. Vallado, Fundamentals of Astrodynamics and Applications; any textbook): its period is one sidereal day,
   86164.0905 s, and its radius 42164.17 km, with the Earth's mu = 398600.4418 km3/s2. period(42164.17) must be within 0.01 s of 86164.0905,
   semi_major_axis_from_period(86164.0905) within 0.01 km of 42164.17, and mean_motion(42164.17) within 5e-12 rad/s of 2 pi / 86164.0905
   (7.29212e-5 rad/s, the Earth's rotation rate to six figures).
2. MU_EARTH == 398600.4418 km3/s2 (EGM96 / WGS-84: a defined constant of those models).

Formulas the tests can evaluate themselves (derive in a comment; they are not "published values"):
- Kepler's third law T = 2 pi sqrt(a^3 / mu); in units where mu = 4 pi^2 and a = 1 the period is exactly 1 (period(1, 4 * pi**2) == 1 within 1e-15);
  T scales as a^1.5 (period(4 a) == 8 period(a) within 1e-14 relative) and as mu^-0.5; mean_motion(a, mu) * period(a, mu) == 2 pi within 1e-15 relative;
  semi_major_axis_from_period inverts period within 1e-14 relative;
- circular_speed(r) = sqrt(mu / r); escape_speed(r) = sqrt(2) * circular_speed(r) (within 4e-16 relative); with mu = 1, r = 4: 0.5 and 0.7071067811865476;
  for the Earth at r = 6378.137 km the escape speed is 11.179875 km/s within 1e-6 (computed: sqrt(2 * 398600.4418 / 6378.137));
- apsides(a, e) = (a (1 - e), a (1 + e)): apsides(10000, 0.2) == (8000.0, 12000.0); a circle has both equal to a;
  elements_from_apsides(8000, 12000) == (10000.0, 0.2) within 1e-15; it inverts apsides within 1e-15;
  elements_from_apsides(r, r) == (r, 0.0); two radii of a circle that differ only by rounding (apoapsis 5e-13 relative below the periapsis) are accepted and give
  e == 0.0 exactly, while an apoapsis 1e-9 relative below the periapsis is refused ("apoapsis");
- apsis_speeds(a, e, mu) = (sqrt(mu / a) sqrt((1 + e) / (1 - e)), sqrt(mu / a) sqrt((1 - e) / (1 + e))): for a = 10000, e = 0.2 and the Earth:
  (7.732404, 5.154936) km/s within 1e-6; for e = 0 both equal circular_speed(a);
  conservation of angular momentum: r_p v_p == r_a v_a (1e-14 relative); conservation of energy (vis-viva):
  v_p^2 / 2 - mu / r_p == v_a^2 / 2 - mu / r_a == specific_energy(a, mu) (1e-12 relative);
- specific_energy(a, mu) = -mu / (2 a): specific_energy(10000) == -19.93002209 within 1e-8; it is negative; at escape speed the energy is zero:
  escape_speed(r)^2 / 2 - mu / r == 0 within 1e-12 * mu / r;
- defaults: every function with mu uses MU_EARTH when mu is omitted (call with and without and compare with ==, and check that another mu changes the result).

Limits (state them): TINY == 1e-30, BIG == 1e30. Refusals (ValueError): a, r, a period or mu equal to 0, negative, below 1e-30 or above 1e30 (both limits accepted;
every result at the limits is a finite, non-zero float), nan, inf, a bool, a string,
None, a complex, a list; e negative, equal to 1, above 1, nan, a bool ("ellipses only"); an apoapsis below the periapsis by more than rounding.
