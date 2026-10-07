# star_anomaly — mean, eccentric, hyperbolic and true anomaly

Kepler's equation and the conversions between the anomalies of an orbit, for closed and for open orbits, accurate up
to nearly parabolic eccentricities. Standard library only.

```python
import math
import star_anomaly as sa
math.degrees(sa.eccentric_from_mean(math.radians(235.4), 0.4))   # 220.512074767522
sa.hyperbolic_from_mean(math.radians(235.4), 2.4)                 # 1.6013761449...
sa.true_from_mean(1.0, 0.5)                                       # 2.0308...
sa.mean_from_true(2.030806214849156, 0.5)                         # 1.0
```

## Requirements
- R1 Closed orbits (0 <= e < 1): `eccentric_from_mean`, `mean_from_eccentric`, `true_from_eccentric`,
  `eccentric_from_true`, `true_from_mean`, `mean_from_true`. Open orbits (e > 1): `hyperbolic_from_mean`,
  `mean_from_hyperbolic`, `true_from_hyperbolic`, `hyperbolic_from_true`. Angles in radians.
- R2 The closed-orbit functions keep the revolution (nothing is wrapped). Kepler's equation is solved by Newton's
  method inside a bracket that always contains the root, with the residual written so that it does not cancel near
  the periapsis of a nearly parabolic orbit; the true anomaly comes from a form with no quadrant to choose.
- R3 Measured on 1120 orbits (620 closed, 500 open, a fifth of them nearly parabolic) and two published examples,
  four conversions each: within 1e-14 rad of 50-digit arithmetic on every case; within 2e-14 rad of hapsira and
  Orekit on the ordinary orbits (the nearly parabolic ones are reported apart in the evidence file).
- R4 Every function returns a float or raises `ValueError`: values that are not finite real numbers, an
  eccentricity on the wrong side of 1 for the function called, an angle beyond 1e9 rad, a true anomaly at or beyond
  the asymptote of an open orbit, a result too large for a float.

## Evidence
- Published: Vallado's two worked examples of Kepler's equation (ellipse and hyperbola).
- `crosscheck_anomaly.py`: 50-digit arithmetic, hapsira (its own interpreter) and Orekit (Java).

## What is NOT claimed
The parabola (e exactly 1) is not covered: use Barker's equation elsewhere. Some conversions are badly conditioned
by nature and no code can repair that: near a parabola, the eccentric anomaly recovered from a true anomaly close
to 180 degrees, and the hyperbolic anomaly recovered from a true anomaly close to the asymptote, hold fewer digits
than the input (the function is accurate for the float it is given; the float does not hold the information).
The 50-digit reference uses other formulas than the module's but was written by the same author. No propagation in
time: converting a time to a mean anomaly is one multiplication, left to the caller.
