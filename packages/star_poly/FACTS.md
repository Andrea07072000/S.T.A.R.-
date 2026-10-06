# Published values the tests of star_poly may cite (checked by the reviewer against the computation)

1. The textbook case of catastrophic cancellation in the quadratic formula (Forsythe, "Pitfalls in computation, or why a math book isn't enough", 1970;
   Press et al., Numerical Recipes, section 5.6): x^2 - 1e8 x + 1 has the roots 1e8 and 1e-8 (more precisely 99999999.99999999 and 1.00000000000000001e-8).
   quadratic_roots(1, -1e8, 1) must return (1e-08, 99999999.99999999) exactly; the naive formula returns 7.45e-9 for the small root.

Values derivable by hand (write the derivation in a comment; exact floats unless a tolerance is given):
- quadratics: quadratic_roots(1, -3, 2) == (1.0, 2.0); (2, -10, 12) -> (2.0, 3.0); (-2, 0, 8) -> (-2.0, 2.0); (1, 0, 0) -> (0.0,);
  a double root is ONE root: (1, -2, 1) -> (1.0,); (1, 2, 1) -> (-1.0,); no real root: (1, 0, 1) -> (); (1, -2, 1 + 1e-15) -> ();
  just on the other side there are two: (1, -2, 1 - 1e-15) -> two roots 1 -+ sqrt(1e-15) = 1 -+ 3.1623e-8, within 1e-12 of 0.9999999683772234 and 1.0000000316227766
  (the float 1 - 1e-15 is not exactly that number: allow 1e-10);
  quadratic_roots(1, 0, -2) == (-sqrt(2), sqrt(2)) as the correctly rounded floats (math.sqrt(2.0));
  a tiny leading coefficient: quadratic_roots(1e-30, 1, 1e-30) has the roots -1e30 and -1e-30 within 1e-15 relative (one root runs away, none is lost);
- cubics: cubic_roots(1, -6, 11, -6) == (1.0, 2.0, 3.0); (2, -12, 22, -12) -> the same; (1, 0, -1, 0) -> (-1.0, 0.0, 1.0); (-1, 0, 1, 0) -> the same;
  a double root is reported once: (1, 0, -3, 2) = (x - 1)^2 (x + 2) -> (-2.0, 1.0); a triple root once: (1, -3, 3, -1) -> (1.0,); (1, 0, 0, 0) -> (0.0,);
  one real root: (1, 0, 0, -8) -> (2.0,); (1, 0, 1, 1) -> (-0.6823278038280193,) within 1e-15; (1e-20, 1, 1, 1) -> one root near -1e20 (within 1e-15 relative);
  roots of very different size keep their digits: cubic_roots(1, -1e8, 1, 0) == (0.0, 1e-08, 99999999.99999999);
  three real roots far apart (a regression case found by the cross-check): cubic_roots(1.0, 629699208343.1134, -1725321542916490.2, 1125531448798881.0) is
  (-629699211083.0272, 0.6525157961281471, 2739.2612597839247) within 1e-15 relative: the middle root must not be lost to its neighbour;
- every root returned satisfies the polynomial: |p(r)| <= 4 * eps * sum(|c_i| |r|^(n-i)); the roots are sorted increasing, distinct, and of type float;
  the sum and the product of the roots obey Vieta's formulas when all the roots are real (sum = -b/a, product = c/a for a quadratic; for a cubic sum = -b/a,
  product = -d/a), within 1e-12 relative; scaling all coefficients by a non-zero factor (also negative) does not change the roots;
- evaluate(coefficients, x) returns (value, derivative), highest power first: evaluate([1, -6, 11, -6], 2) == (0.0, -1.0); at 0: (-6.0, 11.0); evaluate([3], 7) == (3.0, 0.0)
  (a constant); evaluate([1, 0, 0], 3) == (9.0, 6.0); evaluate([2, -3, 1, 5], 2) == (11.0, 13.0); a list and a tuple give the same result.

Limits (state them): BIG == 1e60, MAX_COEFFICIENTS == 30. Refusals (ValueError): a leading coefficient equal to 0 or -0.0 ("must not be zero"); a coefficient or x that is a
bool, a string, None, nan, inf, a complex, or beyond 1e60 (1.0000001e60); evaluate with an empty list, with 31 coefficients (30 accepted), with something that is not a list
or tuple (a string, a generator, a number), or whose result overflows (thirty coefficients equal to 1e60 at x = 1e60: "overflows").
