# Published values the tests of star_linefit may cite (checked by the reviewer against the computation)

1. NIST Statistical Reference Datasets (StRD), linear regression, dataset Norris (36 observations, lower difficulty). Certified values:
   slope 1.00211681802045, intercept -0.262323073774029, standard deviation of the slope 0.429796848199937E-03, of the intercept 0.232818234301152,
   residual standard deviation 0.884796396144373. The data (y, x), in the order of the NIST file:
   y = [0.1, 338.8, 118.1, 888.0, 9.2, 228.1, 668.5, 998.5, 449.1, 778.9, 559.2, 0.3, 0.1, 778.1, 668.8, 339.3, 448.9, 10.8, 557.7, 228.3, 998.0, 888.8, 119.6, 0.3, 0.6,
        557.6, 339.3, 888.0, 998.5, 778.9, 10.2, 117.6, 228.9, 668.4, 449.2, 0.2]
   x = [0.2, 337.4, 118.2, 884.6, 10.1, 226.5, 666.3, 996.3, 448.6, 777.0, 558.2, 0.4, 0.6, 775.5, 666.9, 338.0, 447.5, 11.6, 556.0, 228.1, 995.8, 887.6, 120.2, 0.3, 0.3,
        556.8, 339.1, 887.2, 999.0, 779.0, 11.1, 118.3, 229.2, 669.1, 448.9, 0.5]
   fit(x, y) and fit_errors(x, y) reproduce the five certified values within 1e-12 relative (measured: 1e-13).

Values derivable by hand (write the derivation in a comment). All results are floats; the arguments are (xs, ys):
- fit([0, 1, 2], [1, 3, 5]) == (2.0, 1.0) (points on y = 2x + 1); fit([0, 1], [5, 3]) == (-2.0, 5.0) (two points: the line through them);
  fit([1, 2, 3], [2, 2, 2]) == (0.0, 2.0) (a horizontal line); fit([0, 1, 2, 3], [0, 1, 1, 2]) == (0.6, 0.1) within 1e-15
  [mean x 1.5, mean y 1; Sxx = 5, Sxy = 3; slope 3/5; intercept 1 - 0.9];
- a far origin loses nothing: fit([1e9, 1e9 + 1, 1e9 + 2], [5, 7, 9]) == (2.0, -1999999995.0) exactly;
- fit_errors(xs, ys) returns (standard error of the slope, standard error of the intercept, residual standard deviation), n - 2 degrees of freedom:
  fit_errors([0, 1, 2, 3], [0, 1, 1, 2]) == (sqrt(0.02), sqrt(0.07), sqrt(0.1)) within 1e-15 [residuals -0.1, 0.3, -0.3, 0.1: sum of squares 0.2, over 2 = 0.1;
  0.1 / Sxx = 0.02; 0.1 * (1/4 + 1.5^2 / 5) = 0.07]; points exactly on a line give (0.0, 0.0, 0.0): fit_errors([0, 1, 2], [1, 3, 5]) == (0.0, 0.0, 0.0);
- correlation([1, 2, 3], [2, 4, 6]) == 1.0 exactly; correlation([1, 2, 3], [6, 4, 2]) == -1.0 exactly; correlation([1, 2, 3, 4], [1, 3, 2, 4]) == 0.8 within 1e-15
  [Sxy = 4, Sxx = Syy = 5]; correlation([0, 1, 2, 3], [0, 1, 1, 2]) == 3 / sqrt(10) within 1e-15; correlation([-1, 0, 1], [1, 0, 1]) == 0.0 (no linear relation);
  the result is always in [-1, 1]; correlation(xs, ys) == correlation(ys, xs); it does not change when x or y is shifted or scaled by a positive power of two,
  and changes sign when one of them is negated;
- relations: the slope equals correlation * sqrt(Syy / Sxx); the line passes through the point of the means: slope * mean(x) + intercept == mean(y) within 1e-12;
  exchanging the order of the points (the same permutation of xs and ys) gives identical floats for every function; a tuple and a list give the same result.

Limits (state them): BIG == 1e100, MAX_POINTS == 100000. Refusals (ValueError), for every function:
- xs or ys that is not a list or tuple (a string, a generator, None), or has fewer than 2 values ("xs must be a list or tuple" / "ys must be a list or tuple");
- a value that is a bool, a string, None, nan, inf, a complex, or beyond 1e100 (1.0000001e100; 1e100 accepted) ("xs must be finite real numbers" / "ys must be finite");
- different lengths: fit([1, 2, 3], [1, 2]) ("same length");
- all x equal: fit([1, 1], [1, 2]), fit([3, 3, 3], [1, 2, 3]) ("all the x are equal");
- correlation with all y equal: correlation([1, 2, 3], [5, 5, 5]) ("all the y are equal"); fit and fit_errors accept it (a horizontal line);
- fit_errors with 2 points: fit_errors([0, 1], [5, 3]) ("at least 3 points"); fit and correlation accept 2 points (correlation([0, 1], [5, 3]) == -1.0);
- a result too large for a float: fit([0.0, 5e-324], [1e100, -1e100]) ("too large for a float").
Do NOT build lists of 100001 values more than once in the tests (slow): one test for that limit is enough.
