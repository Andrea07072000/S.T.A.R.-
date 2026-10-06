# Published values the tests of star_interp may cite (checked by the reviewer against the computation)

1. Meeus, Astronomical Algorithms (2nd ed.), Example 3.a: the distance of Mars from the Earth on 1992 November 7, 8 and 9 at 0h TD is
   0.884226, 0.877366 and 0.870531 AU; interpolated to November 8 at 4h 21m TD (interpolating factor n = 4.35 / 24 = 0.18125) it is 0.876125 AU.
   lagrange([7, 8, 9], [0.884226, 0.877366, 0.870531], 8 + 4.35 / 24) must equal 0.876125 within 5e-7 (the value is printed to 6 decimals).

Values derivable by hand (write the derivation in a comment; do not call them published):
- a polynomial of degree n - 1 is reproduced exactly by n points. With y = x^2 at the nodes 0, 1, 2: value 2.25 and derivative 3 at x = 1.5;
  derivative 2 at the node 1, 0 at the node 0 and 4 at the node 2. With y = x^3 + x + 1 at the nodes 0, 1, 2, 3 (values 1, 3, 11, 31):
  value 5.875 and derivative 7.75 at x = 1.5; derivative 13 at the node 2. Tolerance 1e-13;
- two points give the straight line: lagrange([0, 1], [3, 5], 0.25) == 3.5 and the derivative is 2 everywhere (tolerance 1e-14);
- constant data give the constant and derivative 0 (lagrange([0, 10], [5, 5], 3) == 5.0; tolerance 1e-14);
- at a node the tabulated value is returned EXACTLY (==), whatever the other points;
- the barycentric weights of the nodes 0, 1, 2 are [0.5, -1.0, 0.5]; of 0, 1, 2, 3 they are [-1/6, 1/2, -1/2, 1/6]; of 1, 3 they are [-0.5, 0.5];
- the order of the points does not matter: shuffling xs and ys together gives the same value within 1e-13 relative;
- linearity in the data: the interpolant of a*y1 + b*y2 is a times that of y1 plus b times that of y2 (1e-12 relative);
- shifting all nodes and x by the same amount changes nothing; scaling them by a factor leaves the value and divides the derivative by the factor;
- the derivative agrees with a centred finite difference of lagrange (step 1e-5 of the span) within 1e-6 relative, and it is continuous across a node
  (the value just beside a node tends to the value at the node);
- an eleven-point table of sin(x) with step 0.1 interpolates sin in the central interval within 1e-12 and cos by its derivative within 1e-10
  (the truncation error of a 10th-degree interpolant with that step is far smaller).

Constants and limits (state them): MIN_POINTS == 2, MAX_POINTS == 20, BIG == 1e150.
Refusals (ValueError): x outside [min(xs), max(xs)] (even by 1e-7: "extrapolation"); two equal nodes ("distinct"); one point; 21 points (20 are accepted);
ys of a different length; xs or ys that are not a list or tuple (a generator, a string, a dict, a set, None, a number); any node, value or x that is
a bool, a string, None, nan, inf, a complex or beyond 1e150; nodes so close that the weights overflow (lagrange([0, 1e-320], [0, 1], 0)):
"too close"; lagrange_weights applies the same checks to xs.
