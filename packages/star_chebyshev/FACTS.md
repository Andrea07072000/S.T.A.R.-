# Published values the tests of star_chebyshev may cite (checked by the reviewer against the computation)

1. NAIF CSPICE documentation, examples of chbval_c and chbder_c: the series with coefficients (1, 3, 0.5, 1, 0.5, -1, 1) on the interval of midpoint 0.5 and
   radius 3, evaluated at t = 1, has the value -0.340878 and the first derivative 0.382716 (six decimals printed there).
   evaluate_on([1, 3, 0.5, 1, 0.5, -1, 1], 1, 0.5, 3) == (-0.340878, 0.382716) within 5e-7 each.

Values derivable by hand (write the derivation in a comment). T_0 = 1, T_1 = x, T_2 = 2x^2 - 1, T_3 = 4x^3 - 3x, T_4 = 8x^4 - 8x^2 + 1; coefficients are c_0 first:
- evaluate(coefficients, x) returns (value, derivative), two floats: evaluate([5], 0.3) == (5.0, 0.0) (a constant); evaluate([1, 2], 0.3) == (1.6, 2.0);
  evaluate([1, 2, 3], 0.5) == (0.5, 8.0) [1 + 1 - 1.5; 2 + 12x]; evaluate([0, 0, 1], 0.5) == (-0.5, 2.0); evaluate([0, 0, 0, 1], 0.5) == (-1.0, 0.0) [T_3' = 12x^2 - 3];
  evaluate([0, 0, 0, 0, 1], 0.5) == (-0.5, -4.0) [T_4' = 32x^3 - 16x]; evaluate([2, 0, 1], 0.0) == (1.0, 0.0); evaluate((1, -2, 3), -0.25) == (-1.125, -5.0);
  a tuple and a list give the same result; integers are accepted as coefficients and as x;
- at the ends: T_k(1) = 1 and T_k'(1) = k^2; T_k(-1) = (-1)^k and T_k'(-1) = (-1)^(k+1) k^2. So evaluate([1, 1, 1, 1], 1) == (4.0, 14.0), evaluate([1, 1, 1, 1], -1) == (0.0, 6.0),
  evaluate([0, 1], -1) == (-1.0, 1.0), and for a single T_n (coefficients [0]*n + [1]) with n = 7: (1.0, 49.0) at 1 and (-1.0, 49.0) at -1; with n = 199 (200 coefficients,
  the maximum): (1.0, 39601.0) at 1 and (-1.0, 39601.0) at -1, exactly;
- T_n(cos a) = cos(n a) and T_n'(cos a) = n sin(n a) / sin(a): for n = 11, a = 0.7: evaluate([0]*11 + [1], math.cos(0.7)) == (cos 7.7, 11 sin 7.7 / sin 0.7) within 1e-13;
- linearity: evaluate of the sum of two coefficient lists equals the sum of the two results within 1e-12 for coefficients of order 1; evaluate([0.0], x) == (0.0, 0.0), and zeros
  are returned as +0.0 (also evaluate([-0.0, 0.0], -0.0));
- evaluate_on(coefficients, t, mid, radius) evaluates at x = (t - mid) / radius and divides the derivative by radius: evaluate_on([1, 2, 3], 12.5, 10, 5) == (0.5, 1.6);
  evaluate_on([0, 1], 7, 5, 4) == (0.5, 0.25); evaluate_on([1, 2, 3], 15, 10, 5) == (6.0, 2.8) [x = 1: 1 + 2 + 3; (2 + 12)/5]; evaluate_on([1, 2, 3], 5, 10, 5) == (2.0, -2.0)
  [x = -1: 1 - 2 + 3; (2 - 12)/5]; evaluate_on(c, x, 0, 1) == evaluate(c, x) exactly; evaluate_on([4], 3, 3, 1e-100) == (4.0, 0.0);
- a point that leaves the interval by rounding alone is taken as the end: with mid = 1e6 and radius = 1e-3, t = mid + radius (computed in floats) gives exactly
  evaluate_on([1, 2, 3], t, mid, radius) == (6.0, 14000.0); math.nextafter(15.0, 16.0) with mid 10 and radius 5 is accepted and gives (6.0, 2.8), while t = 15.000001 is refused;
- extreme sizes stay finite: evaluate([1e100]*200, 1.0)[0] is about 2e102 (200 * 1e100, within 1e-9 relative) and no call within the limits raises for overflow.

Limits (state them): MAX_TERMS == 200, BIG == 1e100, TINY == 1e-100. Refusals (ValueError):
- coefficients: an empty list, 201 numbers (200 accepted), a string, a generator, a number, None ("coefficients must be a list or tuple"); a coefficient that is a bool, a string,
  None, nan, inf, a complex or beyond 1e100 (1.0000001e100; 1e100 accepted) ("a coefficient");
- evaluate: x = 1.0000001, -1.0000001, nan, inf, a bool, a string, None (1.0 and -1.0 accepted);
- evaluate_on: radius 0, negative, 9e-101, 1.1e100, nan, a bool, a string (1e-100 and 1e100 accepted); mid nan, inf, a bool, beyond 1e100; t nan, inf, a bool, None;
  t outside the interval: evaluate_on([1], 6.1, 0, 6), evaluate_on([1], -6.1, 0, 6), evaluate_on([1], 15.000001, 10, 5) ("t must lie within").
