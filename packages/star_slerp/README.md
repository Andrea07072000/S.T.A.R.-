# star_slerp — interpolation of attitudes along the shortest arc

Spherical linear interpolation between unit quaternions, and interpolation in a table of attitudes at given times, as
needed to resample attitude telemetry. Standard library only.

```python
import math
import star_slerp as sl
identity = (1.0, 0.0, 0.0, 0.0)
quarter_turn_z = (math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4))
sl.slerp(identity, quarter_turn_z, 0.5)                 # (0.9238795325112867, 0.0, 0.0, 0.3826834323650898): 45 degrees about z
sl.interpolate([0, 10, 20], [identity, quarter_turn_z, identity], 15)   # half-way back
```

## Requirements
- R1 `slerp(q0, q1, t)` returns the attitude reached after the fraction t of the rotation from q0 to q1, about the
  same axis and at constant rate; quaternions are (w, x, y, z), scalar first, of unit length.
- R2 The path is always the shorter rotation: when q0 and q1 are in opposite hemispheres q1 is negated first. The
  result is of unit length and in the hemisphere of q0. `interpolate(times, quaternions, t)` applies the same rule
  between the two rows of the table that bracket t and refuses a t outside the table.
- R3 Measured on 600 pairs of attitudes (rotations from 1e-9 rad to within 0.1 degree of 180 degrees, either
  hemisphere): the largest component difference is 4.4e-16 from SciPy `Slerp`, 3.3e-16 from a route through NAIF
  SPICE rotation matrices, axis and angle, and 2.2e-16 from ahrs above its linear-interpolation threshold.
- R4 Every function returns a tuple of four floats or raises `ValueError`: a quaternion that is not four finite
  numbers of unit length within 1e-9 (never normalised silently), t out of range, a malformed or non-increasing table.

## Evidence
- By hand from the definition (Shoemake 1985): fractions of rotations about a fixed axis. No table is cited.
- `crosscheck_slerp.py`: SciPy, ahrs and SPICE, each in its own interpreter. One recorded observation, not a
  criterion: ahrs switches by documented design to linear interpolation for rotations below 3.6 degrees, where it
  differs from the other three by up to 4.8e-8.

## What is NOT claimed
Interpolation at constant rate between two attitudes, nothing else: no angular velocity, no smooth (C1) interpolation
across table rows (the rate jumps at each row), no extrapolation, no model of the true motion between samples. For a
rotation of exactly 180 degrees both arcs are equally short and the result follows the sign of the q1 supplied; other
libraries may choose the other arc. The quaternion convention is scalar-first Hamilton: data in another convention
must be converted before use.
