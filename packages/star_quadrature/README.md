# star_quadrature — Gauss-Legendre quadrature

Nodes and weights of the Gauss-Legendre rules from 1 to 32 points, integration of a function over an interval, and
the Legendre polynomials with their first derivative. Standard library only.

```python
import math
import star_quadrature as sq
sq.gauss_legendre(2)                    # ((-0.5773502691896257, 0.5773502691896257), (1.0, 1.0))
sq.integrate(math.sin, 0, math.pi, 10)  # 2.0 (to the last digits)
sq.integrate(lambda t: t**5, 0, 2, 3)   # 10.666...: exact for polynomials up to degree 2n - 1
sq.legendre(2, 0.5)                     # (-0.125, 1.5): P_2 and its derivative
```

## Requirements
- R1 `gauss_legendre(n)` returns the n nodes (increasing) and the n weights of the rule on [-1, 1], for n from 1 to
  32. Each node is the float nearest to the true root of P_n: the polynomial is built with exact coefficients and
  the root is found by bisection over the floats with the exact sign. Each weight is evaluated in exact arithmetic
  and rounded once. Nodes are exactly antisymmetric and weights exactly symmetric.
- R2 `integrate(f, a, b, n)` applies the n-point rule to [a, b]; `legendre(n, x)` returns P_n(x) and P_n'(x) for
  x in [-1, 1] by the three-term recurrences (no division by 1 - x²).
- R3 Measured on all 32 rules (528 nodes and weights): every node and every weight equals SymPy's 40-digit value
  rounded to a float. 400 Legendre values with derivatives and 120 exact integrals of monomials agree with SymPy
  within 1e-14 relative; NumPy and SciPy agree within their own accuracy.
- R4 Every function returns floats or raises `ValueError`: n that is not an integer in range (booleans and floats
  refused), x outside [-1, 1], limits that are not finite numbers within 1e150, f that is not callable or returns
  something that is not a finite real number, an overflowing result.

## Evidence
- Published: Abramowitz & Stegun, table 25.4, the rules with 2, 3, 4 and 5 points. Closed forms for 1, 2 and 3
  points and the first Legendre polynomials, by hand.
- `crosscheck_quadrature.py`: SymPy (40 digits, exact polynomials), NumPy and SciPy, each in its own interpreter.

## What is NOT claimed
Fixed rules only: no adaptive integration, no error estimate, no other weight functions (Gauss-Lobatto, Laguerre,
Hermite, Kronrod), no rule beyond 32 points. The rule is exact only for polynomials up to degree 2n - 1; for any
other function the result is an approximation whose error this module does not bound: singular, discontinuous or
strongly oscillating integrands need more than a fixed rule. The first call for a given n builds the rule in exact
arithmetic (about two seconds for all rules up to 32 points on a laptop); later calls are cached.
`legendre` is double-precision recurrence, accurate to about 1e-14 relative to the size of the value.
