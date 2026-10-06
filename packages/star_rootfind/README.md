# star_rootfind — bracketed roots to the last float

The point of an interval where a real function changes sign, found by bisection over the floats: no tolerance to
choose, a fixed worst-case cost, and nothing closer to find when it returns. Standard library only.

```python
import math
import star_rootfind as sr
sr.find_root(lambda x: x**3 - 2*x - 5, 2, 3)     # 2.0945514815423265
sr.find_root(math.cos, 1, 2)                     # 1.5707963267948966
sr.find_roots(math.sin, -0.5, 10, 50)            # (0.0, 3.141592653589793, 6.283185307179586, 9.42477796076938)
```

## Requirements
- R1 `find_root(f, a, b)`, a < b, with f(a) and f(b) of opposite sign (or one of them zero), returns a float of
  [a, b] such that f changes sign between it and a neighbouring float, or f is exactly zero there.
- R2 The interval is halved in the number of floats it contains: f is evaluated at a, at b, and then at most 64
  times, whatever the width of the bracket. `find_roots(f, a, b, pieces)` splits [a, b] into equal pieces and
  returns, sorted, one root for each piece with a change of sign and every piece edge where f is zero.
- R3 Measured on 600 bracketed problems in six families (cube root, exponential, cosine, Kepler's equation up to
  e = 0.95, tanh, logarithm): the result agrees with mpmath at 50 digits, SciPy `brentq` and fluids `brenth`
  within 2.1e-15 relative.
- R4 Every function returns floats or raises `ValueError`: f not callable, limits that are not finite numbers
  within 1e300 or not in increasing order, no change of sign, a value of f that is not a finite real number, an
  invalid number of pieces. An exception raised by f itself is not caught.

## Evidence
- Published: the real root of x³ − 2x − 5 (Wallis 1685), 2.0945514815423265. Linear and cubic cases by hand.
- `crosscheck_rootfind.py`: mpmath (50 digits), SciPy and fluids, each in its own interpreter and arithmetic.

## What is NOT claimed
A change of sign is found, not proved to be a root: for a discontinuous function the result is the jump. The result
is exact for f as computed; its distance from the true root is the rounding error of f divided by its slope, which
this module cannot know (x*x − 2 on [0, 2] returns the float below sqrt(2) rounded). Roots without a change of sign
(double roots) are not found, and `find_roots` misses two roots that fall in the same piece: it is a scan, not a
guarantee of completeness. Bisection uses up to 64 evaluations where Brent's method often needs ten: this is for
certainty of termination and of the last digit, not for speed. One dimension only.
