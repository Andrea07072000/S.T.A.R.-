# star_tabint — integrals of tabulated data, correctly rounded

Trapezoid rule, running integral and composite Simpson rule for a table of samples, each evaluated exactly in
rational arithmetic and rounded once. Standard library only.

```python
import star_tabint as ti
ti.trapezoid([0, 1, 2], [0, 1, 4])                 # 3.0
ti.cumulative([0, 1, 3], [0, 2, 2])                # (0.0, 1.0, 5.0)
ti.simpson([0, 1, 8], 1)                           # 4.0: exact for a cubic
ti.trapezoid([0, 1, 2], [1e16, 1.0, -1e16])        # 1.0 (a floating-point sum of the panels gives 0.0)
```

## Requirements
- R1 `trapezoid(xs, ys)` integrates the piecewise-linear curve through the points (xs strictly increasing, any
  spacing); `cumulative` returns the integral from the first point up to each point; `simpson(ys, step)` applies the
  composite Simpson rule to an odd number of equally spaced values.
- R2 Each result is the float nearest to the exact value of the rule on the numbers given: lobes that cancel lose
  nothing, and every element of `cumulative` is rounded from its own exact partial sum.
- R3 Measured on 500 tables of 2 to 60 points (1750 values): every value identical to the exact rational value
  (SymPy) rounded once; NumPy and SciPy within 3.3e-16 of the sum of the absolute panel areas.
- R4 Every function returns floats or raises `ValueError`: tables that are not lists or tuples of 2 to 100000 finite
  numbers within 1e100, different lengths, abscissas not strictly increasing, an even number of values or an invalid
  step for Simpson.

## Evidence
- By hand, exact: Simpson's rule with four intervals for 1/x on [1, 2] is 1747/2520; the trapezoid rule for x² at
  0, 1, 2 is 3; Simpson's rule for x³ at 0, 1, 2 is 4. No external publication is cited.
- `crosscheck_tabint.py`: SymPy (exact rationals), NumPy and SciPy, each in its own interpreter.

## What is NOT claimed
The value of a quadrature RULE on the samples, not the integral of the underlying function: the error of the rule
(of order h² for the trapezoid, h⁴ for Simpson on smooth data) is not estimated, and noisy or sparse samples give a
correspondingly poor integral. No Simpson rule for unequal spacing or an even number of points, no higher-order
rules, no extrapolation. "Exact" refers to the floats supplied. Exact arithmetic is slower than floating point.
