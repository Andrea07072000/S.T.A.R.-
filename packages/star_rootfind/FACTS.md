# Published values the tests of star_rootfind may cite (checked by the reviewer against the computation)

1. The real root of x^3 - 2x - 5 = 0, the equation used by Wallis (1685) to present Newton's method: 2.0945514815423265 (2.09455148154232659...).
   find_root(lambda x: x**3 - 2*x - 5, 2, 3) == 2.0945514815423265 within 4.5e-16.

Values derivable by hand (write the derivation in a comment):
- find_root(f, a, b) returns a float in [a, b]: find_root(lambda x: x - 3, 0, 10) == 3.0 exactly; find_root(lambda x: 3 - x, 0, 10) == 3.0 (a decreasing function);
  find_root(lambda x: x, -1, 1) == 0.0; find_root(lambda x: 2*x - 1, 0, 1) == 0.5; find_root(lambda x: x - 1/3, 0, 1) == 1/3 and find_root(lambda x: 1/3 - x, 0, 1) == 1/3 exactly;
  find_root(lambda x: x**3 - 8, -1e100, 1e100) == 2.0 exactly (a huge bracket costs nothing);
- a root at an end is returned without a change of sign being needed: find_root(lambda x: x - 3, 3, 5) == 3.0; find_root(lambda x: x - 5, 3, 5) == 5.0;
  find_root(lambda x: x * (x - 1), 0, 1) == 0.0 (both ends are roots: the lower is returned, f is evaluated once);
- the result is within ONE float of the true root, not always the nearest: find_root(lambda x: x*x - 2, 0, 2) is 1.414213562373095 (the float below math.sqrt(2.0), because
  x*x - 2 is +4.4e-16 at one and -4.4e-16 at the other and a tie goes to the lower); assert abs(result - math.sqrt(2)) <= 2.3e-16;
  find_root(math.cos, 1, 2) == math.pi / 2 within 2.3e-16; find_root(lambda x: math.exp(x) - 5, 0, 10) == math.log(5) within 4.5e-16;
- a zero result is +0.0 (math.copysign(1.0, r) == 1.0), also for find_root(lambda x: -x, -2.0, -0.0) and for find_root(lambda x: x, -1, 0);
- cost: f is evaluated at a and b, then at most 64 times: with a counter, find_root(lambda x: 1.0 if x > 1e-310 else -1.0, -1e300, 1e300) makes at most 66 calls
  and returns a float within 5e-324 of 1e-310 (a step function: the jump is located to the last float); find_root(lambda x: x - 0.5, 0, 1) makes at most 66 calls;
- a function with a jump: find_root(lambda x: 1.0 if x > 0.3 else -1.0, -1, 1) is 0.3 (the last float where the value is -1: on a tie in |f| the lower end);
- find_roots(f, a, b, pieces) returns a sorted tuple of floats, one per piece in which f changes sign, plus every edge of a piece where f is exactly zero (reported once):
  find_roots(math.sin, -0.5, 10, 50) == (0.0, pi, 2 pi, 3 pi) within 1e-15 each, exactly 4 roots; find_roots(lambda x: (x-1)*(x-2)*(x-3), 0, 4, 4) == (1.0, 2.0, 3.0)
  (the edges 1, 2, 3 are roots); with 3 pieces also (1.0, 2.0, 3.0); with 1 piece exactly ONE root is returned, one of the three (two roots in a piece with a
  change of sign cannot be told apart); find_roots(lambda x: x*x + 1, -1, 1, 10) == (); find_roots(lambda x: x*x - 0.25, -1, 1, 1) == () (two roots in one piece,
  no change of sign: they are missed, by design), while with 4 pieces it is (-0.5, 0.5) (edges); find_roots(lambda x: x - 1.5, 1, 2, 7) == (1.5,);
  find_roots(lambda x: x, 1.0, math.nextafter(1.0, 2.0), 5) == () (an interval of two floats, more pieces than floats: accepted);
  find_roots(lambda x: x - 1.0, 1.0, 2.0, 3) == (1.0,) and find_roots(lambda x: x - 2.0, 1.0, 2.0, 3) == (2.0,) (roots at the two ends of the interval).

Limits (state them): BIG == 1e300, MAX_PIECES == 100000. Refusals (ValueError):
- f not callable (3, None, "sin": "must be callable");
- a or b that is a bool, a string, None, nan, inf, -inf, a complex, or beyond 1e300 (1.1e300; 1e300 and -1e300 are accepted: find_root(lambda x: x, -1e300, 1e300) == 0.0);
- a >= b: find_root(f, 2, 1) and find_root(f, 1, 1) ("a must be smaller than b"); the same for find_roots;
- no change of sign: find_root(abs, 1, 2), find_root(lambda x: -1.0, 0, 1) ("same sign");
- a value of f that is a string, None, a bool, a complex, nan or inf ("must return a finite real number"), at an end or in the middle of the search:
  find_root(lambda x: 1/x, -1, 1.5) does not return: it ends in an exception when 1/x overflows next to 0; assert only `pytest.raises((ValueError, ZeroDivisionError))`;
- pieces = 0, 100001, -1, 2.0, "3", None, True ("pieces must be an integer from 1 to 100000"); 1 and 100000 are accepted (find_roots(lambda x: x, -1, 1, 100000) contains 0.0 or a
  float within 1e-15 of it, and has exactly one element).
An exception raised by f itself is NOT caught: find_root(lambda x: 1/0, 0, 1) raises ZeroDivisionError.
