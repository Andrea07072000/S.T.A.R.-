# star_mrp — modified Rodrigues parameters

The three-number attitude representation used in spacecraft attitude control laws: conversions with quaternions,
direction cosine matrices and rotation vectors, the shadow set, composition of rotations, and the kinematic
equation. Standard library only.

```python
import star_mrp as sm
sm.mrp_from_quaternion((0.5, 0.5, 0.5, 0.5))     # (0.333..., 0.333..., 0.333...): 120 degrees about (1, 1, 1)
sm.quaternion_from_mrp((0, 0, 1))                # (0.0, 0.0, 0.0, 1.0): a half turn about z
sm.shadow((0, 0, 3))                             # (0, 0, -0.333...): the same attitude, the shorter way
sm.compose((0, 0, 0.41421356237309503), (0, 0, 0.41421356237309503))   # (0, 0, 1): two quarter turns
sm.mrp_rate((0.5, 0, 0), (0, 0.4, 0))            # (0, 0.075, 0.1): d(sigma)/dt for a body rate in rad/s
```

## Requirements
- R1 `mrp_from_quaternion`, `quaternion_from_mrp`, `dcm_from_mrp`, `rotation_vector_from_mrp`,
  `mrp_from_rotation_vector` convert between sigma = e tan(phi/4) and the other representations; `shadow` and
  `switch` give the other MRP of the same attitude; `compose(first, second)` chains two rotations; `mrp_rate(s,
  omega)` is the kinematic equation.
- R2 Quaternions are scalar first; the matrix takes reference to body; results of conversions and of `compose` are on
  the short rotation (|sigma| <= 1, quaternion with w >= 0, angle in [0, pi]). `compose` goes through quaternions,
  so two rotations that add up to a full turn give zero and not a division by zero.
- R3 Measured on 601 pairs of MRPs with norms from 1e-8 to 5 (a third beyond 1): eight operations agree with
  Basilisk within 6e-16 and seven with SciPy within 2e-15.
- R4 Every function returns floats or raises `ValueError`: vectors that are not three (or four) finite real numbers
  within 1e150, a zero quaternion, the shadow of the zero MRP, a threshold that is not positive.

## Evidence
- By hand from the definition (Schaub and Junkins): 120 degrees about (1, 1, 1), quarter and half turns, the shadow
  set, the kinematic equation on and off the rotation axis.
- `crosscheck_mrp.py`: Basilisk (`RigidBodyKinematics`) and SciPy (`Rotation`), each in its own interpreter.

## What is NOT claimed
Kinematics only: no dynamics, no control law, no integrator (`mrp_rate` is the right-hand side; integrating it and
switching to the shadow set is left to the caller). At exactly half a turn the two MRPs of norm 1 are equally short
and either may be returned. No Gibbs vector (classical Rodrigues parameters), no Euler angles (see star_euler). No
published numerical table is reproduced: the references are cited for the formulas.
