# star_euler — Euler angles for the twelve sequences, one convention

Rotation matrix from three angles and back, for the six Tait-Bryan and the six proper Euler sequences.
Standard library only.

```python
import star_euler
R = star_euler.to_dcm("ZYX", yaw, pitch, roll)          # degrees; R = Rz(yaw) Ry(pitch) Rx(roll)
yaw, pitch, roll = star_euler.from_dcm("ZYX", R)
star_euler.is_singular("ZYX", R)                        # True at gimbal lock (pitch = +-90)
```

## Requirements
- R1 Convention: ACTIVE, INTRINSIC rotations: `to_dcm("ZYX", a1, a2, a3) = Rz(a1) Ry(a2) Rx(a3)` (turn about Z, then
  about the new Y, then about the new X). This is SciPy's upper-case sequence; NAIF SPICE `eul2m` returns the transpose.
- R2 `from_dcm(seq, R)`: middle angle in [-90, 90] (Tait-Bryan) or [0, 180] (proper), the others in (-180, 180].
  At gimbal lock the third angle is returned as 0 and the first carries the whole rotation; `is_singular` reports it.
- R3 Measured against SciPy and SPICE for all twelve sequences (720 regular cases, 24 at gimbal lock): matrices
  within 6e-16 (bit-identical to SPICE), angles within 4e-13 degrees, matrices rebuilt at gimbal lock within 6e-16.
- R4 Every function returns finite floats or raises `ValueError`: a sequence that is not one of the twelve (lower
  case included: it is not guessed), non-numeric, boolean, NaN or infinite input, a matrix of the wrong shape, not
  orthonormal to 1e-9, or a reflection.

## Evidence
- By hand: single quarter turns, the yaw-pitch-roll matrix as printed in flight-dynamics texts, the product of three
  elementary rotations for every sequence, the classical ZXZ angles.
- `crosscheck_euler.py`: SciPy and SPICE, each in its own interpreter, first probed on two textbook rotations (a
  driver with the passive or extrinsic reading fails the probe).

## What is NOT claimed
No extrinsic (fixed-axis) sequences as a separate option: reverse the letters and the angles to get them. No angular
rates or kinematic equations. Within about 1e-7 degrees of gimbal lock the first and third angles are not separable
and only their combination is returned.
