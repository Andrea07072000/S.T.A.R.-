# star_linefit — least-squares line and correlation, correctly rounded

Slope and intercept of the least-squares straight line, their standard errors, the residual standard deviation and
the Pearson correlation, each computed exactly in rational arithmetic and rounded once. Standard library only.

```python
import star_linefit as lf
lf.fit([0, 1, 2, 3], [0, 1, 1, 2])                       # (0.6, 0.1)
lf.fit_errors([0, 1, 2, 3], [0, 1, 1, 2])                # (0.1414..., 0.2645..., 0.3162...)
lf.correlation([1, 2, 3, 4], [1, 3, 2, 4])               # 0.8
lf.fit([1e9, 1e9 + 1, 1e9 + 2], [5, 7, 9])               # (2.0, -1999999995.0): a far origin loses nothing
```

## Requirements
- R1 `fit(xs, ys)` returns (slope, intercept) of the line that minimises the sum of squared vertical residuals;
  `fit_errors` returns the standard errors of the two and the residual standard deviation (n - 2 degrees of freedom);
  `correlation` returns Pearson's r.
- R2 Every result is the float nearest to the exact value of its formula applied to the numbers given, square roots
  included; it does not depend on the order of the points, and r is exactly ±1 only for points exactly on a line.
- R3 Measured on 500 datasets of 3 to 40 points: all six results identical to the exact rational value (SymPy)
  rounded once. SciPy, NumPy and CPython's `statistics` agree within 1e-7 of the natural scale on the half of the
  corpus with x within ±10; on the half with x near 1e6 to 1e9 their own rounding reaches 4e-7.
  The NIST reference dataset Norris is reproduced to 1e-13 relative on its five certified values.
- R4 Every function returns floats or raises `ValueError`: data that are not lists or tuples of 2 to 100000 finite
  numbers within 1e100, different lengths, all x equal, all y equal (correlation), fewer than 3 points (errors), a
  result too large for a float.

## Evidence
- Published: NIST StRD linear regression dataset Norris, certified to 15 digits. Small cases by hand.
- `crosscheck_linefit.py`: SymPy (exact rationals), SciPy, NumPy and CPython, each in its own interpreter.

## What is NOT claimed
An ordinary least-squares line with errors only in y, equal weights and no intercept constraint: no weighted fit, no
errors in x, no polynomial or robust fit, no confidence intervals or tests. The standard errors assume independent
residuals of equal variance, which this module cannot check. "Exact" refers to the floats supplied. Exact arithmetic
is slower than floating point: it is for results that must not depend on rounding, not for large arrays.
