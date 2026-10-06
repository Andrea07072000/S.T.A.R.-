# star_vec3 — the three-dimensional vector operations of orbit and attitude code

Dot, cross and triple product, length, distance, unit vector, the angle between two directions, and the parts of a
vector along and across another: written once, with the numerically careful form of each.
Standard library only.

```python
import star_vec3 as sv
sv.cross((1, 0, 0), (0, 1, 0))              # (0.0, 0.0, 1.0)
sv.angle_deg((1, 0, 0), (1, 1e-9, 0))       # 5.73e-08 deg: nearly parallel vectors keep their digits
sv.project((1, 2, 3), (-2, 0.5, 4))         # the part of the first vector along the second
sv.unit((3e-300, 4e-300, 0))                # (0.6, 0.8, 0.0): no underflow
```

## Requirements
- R1 `dot`, `cross`, `triple`, `norm`, `distance`, `unit`: the definitions, with the length computed without
  intermediate overflow or underflow and the sums compensated.
- R2 `angle_deg` as atan2(|a × b|, a · b) on unit vectors: in [0, 180], accurate near 0 and near 180 degrees and
  independent of the lengths; `project` and `reject`, which add up to the first vector.
- R3 Measured on 600 triples of vectors (lengths 1e-3 to 1e9; 200 pairs within 1e-9 to 1e-3 rad of parallel or
  antiparallel): within 6e-16 of SPICE and ERFA relative to the lengths involved, angles within 5e-14 deg; the
  triple product within 8e-15 of NumPy's determinant.
- R4 Every function returns floats or raises `ValueError`: a vector that is not a list or tuple of exactly three
  finite real numbers within ±1e100 (booleans refused), or the zero vector where a direction is needed.

## Evidence
- By hand: the basis vectors, a worked pair of vectors, right angles, Lagrange's identity, the extremes of the range.
  There is no published numerical example for a definition: none is claimed.
- `crosscheck_vec3.py`: SPICE, ERFA and NumPy, each in its own interpreter, each probed on the by-hand cases.

## What is NOT claimed
No matrices, no rotations (see `star_quaternion` and `star_euler`), no vectors of other dimensions. The triple
product is compared with one library (NumPy) only. Products of components below 1e-154 underflow to zero in `dot`,
`cross` and `triple` as in any double-precision code; `norm`, `unit` and `angle_deg` are not affected.
