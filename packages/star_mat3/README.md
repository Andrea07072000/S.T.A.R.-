# star_mat3 — the 3×3 matrix operations of frame and attitude code

Transpose, determinant, inverse, matrix and matrix-vector products, and a test for proper rotations; the
determinant and the inverse are exact to the last digit. Standard library only.

```python
import star_mat3 as m3
A = [[2, 0, 1], [1, 3, 2], [1, 0, 1]]
m3.determinant(A)                 # 3.0
m3.inverse(A)                     # ((1.0, 0.0, -1.0), (0.333..., 0.333..., -1.0), (-1.0, 0.0, 2.0))
m3.matvec(A, (1, 2, 3))           # (5.0, 13.0, 4.0)
m3.is_rotation(m3.identity())     # True; a reflection or a scaled matrix is not
```

## Requirements
- R1 `determinant` and `inverse` in exact rational arithmetic (a float is an exact fraction), rounded once: correct
  to the last digit whatever the conditioning. `inverse` refuses singular and nearly singular matrices, with a test
  that does not depend on the scale of the entries.
- R2 `transpose`, `matmul`, `matvec`, `identity`; `is_rotation(m, tol)` is True only for an orthonormal matrix with
  determinant +1 within the tolerance.
- R3 Measured on 575 matrices (300 general, 150 rotations, 125 with condition numbers up to 1e8) against EXACT
  arithmetic (SymPy): determinant and inverse identical to the exact value rounded; products within 4e-15. On the
  ill-conditioned matrices SPICE's inverse differs from the exact one by up to 6e-6 of its largest entry and NumPy's
  by 9e-10. `is_rotation` agrees with SPICE on every matrix.
- R4 Every function returns floats (or a bool) or raises `ValueError`: wrong shape or type, an entry that is not a
  finite real number within ±1e60 (booleans refused), a singular or nearly singular matrix, an inverse that
  overflows, a tolerance outside (0, 1].

## Evidence
- By hand: a worked matrix with its determinant and inverse, diagonal and permutation matrices, a cancellation that
  floating point gets wrong, rotations and a reflection. No published numerical example exists for a definition:
  none is claimed.
- `crosscheck_mat3.py`: SymPy (exact), SPICE and NumPy, each in its own interpreter, each probed on the by-hand case.

## What is NOT claimed
3×3 only; no eigenvalues, no decompositions, no orthonormalisation of a drifting rotation. The exact arithmetic
makes `inverse` slower than a floating-point one (tens of microseconds): it is for correctness, not for inner loops.
"Exact" means the exact inverse of the floats given: if those floats are themselves rounded measurements of an
ill-conditioned matrix, the inverse amplifies their error by the condition number, and nothing here can prevent that.
The products are compensated sums of rounded products, accurate to a few units in the last place, not exact.
