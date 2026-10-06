# star_cw — relative motion near a circular orbit (Clohessy-Wiltshire)

Closed-form transition matrix, free drift and two-impulse rendezvous in the rotating frame of a chief on a circular
orbit. Standard library only.

```python
import math, star_cw
n = math.sqrt(398600.4418 / 7000.0**3)                    # rad/s, mean motion of the chief
star_cw.propagate((0.0, -1.0, 0.0, 0.0, 0.0, 0.0), n, 600.0)        # hold point 1 km behind: stays there
dv1, dv2 = star_cw.rendezvous((0, -1, 0), (0, 0, 0), (0, 0, 0), n, 0.25 * 2 * math.pi / n)
```

## Requirements
- R1 Frame and state: x radial outward, y along the velocity, z along the orbit normal, origin at the chief; state
  (x, y, z, vx, vy, vz) relative to the rotating frame; n in rad/s; any consistent length unit.
- R2 `stm(n, t)` (6x6) and `propagate(state, n, t)`: the closed-form solution; agrees with SciPy's matrix exponential
  of the system matrix within 1.1e-13 relative on 300 states and times up to three revolutions.
- R3 `rendezvous(r0, v0, rf, n, t)` returns (dv1, dv2): the impulse now that brings the deputy to the point rf of the
  rotating frame after t, and the impulse there that stops it relative to rf.
- R4 Every function returns finite floats of the documented shape or raises `ValueError`: non-numeric, boolean, NaN,
  infinite or |value| >= 1e150 input; wrong shapes; n <= 0; t <= 0 for a rendezvous; and the singular transfer times
  (whole and half revolutions, and the other roots of 8(1 - cos nt) = 3 nt sin nt), where no finite impulse reaches
  an arbitrary point.

## How far the model is from real motion (measured)
Against two full Keplerian orbits propagated with NAIF prop2b (chief at 7000 km, drift up to one revolution, relative
velocity up to n times the separation), the largest position difference was 0.09 mm at 1 m separation, 1.2 m at
100 m, and 12 km at 10 km: it grows as separation squared over orbit radius, with a factor of up to about 850.
Beyond a few hundred metres over a revolution the linear model is a first guess, not a prediction.

## Evidence
- Textbook trajectories (hold point, 12 pi x0 drift per revolution, closed 2-by-1 ellipse, cross-track oscillation).
- A fixed-step RK4 integration of the three equations in the tests (no closed form involved).
- `crosscheck_cw.py`: SciPy `expm` (algebra) and NAIF prop2b differencing (physics), each in its own interpreter.

## What is NOT claimed
Circular chief only (no Tschauner-Hempel), no J2, drag or thrust arcs, no collision check along the transfer, no
optimisation of the transfer time. A found defect is recorded in the module: the first version returned an empty
tuple from `propagate`; the cross-check now refuses answers that do not have six components.
