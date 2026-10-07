# Published values the tests of star_anomaly may cite (checked by the reviewer against the computation)

1. Vallado, Fundamentals of Astrodynamics and Applications, worked example of Kepler's equation for an ellipse: M = 235.4 deg, e = 0.4 gives E = 220.512074767522 deg.
   math.degrees(eccentric_from_mean(math.radians(235.4), 0.4)) == 220.512074767522 within 1e-11 deg.
2. The same book, Kepler's equation for a hyperbola: M = 235.4 deg, e = 2.4 gives H = 1.6013761449 rad.
   hyperbolic_from_mean(math.radians(235.4), 2.4) == 1.6013761449 within 1e-10.

Values derivable by hand (write the derivation in a comment):
- all angles in radians; closed orbits need 0 <= e < 1, open orbits e > 1; ten functions: eccentric_from_mean(M, e), mean_from_eccentric(E, e), true_from_eccentric(E, e),
  eccentric_from_true(nu, e), true_from_mean(M, e), mean_from_true(nu, e), hyperbolic_from_mean(M, e), mean_from_hyperbolic(F, e), true_from_hyperbolic(F, e), hyperbolic_from_true(nu, e);
- Kepler's equation directly: mean_from_eccentric(E, e) == E - e sin(E): mean_from_eccentric(pi / 2, 0.5) == pi / 2 - 0.5 within 1e-15; mean_from_eccentric(1.2, 0.3) == 0.9203882742098322
  within 1e-15; mean_from_hyperbolic(F, e) == e sinh(F) - F: mean_from_hyperbolic(1.0, 2.0) == 2 sinh(1) - 1 = 1.3504023872876028 within 1e-15;
- a circular orbit has only one anomaly: for e = 0 all six closed-orbit functions return their argument exactly;
- fixed points for every e: zero maps to zero exactly in all ten functions; pi maps to pi (eccentric_from_mean(pi, e) == pi, true_from_eccentric(pi, e) == pi within 5e-16) and -pi to -pi;
- odd functions, exactly: f(-x, e) == -f(x, e) for all ten;
- the revolution is kept: eccentric_from_mean(M + 2 pi k, e) == eccentric_from_mean(M, e) + 2 pi k within 1e-12 + 4e-15 |2 pi k| for integer k (k = 7, -3, 1000), and the same for true_from_eccentric,
  eccentric_from_true and their compositions; E - M and nu - E stay within e and pi in absolute value: |eccentric_from_mean(M, e) - M| <= e;
- order between perigee and apogee (0 < M < pi, e > 0): M < E < nu < pi; e.g. e = 0.5, M = 1: eccentric_from_mean(1, 0.5) == 1.4987011335178484 within 1e-14 and
  true_from_mean(1, 0.5) == 2.030806214849156 within 1e-14 [tan(nu/2) = sqrt(3) tan(E/2)];
- the half-angle relation: tan(true_from_eccentric(E, e) / 2) == sqrt((1 + e) / (1 - e)) tan(E / 2) within 1e-13 relative for |E| < 3; true_from_eccentric(pi / 2, e) == pi / 2 + asin(e)
  within 1e-15 [cos(nu) = -e when E = 90 deg: nu = acos(-e)]: true_from_eccentric(pi / 2, 0.5) == 2 pi / 3 within 1e-15;
- inverses: eccentric_from_mean(mean_from_eccentric(E, e), e) == E within 1e-12 for e <= 0.99; eccentric_from_true(true_from_eccentric(E, e), e) == E within 1e-12 for e <= 0.99;
  mean_from_true(true_from_mean(M, e), e) == M within 1e-12 for e <= 0.9; hyperbolic_from_mean(mean_from_hyperbolic(F, e), e) == F within 1e-12 for |F| <= 5, e >= 1.01;
  hyperbolic_from_true(true_from_hyperbolic(F, e), e) == F within 1e-9 for |F| <= 5 (the true anomaly approaches the asymptote and holds fewer digits of F);
- the residual of Kepler's equation is at the level of rounding: E - e sin(E) - M within 2e-15 for the E returned, any e in [0, 1) and |M| <= pi;
- nearly parabolic orbits near periapsis keep their digits: for e = 1 - 1e-12 and M = 1e-10, eccentric_from_mean returns 8.434303040921716e-4 within 1e-15 relative (the root of
  (1 - e) E + e (E - sin E) = M, where E - sin E is E^3 / 6 to first order: E is close to (6 M)^(1/3) = 8.43e-4);
- open orbits: the true anomaly stays inside the asymptotes, |true_from_hyperbolic(F, e)| < acos(-1 / e) for every F [e = 2: below 2 pi / 3]; true_from_hyperbolic(F, e) tends to
  acos(-1 / e) as F grows: true_from_hyperbolic(30, 2.0) == 2 pi / 3 within 1e-12; tanh(F / 2) == sqrt((e - 1) / (e + 1)) tan(nu / 2);
  small mean anomaly: hyperbolic_from_mean(M, e) tends to M / (e - 1): hyperbolic_from_mean(1e-9, 3.0) == 5e-10 within 1e-15 relative;
  large mean anomaly: F tends to ln(2 M / e): hyperbolic_from_mean(1e100, 2.0) == ln(1e100) + small = 230.2585 within 1e-3.

Limits (state them): MAX_ANGLE == 1e9 (closed orbits), MAX_HYPERBOLIC == 700.0, MAX_MEAN == 1e150. Refusals (ValueError):
- any argument that is a bool, a string, None, a complex, nan or inf;
- closed-orbit functions with e = 1, 1.5 or -0.1 ("e must be in [0, 1) for a closed orbit"); e = math.nextafter(1, 0) is accepted;
- open-orbit functions with e = 1, 0.5 or 0 ("e must be greater than 1 for an open orbit"); e = math.nextafter(1, 2) is accepted;
- a closed-orbit angle beyond 1e9 in absolute value (1.0000001e9; 1e9 itself is accepted); a hyperbolic anomaly beyond 700; a mean anomaly of an open orbit beyond 1e150;
- hyperbolic_from_true with a true anomaly at or beyond the asymptote: nu = 2.2 or pi for e = 2 ("asymptote"), or beyond pi in absolute value; nu = 2.0 is accepted for e = 2;
- mean_from_hyperbolic whose result overflows: mean_from_hyperbolic(700, 1e150) ("too large").
