# star_rotframe — position and velocity between an inertial and a rotating frame

The state (position and velocity) of a point seen from a frame rotating about z, and back: the step between an
Earth-centred inertial frame and the Earth-fixed frame once the rotation angle is known. Standard library only.

```python
import math
import star_rotframe as rf
R, w, a = 6378.137, rf.EARTH_RATE, math.pi / 2
rf.to_rotating((0.0, R, 0.0), (-w * R, 0.0, 0.0), a)     # ((6378.137, 0.0, 0.0), (0.0, 0.0, 0.0)): a point on the equator is at rest
rf.to_rotating((7000.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0) # ((7000.0, 0.0, 0.0), (0.0, -0.51044805, 0.0)): a fixed star-ward point drifts west
```

## Requirements
- R1 `to_rotating(r, v, angle, rate)` returns r' = Rz(angle) r and v' = Rz(angle) v − w × r', with w = (0, 0, rate):
  the velocity seen in the rotating frame, transport term included. `angle` is in radians, about +z.
- R2 `to_inertial` is the exact inverse. The default rate is the WGS-84 angular velocity of the Earth,
  `EARTH_RATE` = 7.292115e-5 rad/s; any other rate, of either sign, can be given.
- R3 Measured on 600 states (orbits in km and in metres, random magnitudes, angles up to 1e8 rad, rates up to
  0.1 rad/s), there and back: agreement with NAIF SPICE (`rav2xf`), SciPy and astropy within 5.2e-16 of |r| and of
  |v| + |rate| |r|; round trip within 3.4e-16.
- R4 Every function returns two tuples of three floats or raises `ValueError`: vectors that are not three finite
  numbers within 1e15, an angle or a rate that is not finite or is out of range, booleans.

## Evidence
- Published: the WGS-84 angular velocity. By hand: a point fixed on the equator is at rest in the rotating frame; an
  inertially fixed point drifts at −w × r.
- `crosscheck_rotframe.py`: SPICE, SciPy and astropy, each in its own interpreter.

## What is NOT claimed
A rotation about one fixed axis at a constant rate. For the Earth this leaves out polar motion, precession, nutation
and the variation of the length of day: this module is NOT a full ICRS-to-ITRS transformation, and the angle (Earth
Rotation Angle or sidereal time) must come from elsewhere (see `star_era` in this repository). Over a day the neglected
terms move a ground point by metres to tens of metres. No acceleration (Coriolis and centrifugal terms) is returned.
Units are whatever the caller uses, consistently.
