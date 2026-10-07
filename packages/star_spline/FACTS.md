# Published values the tests of star_spline may cite (checked by the reviewer against the computation)

1. Burden and Faires, Numerical Analysis, section on cubic spline interpolation, the worked example of the natural cubic spline through (1, 2), (2, 3), (3, 5):
   S0(x) = 2 + 3/4 (x - 1) + 1/4 (x - 1)^3 on [1, 2] and S1(x) = 3 + 3/2 (x - 2) + 3/4 (x - 2)^2 - 1/4 (x - 2)^3 on [2, 3].
   Hence, all exactly: second_derivatives([1, 2, 3], [2, 3, 5]) == (0.0, 1.5, 0.0); values([1, 2, 3], [2, 3, 5], [1, 1.5, 2, 2.5, 3]) == (2.0, 2.40625, 3.0, 3.90625, 5.0);
   derivatives([1, 2, 3], [2, 3, 5], [1, 2, 3]) == (0.75, 1.5, 2.25); integral([1, 2, 3], [2, 3, 5], 1, 3) == 6.375 [2.4375 on the first interval, 3.9375 on the second];
   integral(..., 1.5, 2.5) == 3.0546875.

Values derivable by hand (write the derivation in a comment):
- second_derivatives(xs, ys) returns a tuple of len(xs) floats whose first and last are exactly 0.0; values(xs, ys, points) and derivatives(xs, ys, points) return a tuple with one
  float per point (an empty list of points gives an empty tuple); integral(xs, ys, a, b) returns a float;
- the spline passes through the knots exactly: values(xs, ys, xs) == tuple(float(y) for y in ys) for any table;
- two points give the straight line: second_derivatives([0, 1], [1, 3]) == (0.0, 0.0); values([0, 1], [1, 3], [0.25]) == (1.5,); derivatives([0, 1], [1, 3], [0.7]) == (2.0,);
  integral([0, 1], [1, 3], 0, 1) == 2.0;
- data on a straight line give that line whatever the spacing: all second derivatives are exactly 0.0, values([0, 1, 2, 3, 4], [1, 3, 5, 7, 9], [2.5]) == (6.0,) and the derivative
  is exactly the slope everywhere; the same with uneven knots [0, 0.125, 5, 5.5, 20] and y = 3 - 0.5 x (knots that are exact binary fractions: with 0.1 the
  floats 3 - 0.5 * 0.1 are not exactly on a line and the second derivatives are of the order of 1e-15, not zero);
- three equally spaced knots with spacing h: the middle second derivative is 3 (y0 - 2 y1 + y2) / (2 h^2) [from 4 h M1 = 6 (y2 - 2 y1 + y0) / h]:
  second_derivatives([0, 1, 2], [0, 1, 0])[1] == -3.0 exactly, and the spline at 0.5 is 0.6875 [y-bar 0.5 minus h^2/16 * (M0 + M1) = 0.5 + 3/16];
  second_derivatives([0, 2, 4], [1, 0, 1])[1] == 0.75;
- symmetry: reversing the table about its centre mirrors the spline: for xs symmetric and ys symmetric, values at x and at (xs[0] + xs[-1] - x) are equal exactly;
  the spline is linear in the data: the spline of (ys1 + ys2) is the sum of the two splines (within 1e-12), and scaling ys by 2 doubles every value and derivative exactly;
- shifting every x by a constant shifts the spline (values at shifted points equal, within 1e-12, when the shift is exactly representable they are equal exactly:
  values([1e9 + k for k in range(5)], ys, [1e9 + 1.5]) == values([0, 1, 2, 3, 4], ys, [1.5]));
- continuity at the knots: the first derivative just left and just right of an interior knot agree to rounding (derivatives at xs[i] is single-valued), and the second
  derivative read from finite differences of derivatives on each side tends to second_derivatives[i];
- the integral: integral(xs, ys, a, a) == 0.0; integral(xs, ys, b, a) == -integral(xs, ys, a, b) exactly; integral over [a, c] is the sum of the integrals over [a, b] and [b, c]
  within 1e-13 relative; for two points it is the trapezoid; for the natural spline on equally spaced knots it is the trapezoid sum minus h^3/24 times the sum of
  (M_i + M_(i+1)) over the intervals [for [0, 1, 2], [0, 1, 0]: trapezoid 1.0, minus (1/24) * ((0 - 3) + (-3 + 0)) = 1.25];
- points at the ends are inside the table: values(xs, ys, [xs[0], xs[-1]]) are the first and last y exactly.

Limits (state them): MAX_POINTS == 300, BIG == 1e100. Refusals (ValueError):
- xs or ys that are not a list or tuple (a string, None, a number, a generator), with fewer than 2 or more than 300 values ("2 to 300 numbers"); a value that is a bool, a string,
  None, a complex, nan, inf, or beyond 1e100 ("finite real numbers within"); different lengths ("same length");
- xs not strictly increasing: equal knots ([0, 1, 1, 2]) or decreasing ([0, 2, 1]) ("strictly increasing");
- a point, or a limit a or b, outside the table: just below xs[0] or just above xs[-1] (math.nextafter), nan, inf, a string ("not extrapolated" or "finite real numbers");
  points that is not a list or tuple ("points must be a list or tuple");
- a result too large for a float: values([0, 1e-300, 2e-300], [0, 1e100, 0], [...]) is fine (the values stay within the data), but second_derivatives of that table is about
  -3e700 and is refused ("too large").
