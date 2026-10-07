# Values the tests of star_tabint may cite (checked by the reviewer against the computation)

No external publication is needed: every value below is exact arithmetic that can be redone by hand (write the derivation in a comment).

- trapezoid(xs, ys) is the sum of (x[k+1] - x[k]) * (y[k] + y[k+1]) / 2: trapezoid([0, 1, 2], [0, 1, 4]) == 3.0 [0.5 + 2.5]; trapezoid([0, 1], [3, 5]) == 4.0;
  trapezoid([0, 2, 3], [1, 1, 1]) == 3.0 (a constant: the width); trapezoid([1, 2, 4, 8], [2, 4, 8, 16]) == 63.0 (the line y = 2x: x^2 from 1 to 8, exact for a line
  on any grid); trapezoid([-1, 0, 1], [-1, 0, 1]) == 0.0 (an odd function); trapezoid([0, 0.5, 2], [4, 0, 2]) == 2.5 [1.0 + 1.5];
- lobes that cancel are summed exactly: trapezoid([0, 1, 2, 3], [1e16, 1, -1e16, 1]) == -4999999999999998.0 [the exact value is (3 - 1e16)/2 = -4999999999999998.5,
  which rounds to the even neighbour]; trapezoid([0, 1, 2], [1e16, 1.0, -1e16]) == 1.0 [0.5 (1e16 + 1) + 0.5 (1 - 1e16)];
- cumulative(xs, ys) returns a tuple as long as the table, first element 0.0, last element == trapezoid(xs, ys): cumulative([0, 1, 3], [0, 2, 2]) == (0.0, 1.0, 5.0);
  cumulative([0, 1, 2, 3], [1, 1, 1, 1]) == (0.0, 1.0, 2.0, 3.0); cumulative([0, 1], [3, 5]) == (0.0, 4.0); each element k equals trapezoid(xs[:k+1], ys[:k+1]) exactly
  (for k >= 1); cumulative([0, 1, 2, 3], [1e16, 1, -1e16, 1]) == (0.0, 5000000000000000.0, 1.0, -4999999999999998.0);
- simpson(ys, step) is step / 3 * (y0 + 4 y1 + 2 y2 + ... + 4 y(n-2) + y(n-1)) for an odd number n of values: simpson([0, 1, 8], 1) == 4.0 (x^3 on [0, 2]: exact for a
  cubic); simpson([0, 1, 4, 9, 16], 0.5) == 32/3 within 2e-15 (x^2 on [0, 2] ... with step 0.5 the values 0, 1, 4, 9, 16 are (2x)^2: integral 4 * 8/3);
  simpson([1, 1, 1], 2) == 4.0; simpson([5, 5, 5, 5, 5], 0.25) == 5.0; simpson([1, 0.8, 2/3, 4/7, 0.5], 0.25) == 1747/2520 within 2e-16 (1/x on [1, 2], four intervals:
  (1/12) (1 + 16/5 + 4/3 + 16/7 + 1/2) = 1747/2520 = 0.693253968253968...); the weights of the inner points alternate 4, 2: simpson([0, 1, 0, 0, 0], 3) == 4.0 and
  simpson([0, 0, 1, 0, 0], 3) == 2.0, simpson([1, 0, 0, 0, 0], 3) == 1.0 and simpson([0, 0, 0, 0, 1], 3) == 1.0;
- for a straight line the two rules agree: simpson([1, 3, 5], 1) == trapezoid([0, 1, 2], [1, 3, 5]) == 6.0;
- scaling: trapezoid(xs, [2 * y for y in ys]) == 2 * trapezoid(xs, ys) exactly (a power of two); reversing the sign of ys reverses the sign of the result;
  shifting xs by an integer does not change trapezoid for integer abscissas;
- a tuple and a list give the same result; integers are accepted; every result is a float (cumulative: a tuple of floats).

Limits (state them): BIG == 1e100, TINY == 1e-100, MAX_POINTS == 100000. Extremes stay finite: trapezoid([-1e100, 1e100], [1e100, 1e100]) == 2e200. Refusals (ValueError):
- xs or ys that is not a list or tuple (a string, a generator, None) or has fewer than 2 values ("xs must be a list or tuple" / "ys must be a list or tuple");
- a value that is a bool, a string, None, nan, inf, a complex, or beyond 1e100 ("must be finite real numbers");
- different lengths ("same length"); xs not strictly increasing: equal neighbours [0, 0, 1], decreasing [1, 0] ("strictly increasing");
- simpson: an even number of values (2 or 4: "odd number of values"); a step that is 0, negative, 9e-101, 1.1e100, nan, inf, a bool, a string, None ("step must be");
  1e-100 and 1e100 are accepted (simpson([1, 1, 1], 1e-100) == 2e-100).
Do NOT build lists of 100001 values more than once in the tests (slow): one test for that limit is enough.
