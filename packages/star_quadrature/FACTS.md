# Published values the tests of star_quadrature may cite (checked by the reviewer against the computation)

1. Abramowitz & Stegun, Handbook of Mathematical Functions (1964), table 25.4, abscissas and weight factors for Gaussian integration on [-1, 1]:
   n = 2: nodes +-0.577350269189626, weights 1.000000000000000;
   n = 3: nodes 0, +-0.774596669241483, weights 0.888888888888889 (centre), 0.555555555555556;
   n = 4: nodes +-0.339981043584856 (weight 0.652145154862546), +-0.861136311594053 (weight 0.347854845137454);
   n = 5: nodes 0 (weight 0.568888888888889), +-0.538469310105683 (weight 0.478628670499366), +-0.906179845938664 (weight 0.236926885056189).
   gauss_legendre(n) returns (nodes, weights), two tuples of n floats, nodes increasing; compare with these values within 1e-15 absolute.

Values derivable by hand (write the derivation in a comment):
- closed forms: n = 1 -> ((0.0,), (2.0,)) exactly; n = 2 -> nodes -+1/sqrt(3) within 2e-16, weights exactly (1.0, 1.0); n = 3 -> nodes (-sqrt(3/5), 0.0, sqrt(3/5)) with the centre
  exactly 0.0, weights (5/9, 8/9, 5/9) within 2e-16; n = 5 centre weight 128/225 within 2e-16;
- for every n from 1 to 32: n nodes and n weights, all floats; nodes strictly increasing and strictly inside (-1, 1); nodes antisymmetric EXACTLY (nodes[i] == -nodes[n-1-i]) and
  weights symmetric EXACTLY (weights[i] == weights[n-1-i]); every weight > 0; math.fsum(weights) == 2.0 within 4e-16; the centre node of an odd rule is exactly 0.0;
  the same tuple objects or equal tuples are returned by repeated calls;
- exactness: the n-point rule integrates x^k over [-1, 1] exactly for k <= 2n - 1: sum(w * x**k) is 2/(k + 1) for even k and 0 for odd k, within 1e-14; it is NOT exact for
  k = 2n: for n = 2, sum(w * x**4) = 2/9, not 2/5 (2 * (1/sqrt 3)^4 = 2/9); for n = 1, sum(w * x**2) = 0, not 2/3;
- integrate(f, a, b, n): integrate(lambda t: 1.0, 2, 5, 1) == 3.0; integrate(lambda t: t, 0, 4, 1) == 8.0 (midpoint rule: 4 * f(2)); integrate(lambda t: t * t, 0, 3, 2) == 9.0 within 1e-14;
  integrate(lambda t: t**5 + t**4, -1, 2, 3) == 17.1 within 1e-13 (63/6 + 33/5); reversing the limits changes the sign: integrate(lambda t: t * t, 3, 1, 2) == -26/3 within 1e-14;
  equal limits give 0.0; integrate(math.sin, 0, math.pi, 10) == 2.0 within 1e-14; integrate(math.exp, 0, 1, 6) == e - 1 within 1e-14; integrate(lambda t: 1/t, 1, 2, 8) = ln 2
  within 1e-11 but NOT within 1e-13 (the rule is not exact for 1/t: the error at 8 points is 5.9e-13); with n = 1 the same integral is 2/3 (midpoint 1.5), far from ln 2;
  an integer returned by f is accepted (integrate(lambda t: 7, 0, 2, 3) == 14.0 within 1e-14); f is called exactly n times, at increasing points inside (a, b) when a < b;
- legendre(n, x) returns (P_n(x), P_n'(x)): legendre(0, 0.3) == (1.0, 0.0); legendre(1, 0.3) == (0.3, 1.0); legendre(2, 0.5) == (-0.125, 1.5) [P_2 = (3x^2 - 1)/2, P_2' = 3x];
  legendre(3, 0.5) == (-0.4375, 0.375) [P_3 = (5x^3 - 3x)/2, P_3' = (15x^2 - 3)/2]; legendre(4, 0.5) == (-0.2890625, -1.5625) [P_4 = (35x^4 - 30x^2 + 3)/8];
  at the ends, for every n from 0 to 32: legendre(n, 1.0) == (1.0, n(n + 1)/2) and legendre(n, -1.0) == ((-1)^n, (-1)^(n+1) n(n + 1)/2), exactly (legendre(32, 1.0) == (1.0, 528.0));
  parity: legendre(n, -x)[0] == (-1)^n legendre(n, x)[0] exactly; at x = 0 odd orders vanish exactly and legendre(2, 0.0) == (-0.5, 0.0), legendre(4, 0.0)[0] == 0.375;
  every node of gauss_legendre(n) is a root: abs(legendre(n, node)[0]) <= 1e-13 for n up to 32; an integer x (0, 1, -1) is accepted.

Limits (state them): MAX_POINTS == 32, BIG == 1e150. Refusals (ValueError):
- gauss_legendre and integrate: n = 0, 33, -1, 2.0 (a float), "2", None, True, False ("n must be an integer from 1 to 32"); n = 1 and n = 32 are accepted;
- legendre: n = -1, 33, 1.5, True, None ("from 0 to 32"); n = 0 and n = 32 accepted; x = 1.0000001, -1.0000001, nan, inf, a bool, a string, None, a complex; x = 1.0 and -1.0 accepted;
- integrate: f not callable (a number, None, a string: "must be callable"); a or b that is a bool, a string, None, nan, inf, a complex, or beyond 1e150 (1.0000001e150; 1e150 itself
  is accepted: integrate(lambda t: 0.0, -1e150, 1e150, 2) == 0.0); f returning a string, None, a bool, a complex, nan or inf ("must return a finite real number");
  a result that overflows: integrate(lambda t: 1e300, -1e150, 1e150, 2) ("overflows").
