# Values the tests of star_vec3 may cite (checked by the reviewer against the computation)

There is NO published numerical example for these definitions: do not call any number published.

Values derivable by hand (write the derivation in a comment; exact unless a tolerance is given):
- the basis: cross((1,0,0), (0,1,0)) == (0.0, 0.0, 1.0), cross(j, k) == i, cross(k, i) == j, cross(b, a) == -cross(a, b), cross(a, a) == (0, 0, 0);
  dot(i, j) == 0.0, dot(a, a) == norm(a) ** 2 (1e-15 relative);
- with a = (1, 2, 3) and b = (-2, 0.5, 4): dot == 11.0; cross == (6.5, -10.0, 4.5); norm(a) == sqrt(14); distance(a, b) == 3.5;
  triple(a, b, (1, 1, 1)) == 1.0 (= 6.5 - 10 + 4.5); unit(a) == a / sqrt(14) within 2e-16; project(a, b) == 11 / 20.25 * b within 1e-15
  (|b|^2 = 20.25) and reject(a, b) == a - project(a, b); angle_deg(a, b) == degrees(acos(11 / (sqrt(14) * 4.5))) = 49.2087297841 within 1e-9;
- norm((3, 4, 0)) == 5.0; norm((1, 2, 2)) == 3.0; distance((1, 1, 1), (1, 1, 1)) == 0.0; unit((0, 0, -7)) == (0.0, 0.0, -1.0);
- angles: angle_deg(i, j) == 90.0; angle_deg(i, (1, 1, 0)) == 45.0 within 1e-13; angle_deg(a, a) == 0.0; angle_deg(a, -a) == 180.0 exactly; the angle does not
  depend on the lengths (angle_deg(1e-200 * i ... use (1e-200, 0, 0) and (0, 1e100, 0)) == 90.0);
  nearly parallel vectors keep their digits: angle_deg((1, 0, 0), (1, 1e-9, 0)) == degrees(1e-9) = 5.729577951308232e-08 within 1e-15 relative of that
  (the arc-cosine form would return 0), and angle_deg((1, 0, 0), (-1, 1e-9, 0)) == 180 - 5.729577951308232e-08 within 1e-13;
- identities to check with the module's outputs: cross(a, b) is perpendicular to a and to b (dot within 1e-13 * lengths); Lagrange: |a x b|^2 + (a . b)^2 == |a|^2 |b|^2
  (1e-14 relative); project(a, b) + reject(a, b) == a (1e-15 * |a|); reject(a, b) is perpendicular to b; project(a, b) is parallel to b (cross within 1e-13);
  project and reject do not depend on the length of b; triple(a, b, c) == triple(b, c, a) == -triple(b, a, c) (1e-13 relative); triple of coplanar vectors is 0;
  unit(a) has norm 1 within 2e-16 and is unchanged when a is scaled by a positive factor; unit works at the extremes: unit((3e-300, 4e-300, 0)) and
  unit((3e99, 4e99, 0)) are both (0.6, 0.8, 0.0) within 1e-15; norm((3e99, 4e99, 0)) == 5e99 (no overflow);
- results are tuples of three floats (cross, unit, project, reject) or a float; lists and tuples are both accepted as input, ints and fractions.Fraction too.

Limits (state them): BIG == 1e100; at the limit nothing overflows: triple((1e100, 0, 0), (0, 1e100, 0), (0, 0, 1e100)) == 1e300, dot of two (1e100, 1e100, 1e100) == 3e200.
Refusals (ValueError): a vector that is not a list or tuple (a string, a set, a dict, a generator, None, a number), of length 2 or 4, or holding a bool, a string, None,
nan, inf, a complex or a component beyond 1e100 (1.0000001e100); the zero vector in unit, in either argument of angle_deg and as the SECOND argument of project and
reject ("zero vector"); a zero first argument of project and reject is accepted and gives (0, 0, 0).
