# star_j2 — what the Earth's oblateness does to an orbit, on average

First-order secular rates in J2: node regression, perigee rotation, mean-anomaly rate, nodal period, the
sun-synchronous inclination and the critical inclination. Standard library only.

```python
import star_j2
star_j2.raan_rate_deg_day(6778.137, 0.0, 51.6)          # about -5.0 deg/day (ISS-like orbit)
star_j2.sun_synchronous_inclination_deg(6378.137 + 800)  # about 98.6 deg
```

## Requirements
- R1 `raan_rate_deg_day`, `argp_rate_deg_day`, `mean_anomaly_rate_deg_day`, `nodal_period_s` for mean elements
  (a in km, e, inclination in degrees), EGM96/WGS-84 constants by default, overridable by keyword.
- R2 `sun_synchronous_inclination_deg(a_km, e=0)`: the inclination whose node advances 360 degrees per tropical year;
  `CRITICAL_INCLINATION_DEG` = 63.4349...: the perigee does not rotate.
- R3 Accuracy, measured on 51 orbits: node rate within 0.31 % of Orekit's Eckstein-Hechler theory (J2 only, mean
  elements) and within 0.38 % of a numerical integration of the equations of motion with J2; perigee rate within
  0.013 deg/day of the numerical integration. The formulas are first order in J2: differences of this size are the
  model, not a rounding error.
- R4 Every function returns a finite float or raises `ValueError`: non-numeric, boolean, NaN or infinite input;
  a <= 0; e outside [0, 1); inclination outside [0, 180]; perigee inside the Earth; non-positive mu, re or j2; an
  orbit too high to be sun-synchronous (above about 12 350 km semi-major axis for a circular orbit).

## Evidence
- Textbook figures: critical inclination, ISS node regression of about 5 deg/day, 98.6 deg at 800 km, 97.4 deg at 500 km.
- Exact identities of the formulas (signs, symmetries, scaling with a, e, mu, J2).
- A fixed-step RK4 integration of the J2 equations of motion in the tests (no secular formula involved).
- `crosscheck_j2.py`: Orekit and SciPy DOP853, each in its own interpreter, first probed on the ISS-like orbit.

## What is NOT claimed
Mean rates only: no short-period terms, no J2-squared, J3 or higher harmonics, no drag, no third bodies. Not a
propagator. For mission design at the 0.5 % level; a station-keeping budget needs a full theory or an integration.
