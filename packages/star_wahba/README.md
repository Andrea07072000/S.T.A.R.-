# star_wahba — attitude from vector observations

The orientation of a spacecraft from directions it measures (stars, the Sun, the magnetic field) and the same
directions known in a reference frame: TRIAD for two observations, Davenport's q-method for any number with weights.
Standard library only.

```python
import star_wahba as sw
refs = [(1, 0, 0), (0, 1, 0)]                  # known in the reference frame
bodies = [(0, -1, 0), (1, 0, 0)]               # measured in the body frame
sw.triad(refs[0], refs[1], bodies[0], bodies[1])   # ((0, 1, 0), (-1, 0, 0), (0, 0, 1)): b = A r
q = sw.q_method(refs, bodies, weights=[2, 1])      # (0.7071..., 0, 0, 0.7071...): scalar first
sw.rotation_matrix(q)                               # the same matrix
sw.wahba_loss(q, refs, bodies)                      # 0.0: the data are consistent
```

## Requirements
- R1 `triad(r1, r2, b1, b2)` returns the attitude matrix A (reference to body, b = A r) that matches the first pair
  exactly; `q_method(refs, bodies, weights)` returns the unit quaternion (w, x, y, z), w >= 0, that minimises
  Wahba's loss; `rotation_matrix(q)` converts it to A; `wahba_loss` evaluates 0.5 Σ w |b - A r|² with the weights
  normalised to sum 1.
- R2 TRIAD by two orthonormal triads; the q-method by the eigenvector of the largest eigenvalue of Davenport's K
  matrix, found with Jacobi rotations. Vectors need not be unit: only their directions are used.
- R3 Measured on 401 attitudes with 2 to 8 weighted directions, half of them with 0.01 rad of noise: the q-method
  agrees with the singular-value solution of SciPy within 7e-15 in every element of the matrix, TRIAD with the TRIAD
  of ahrs within 5e-16.
- R4 Every function returns floats or raises `ValueError`: vectors that are not three finite numbers or are zero,
  fewer than 2 or more than 1000 pairs, weights that are not positive, directions that do not fix an attitude
  (parallel), a zero quaternion.

## Evidence
- By hand: a quarter turn about z, a half turn about x, turns about x and y, the loss of two inconsistent
  observations (1 - cos of half the inconsistency).
- `crosscheck_wahba.py`: SciPy (`Rotation.align_vectors`) and ahrs (`TRIAD`), each in its own interpreter.

## What is NOT claimed
A single-frame estimate: no filtering over time, no gyro, no covariance of the estimate, no bias estimation, no
QUEST or ESOQ variants (they solve the same problem faster; this one favours robustness over speed). TRIAD and the
q-method give different answers on noisy data by design: TRIAD trusts the first observation entirely. Nearly
parallel observations are accepted down to 1e-12 and give an attitude that is very sensitive to noise about their
common direction: the functions do not warn about it. No published numerical example is reproduced: the references
(Wahba 1965, Black 1964, Davenport 1968, Markley and Crassidis) are cited for the method.
