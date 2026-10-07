# star_polyfit — least-squares polynomial, correctly rounded

Fit of a polynomial of degree 0 to 10 to data, weighted or not, with every coefficient the float nearest to the true
least-squares value. Standard library only.

```python
import star_polyfit as sp
sp.polyfit([0, 1, 2, 3], [0, 1, 0, 1], 1)        # (0.2, 0.2): intercept first, then slope
sp.polyfit([1e9 + k for k in range(8)], [k * k for k in range(8)], 2)   # (1e+18, -2000000000.0, 1.0), exactly
sp.polyval((1, 2, 3), 2)                         # 17.0
sp.residual_sum([0, 1, 2, 3], [0, 1, 0, 1], (0.2, 0.2))   # 0.8
```

## Requirements
- R1 `polyfit(xs, ys, degree, weights=None)` returns the coefficients, lowest power first, of the polynomial that
  minimises the sum of w (y - p(x))². `polyval(coefficients, x)` evaluates a polynomial; `residual_sum(xs, ys,
  coefficients, weights=None)` returns the weighted sum of squared residuals.
- R2 The normal equations are formed and solved in exact rational arithmetic on the floats given, and each result is
  rounded once: the conditioning of the problem costs no digit. `polyval` and `residual_sum` are exact sums rounded
  once as well.
- R3 Measured on 161 problems (120 well conditioned, 40 badly conditioned, and the NIST dataset Wampler1): every
  coefficient equals the exact rational solution of SymPy rounded to a float and the QR solution of mpmath at 120
  digits. NumPy agrees within 1e-9 on the well-conditioned problems; on the badly conditioned ones (x in
  [1000, 1001], x = 1e6 + k) its coefficients share no digit with the exact ones (the numbers are in the evidence
  file).
- R4 Every function returns floats or raises `ValueError`: a degree that is not an integer from 0 to 10, data that
  are not lists or tuples of finite real numbers within 1e100 (booleans refused), different lengths, negative
  weights, fewer distinct x with a positive weight than degree + 1, a result too large for a float.

## Evidence
- Published: NIST Statistical Reference Datasets, Wampler1 (certified coefficients all 1, reproduced exactly) and
  Wampler2. Lines and parabolas by hand.
- `crosscheck_polyfit.py`: SymPy (exact), mpmath (QR at 120 digits) and NumPy, each in its own interpreter.

## What is NOT claimed
Exact coefficients are not a good model: a high-degree fit of noisy data oscillates, and the exact coefficients of a
badly conditioned problem change a lot when the data change a little; the float nearest to each coefficient is still
only a float, and evaluating the fitted polynomial in ordinary float arithmetic far from the origin can lose every
digit (use `polyval`, or centre the data). No standard errors, no covariance matrix, no orthogonal polynomials, no
automatic choice of the degree, no robust fitting. Exact arithmetic is slow: about a second for 2000 points at degree
10 on a laptop. "Nearest float" refers to the floats passed in, not to the decimal numbers you may have meant.
