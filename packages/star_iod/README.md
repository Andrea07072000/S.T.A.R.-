# star_iod — velocity from three positions (Gibbs, Herrick-Gibbs)

The first step of orbit determination from radar or optical fixes: three position vectors give the velocity at the
middle one. Standard library only.

```python
import star_iod
v2 = star_iod.gibbs(r1, r2, r3)                                  # km -> km/s, positions more than ~0.4 deg apart
v2 = star_iod.herrick_gibbs(r1, r2, r3, t1, t2, t3)              # closely spaced positions with their times (s)
star_iod.separation_deg(r1, r2, r3)                              # to choose between the two
```

## Requirements
- R1 `gibbs(r1, r2, r3, mu, coplanar_tol_deg=3)`: Vallado Algorithm 54. Reproduces Example 7-3 within 5e-7 km/s. The
  direction of motion is the order r1, r2, r3. The sums of the textbook form are written with differences of
  neighbouring vectors: at 0.02 degrees of spacing the error is 2e-8 relative instead of 1.5e-5.
- R2 `herrick_gibbs(r1, r2, r3, t1, t2, t3, mu, coplanar_tol_deg=3)`: Vallado Algorithm 55, for closely spaced
  positions; `separation_deg` returns the two angles.
- R3 Measured domains (240 known orbits, largest relative velocity error by spacing in mean anomaly):

  | spacing | Gibbs | Herrick-Gibbs |
  |---|---|---|
  | 0.02 deg | 2.2e-08 | 6.7e-12 |
  | 0.1 deg | 1.1e-09 | 2.0e-11 |
  | 0.5 deg | 4.1e-11 | 1.1e-07 |
  | 2 deg | 2.6e-12 | 1.6e-05 |
  | 10 deg | 1.2e-13 | 6.0e-02 |
  | 40 deg | 1.2e-14 | 5.1e-01 |

  The two methods cross near 0.4 degrees. Gibbs agrees with Orekit's IodGibbs within 8e-9 at every spacing.
- R4 Every function returns three finite floats or raises `ValueError`: wrong shapes, non-numeric, boolean, NaN or
  infinite input; a zero position; mu <= 0; positions further than `coplanar_tol_deg` from a common plane; collinear
  or coincident positions; positions through which no orbit about the centre passes (Gibbs); times not strictly
  increasing (Herrick-Gibbs).

## Evidence
- Published: Vallado Example 7-3 (all components) and Example 7-4 (first two components; the third is not asserted,
  see `test_star_iod.py`).
- Truth without a solver: positions and velocity of known orbits from the conic equations (tests) and from NAIF
  `conics` (`crosscheck_iod.py`); Orekit IodGibbs as an independent implementation, probed on Example 7-3.

## What is NOT claimed
Perfect positions in, velocity out: no measurement noise model, no covariance, no angles-only methods (Gauss,
Laplace, Gooding), no differential correction. With noisy fixes the error of either method is dominated by the noise
divided by the arc length, not by the figures above.
