# star_poly — real roots of quadratics and cubics

The distinct real roots of a quadratic or a cubic, with their number decided exactly and each root correct to the
last digits; and Horner evaluation of a polynomial with its derivative. Standard library only.

```python
import star_poly as sp
sp.quadratic_roots(1, -1e8, 1)        # (1e-08, 99999999.99999999): the textbook formula gives 7.45e-09 for the first
sp.quadratic_roots(1, -2, 1)          # (1.0,): a double root is one root
sp.cubic_roots(1, -6, 11, -6)         # (1.0, 2.0, 3.0)
sp.cubic_roots(1, 0, -3, 2)           # (-2.0, 1.0): (x - 1)^2 (x + 2)
sp.evaluate([1, -6, 11, -6], 2.0)     # (0.0, -1.0): value and derivative
```

## Requirements
- R1 `quadratic_roots(a, b, c)` and `cubic_roots(a, b, c, d)` return the distinct real roots, sorted. The number of
  roots is decided by the discriminant computed in exact rational arithmetic: a double or triple root is reported
  once, and a polynomial with no real root returns an empty tuple.
- R2 Each root is located inside an interval that holds no other root, by bisection over the floats driven by the
  exact sign of the polynomial (at most 64 steps, no starting guess): roots of very different size keep their digits and none is lost to a neighbour.
  `evaluate(coefficients, x)` returns the value and the first derivative (Horner).
- R3 Measured on 640 quadratics and cubics (random, exact multiple roots, roots separated by up to 1e12, leading
  coefficients down to 1e-30): the number of real roots equals SymPy's exact count in every case, and every root
  equals the exact root rounded to a float; all are roots for mpmath at 60 digits and for NumPy.
- R4 Every function returns floats or raises `ValueError`: a zero leading coefficient, a non-finite or non-numeric
  coefficient (booleans included), a coefficient beyond 1e60, a malformed coefficient list, an overflowing result.

## Evidence
- Published: the classic cancellation example x² − 1e8 x + 1 (Forsythe 1970; Numerical Recipes 5.6). Factored
  polynomials with integer roots, double and triple roots, Vieta's formulas, by hand.
- `crosscheck_poly.py`: SymPy (exact real roots), mpmath (60 digits) and NumPy, each in its own interpreter.

## What is NOT claimed
Real roots only: no complex roots, no quartics or higher degrees. "Exact" refers to the polynomial whose
coefficients are the floats given: if those are rounded measurements, a nearly double root may be reported as two,
one or none, and that is the correct answer for the numbers supplied. Two distinct roots closer than one float are
returned as two neighbouring floats. The exact arithmetic makes these functions slower than a closed formula (tens
to hundreds of microseconds): they are for correctness, not for inner loops. `evaluate` is plain double-precision
Horner, not compensated.
