# star_twobody — the sizes and speeds of a Keplerian ellipse

Period, mean motion, circular and escape speed, apsis radii and speeds, specific energy: the quantities that follow
from the semi-major axis, the eccentricity and the gravitational parameter of a two-body orbit.
Standard library only.

```python
import star_twobody as tb
tb.period(42164.17)                          # 86164.09 s: the geostationary orbit, one sidereal day
tb.semi_major_axis_from_period(86164.0905)   # 42164.17 km
tb.apsides(10000.0, 0.2)                     # (8000.0, 12000.0) km
tb.apsis_speeds(10000.0, 0.2)                # (7.7324, 5.1549) km/s
tb.escape_speed(6378.137)                    # 11.180 km/s at the Earth's equatorial radius
```

## Requirements
- R1 `period`, `semi_major_axis_from_period`, `mean_motion`: Kepler's third law, for the Earth by default or any mu.
  Reproduce the geostationary orbit (one sidereal day at 42164.17 km).
- R2 `circular_speed`, `escape_speed`, `apsides`, `elements_from_apsides`, `apsis_speeds`, `specific_energy`, consistent
  with each other: angular momentum and energy are the same at the two apsides.
- R3 Measured on 600 orbits (a 6600 to 400000 km, e 0 to 0.95, 100 circular): within 4e-14 relative of SPICE for a
  gravitational parameter from the Moon's to the Sun's, and within 2.6e-14 of hapsira on the Earth.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input, a
  length, period or mu outside [1e-30, 1e30] (zero and negative values included), an eccentricity outside [0, 1), an apoapsis
  below the periapsis by more than rounding.

## Evidence
- Published: the geostationary orbit and the Earth's gravitational parameter. Kepler's third law in canonical units,
  conservation of angular momentum and of energy between the apsides, by hand.
- `crosscheck_twobody.py`: SPICE and hapsira, each in its own interpreter, each probed on the geostationary period.

## What is NOT claimed
Two-body motion only: the real period of a low orbit differs by seconds because of the Earth's oblateness (see
`star_j2` for the nodal period). Ellipses only: no parabolic or hyperbolic orbits. No position along the orbit (see
`star_kepler`) and no manoeuvres (see `star_maneuver`). The result is as good as the mu supplied.
