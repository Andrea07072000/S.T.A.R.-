# star_quaternion — rotations with one stated convention

Unit quaternions, rotation matrices and axis-angle. Standard library only.

```python
import star_quaternion as sq
q = sq.from_axis_angle((0, 0, 1), 90.0)        # (w, x, y, z), scalar first
sq.rotate(q, (1, 0, 0))                        # -> (0, 1, 0): active rotation, right-hand rule
R = sq.to_dcm(q)                               # rotate(q, v) == R v
```

## Requirements
- R1 Convention: quaternion (w, x, y, z) with the scalar first, Hamilton product, ACTIVE rotation; `to_dcm(q)` is the
  matrix R with `rotate(q, v) = R v`; `multiply(a, b)` applies b first, then a. This is the convention of NAIF SPICE
  (`q2m`, `m2q`, `qxq`); SciPy stores the scalar last.
- R2 `normalize`, `conjugate`, `multiply`, `rotate`, `to_dcm`, `from_dcm`, `from_axis_angle`, `to_axis_angle`,
  `angle_between_deg`. `from_dcm` uses the largest-component method (exact on half-turns, where the trace method
  divides by zero) and returns the quaternion with w >= 0. Angles are computed with atan2: a rotation of 1e-12
  degrees keeps its value.
- R3 Measured against SPICE and SciPy on 411 cases (random rotations, identity, half-turns, 1e-9 degree rotations):
  matrix, matrix-to-quaternion, product, rotated vector and angle agree within 9e-16.
- R4 Every function returns finite floats or raises `ValueError`: wrong shape, non-numeric, boolean, NaN, infinite or
  |value| >= 1e150 input; a zero quaternion or axis; a quaternion whose norm is further than 1e-6 from 1 where a unit
  quaternion is required (it is refused, not silently normalised); a matrix that is not orthonormal to 1e-9 or is a
  reflection.

## Evidence
- Rotations done by hand: quarter turns about each axis, the Hamilton relations ij = k, jk = i, ki = j, the order of
  the product, half-turns.
- `crosscheck_quaternion.py`: SPICE and SciPy, each in its own interpreter, first probed on the +90 degree rotation
  about +Z (a library or driver with the passive or transposed convention fails the probe).

## What is NOT claimed
No Euler angles (twelve conventions: a separate, explicit interface is needed), no interpolation, no attitude
determination. Frames are the caller's: the functions rotate vectors, they do not know what the frames are called.
