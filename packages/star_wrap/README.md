# star_wrap — reducing, differencing and averaging angles

The four operations that every angle needs before it is used: bring it into [0, 360) or [-180, 180), take the
shortest signed difference of two, and average a set without the 359°/1° trap. Standard library only.

```python
import star_wrap as sw
sw.wrap360(-2318.19280)             # 201.80720: Meeus Example 25.a
sw.wrap180(190.0)                   # -170.0
sw.difference(10.0, 350.0)          # 20.0: the short way round
sw.circular_mean([350.0, 10.0])     # 0.0, not 180
```

## Requirements
- R1 `wrap360` returns [0, 360) and `wrap180` returns [-180, 180), with the exact floating-point remainder: an angle
  of 1e9 deg loses nothing in the reduction. Reproduces the reductions of Meeus Example 25.a.
- R2 `difference(a, b)` is a − b as the shortest signed rotation in [-180, 180); `circular_mean(angles)` is the
  direction of the mean unit vector in [0, 360), and is refused when the vectors cancel.
- R3 Measured on 600 angles up to 1e6 deg (100 within 1e-9 deg of a multiple of 180) and 600 samples: identical
  to astropy, within 2.4e-10 deg of ERFA (which rounds through radians), circular means within 6e-14 deg of SciPy;
  every result inside its range.
- R4 Every function returns a finite float in its range or raises `ValueError`: non-numeric, boolean, NaN or
  infinite input, an angle beyond 1e12 deg, an empty or non-list/tuple collection or one longer than 1,000,000, a
  mean resultant length below 1e-9.

## Evidence
- Published: Meeus, Astronomical Algorithms, Example 25.a (−2318.19280° = 201.80720°, −2241.00603° = 278.99397°).
- `crosscheck_wrap.py`: ERFA, astropy and SciPy, each in its own interpreter, each probed before being compared.

## What is NOT claimed
Half a turn is −180, not +180: callers who need (−180, 180] must map it themselves. The circular mean is not a
weighted mean and gives no dispersion. An angle is a float: 1e12 deg still reduces exactly, but its own last digit
is already 1e-4 deg.
