# star_linsolve — small linear systems, correctly rounded

Determinant, solution and inverse of a square matrix of order 1 to 20, each number the float nearest to the true one
for the matrix as given. Standard library only.

```python
import star_linsolve as sl
sl.det([[1, 2], [3, 4]])                      # -2.0
sl.solve([[2, 1], [1, 3]], [3, 5])            # (0.8, 1.4)
sl.inverse([[4, 7], [2, 6]])                  # ((0.6, -0.7), (-0.2, 0.4))
e = 2 ** -52
sl.solve([[1, 1], [1, 1 + e]], [2, 2 + 2 * e])   # (0.0, 2.0): nearly singular, solved exactly
```

## Requirements
- R1 `det(a)` returns the determinant, `solve(a, b)` the vector x with a x = b, `inverse(a)` the inverse, for a
  matrix given as a list or tuple of rows.
- R2 The elimination is done in exact rational arithmetic on the floats given and each result is rounded once: the
  conditioning of the matrix costs no digit. A matrix is singular exactly when its exact determinant is zero; no
  tolerance is involved, so a nearly singular matrix is solved and an exactly singular one is refused.
- R3 Measured on 151 systems (110 well conditioned, 40 badly conditioned, and the Hilbert matrix of order 3 scaled
  to integers): determinant, solution and inverse equal the exact rational results of SymPy rounded to a float and
  those of mpmath at 400 digits. NumPy agrees within 1e-12 on the well-conditioned systems; on the badly conditioned
  ones it loses most digits or refuses the matrix as singular (the numbers are in the evidence file).
- R4 Every function returns floats or raises `ValueError`: a matrix that is not square or larger than 20, entries
  that are not finite real numbers within 1e100 (booleans refused), a right-hand side of the wrong length, a singular
  matrix (for `solve` and `inverse`), a result too large for a float.

## Evidence
- Published: the Hilbert matrix of order 3 (determinant 1/2160 and its integer inverse), used scaled by 60 so that
  the input is exact. Small matrices by hand.
- `crosscheck_linsolve.py`: SymPy (exact), mpmath (400 digits) and NumPy, each in its own interpreter.

## What is NOT claimed
Exact arithmetic on the floats you pass: 0.1 is not one tenth, and the solution of a badly conditioned system still
changes a lot when the data change a little; the answer is exact for the matrix given, not for the one you meant.
A determinant returned as 0.0 can be an underflow (two entries of 1e-200 on the diagonal) and is not by itself a proof
of singularity: `solve` and `inverse` decide on the exact value. Not for large systems: nothing beyond order 20, no
sparse matrices, no least squares, no eigenvalues, no condition number; a 20 x 20 inverse takes about a quarter of a
second on a laptop and more when the entries have many different exponents.
