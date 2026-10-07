# Published values the tests of star_polyfit may cite (checked by the reviewer against the computation)

1. NIST Statistical Reference Datasets (StRD), linear regression, dataset Wampler1: 21 observations, x = 0, 1, ..., 20 and y = 1 + x + x^2 + x^3 + x^4 + x^5
   (y = 1, 6, 63, 364, ..., 3368421 at x = 20). Certified values of the fit of degree 5: B0 = B1 = B2 = B3 = B4 = B5 = 1.00000000000000, residual standard deviation 0.
   polyfit(list(range(21)), ys, 5) == (1.0, 1.0, 1.0, 1.0, 1.0, 1.0) exactly, and residual_sum(xs, ys, that) == 0.0 exactly.
2. NIST StRD, dataset Wampler2: the same x and y = 1 + 0.1 x + 0.01 x^2 + 0.001 x^3 + 0.0001 x^4 + 0.00001 x^5 (y = 1.00000, 1.11111, 1.24992, ..., 63.00000 at x = 20).
   Certified values: B0 = 1, B1 = 0.1, B2 = 0.01, B3 = 0.001, B4 = 0.0001, B5 = 0.00001, residual standard deviation 0. With the y computed in Python as
   round(sum(0.1**k * x**k for k in range(6)), 5), polyfit gives each coefficient within 1e-12 relative of the certified one (the y are floats, not exact decimals).

Values derivable by hand (write the derivation in a comment):
- polyfit(xs, ys, degree, weights=None) returns a tuple of degree + 1 floats, LOWEST power first (c0, c1, ..., c_degree); polyval(coefficients, x) returns c0 + c1 x + ...;
  residual_sum(xs, ys, coefficients, weights=None) returns the sum of w (y - p(x))^2;
- degree 0 is the mean: polyfit([1, 2, 3], [2, 4, 9], 0) == (5.0,); weighted mean: polyfit([0, 1], [1, 4], 0, [1, 2]) == (3.0,);
- a polynomial through exactly degree + 1 points interpolates them: polyfit([0, 1, 2], [1, 3, 7], 2) == (1.0, 1.0, 1.0) [1 + x + x^2]; polyfit([0, 1], [3, 5], 1) == (3.0, 2.0);
  polyfit([5], [7], 0) == (7.0,) (one point is enough for degree 0);
- a line by the textbook sums: polyfit([0, 1, 2, 3], [0, 1, 0, 1], 1) == (0.2, 0.2) [mean x 1.5, mean y 0.5, Sxy = 1, Sxx = 5: slope 1/5, intercept 0.5 - 0.3];
  its residuals are -0.2, 0.6, -0.6, 0.2, so the sum of squares is 0.8: residual_sum([0, 1, 2, 3], [0, 1, 0, 1], [0.2, 0.2]) == 0.8 within 1e-15;
- weighted line: polyfit([0, 1, 2, 3], [1, 0, 0, 2], 1, [1, 2, 2, 1]) == (1/11, 3/11) within 1e-16 [weighted means 1.5 and 0.5, Sxx = 5.5, Sxy = 1.5];
- a weight of 0 removes the point: polyfit([0, 1, 2], [0, 1, 4], 1, [1, 1, 0]) == (0.0, 1.0); weights are relative: multiplying all of them by 7 gives the same tuple exactly;
- data exactly on a polynomial give it back exactly whatever the offset: polyfit([1e9 + k for k in range(8)], [k * k for k in range(8)], 2) == (1e18, -2e9, 1.0) exactly
  [(x - 1e9)^2 = x^2 - 2e9 x + 1e18]; polyfit([0, 1, 2, 3], [1, 1, 2, 4], 2) == (1.0, -0.5, 0.5) [1 - x/2 + x^2/2 passes through all four points];
- the order of the points does not matter: any permutation of the pairs gives the same tuple exactly; repeating every point twice gives the same tuple exactly;
- shifting every y by a constant c changes only c0, by c (within rounding: 1e-12 relative on random data); the normal equations hold: with r_i = y_i - p(x_i) for the EXACT solution the
  sum of w r x^k is zero for k = 0..degree; with the rounded coefficients it is small (below 1e-9 for x in [-2, 2] and |y| <= 10);
- polyval([1, 2, 3], 2) == 17.0; polyval([5], 123.0) == 5.0; polyval([0.1, 0.2], 0.3) is the float nearest to 0.1 + 0.2 * 0.3 computed exactly, i.e. 0.16 (the naive float expression
  0.1 + 0.2 * 0.3 gives 0.16 as well; the exact value differs from the real number 0.16 by less than 1e-17);
- residual_sum(xs, ys, c) >= 0 always and == 0.0 exactly when the float coefficients reproduce the float data exactly (Wampler1); the least-squares solution has the smallest sum:
  changing any coefficient returned by polyfit by a relative 1e-3 does not decrease residual_sum (on well-conditioned data).

Limits (state them): MAX_DEGREE == 10, MAX_POINTS == 10000, BIG == 1e100. Refusals (ValueError):
- degree: -1, 11, 1.0 (a float), "2", None, True, False ("degree must be an integer from 0 to 10"); 0 and 10 accepted;
- xs, ys: not a list or tuple (a string, None, a set, a generator, a number), empty, more than 10000 values; a value that is a bool, a string, None, a complex, nan, inf, or beyond 1e100
  (1.0000001e100; 1e100 itself is accepted as a value); different lengths ("same length");
- weights: not None and not a list or tuple, a different number of them ("as many as the points"), a negative one (">= 0"), nan, inf, a bool;
- not enough distinct x with a positive weight: polyfit([1, 1, 2], [1, 2, 3], 2), polyfit([1, 1, 1], [1, 2, 3], 1), polyfit([0, 1, 2], [1, 2, 3], 2, [1, 1, 0]), polyfit([1, 2], [1, 2], 2),
  all weights 0 ("needs at least"); polyfit([1, 1, 2], [1, 2, 3], 1) is accepted (two distinct x) and gives (0.0, 1.5) [mean x 4/3, mean y 2, Sxx = 2/3, Sxy = 1];
- polyval and residual_sum: coefficients that are not a list or tuple of 1 to 11 finite numbers (empty, 12 values, a bool inside); x that is not a finite real number within 1e100;
- a result too large for a float: polyval([0.0] * 10 + [1e100], 1e100) ("too large"); residual_sum([0], [1e100], [-1e100]) is 4e200, still a float, and is accepted;
  residual_sum([0, 0, 0], [1e100] * 3, [-1e100]) == 1.2e201 within 1e-15 relative; residual_sum([1e100], [1e100], [0.0, 0.0, 1e100]) is refused ("too large").
