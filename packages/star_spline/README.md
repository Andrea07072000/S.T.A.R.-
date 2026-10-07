# star_spline — natural cubic spline, correctly rounded

The smooth curve through tabulated points: values, slope and integral of the natural cubic spline, each number the
float nearest to the true one for the table as given. Standard library only.

```python
import star_spline as ss
xs, ys = [1, 2, 3], [2, 3, 5]
ss.values(xs, ys, [1.5, 2.5])          # (2.40625, 3.90625)
ss.derivatives(xs, ys, [1, 2, 3])      # (0.75, 1.5, 2.25)
ss.second_derivatives(xs, ys)          # (0.0, 1.5, 0.0)
ss.integral(xs, ys, 1, 3)              # 6.375
```

## Requirements
- R1 `values(xs, ys, points)` and `derivatives(xs, ys, points)` return the natural cubic spline through the points
  (xs strictly increasing) and its first derivative at each point; `second_derivatives(xs, ys)` its second derivative
  at the knots (zero at the two ends); `integral(xs, ys, a, b)` its integral between two abscissas of the table.
- R2 The tridiagonal system is solved in exact rational arithmetic on the floats given and each result is evaluated
  exactly and rounded once: knots very close together, values far from zero or a long table cost no digit.
- R3 Measured on 151 tables of 3 to 40 unevenly spaced knots, 25 points each: values within 8e-15 and first
  derivatives within 2e-14 of SciPy (relative to the scale of each table), second derivatives within 2e-12, the
  integral within 3e-13; values within 7e-15 and first derivatives within 2e-15 of Hipparchus.
- R4 Every function returns floats or raises `ValueError`: tables that are not 2 to 300 finite real numbers within
  1e100, different lengths, knots that are not strictly increasing, a point outside the table (a spline is not
  extrapolated), a result too large for a float.

## Evidence
- Published: the worked example of Burden and Faires, Numerical Analysis (three points), reproduced exactly.
- `crosscheck_spline.py`: SciPy (`CubicSpline`, natural) and Hipparchus (`SplineInterpolator`).

## What is NOT claimed
The natural end condition only (zero second derivative at both ends): no clamped, not-a-knot or periodic spline, no
smoothing spline, no extrapolation. A spline through noisy or unevenly sampled data can overshoot between the knots;
exact arithmetic does not make it a good model. Exact arithmetic is slow: about a second for a table of 300 knots,
and every call solves the table again (pass all the points you need in one call). Nothing beyond 300 knots.
"Nearest float" refers to the floats passed in, not to the decimal numbers you may have meant.
