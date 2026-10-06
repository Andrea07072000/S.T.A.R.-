# star_atmosphere — U.S. Standard Atmosphere 1976 (below 86 km)

Temperature, pressure, density and speed of sound at a geometric altitude. Standard library only.

```python
import star_atmosphere
T, P, rho, a = star_atmosphere.ussa1976(11000.0)      # K, Pa, kg/m3, m/s at 11 km geometric altitude
```

## Requirements
- R1 `ussa1976(z_m)`: the seven-layer model of "U.S. Standard Atmosphere, 1976" with the constants of the standard
  (R* = 8.31432 J/(mol K)). Reproduces the published base pressure of every layer within 2e-7 and eight rows of the
  main table to the printed digits (0.001 K; one unit in the fifth digit of pressure and density).
- R2 `geopotential_m(z)` / `geometric_m(h)`: the standard's conversion with r0 = 6 356 766 m; the input of `ussa1976`
  is GEOMETRIC altitude (the usual source of 0.3 % errors at 20 km is passing one for the other).
- R3 Measured against two independent implementations on 308 altitudes: fluids within 4e-15 relative; hapsira COESA76
  within 3e-16 in temperature and 5.7e-5 in pressure and density (its table of base pressures is rounded to 4-5
  digits: verified in its data file).
- R4 Valid from -5000 m to 86 000 m geometric. Outside, and for non-numeric, boolean, NaN or infinite input:
  `ValueError`. Nothing is extrapolated.

## Evidence
- Published: layer bases and main-table rows of the 1976 standard (tests).
- `crosscheck_atmosphere.py`: fluids and hapsira, each in its own interpreter, first probed on published values.
- Ideal-gas law, hydrostatic balance (numerical derivative against rho*g) and continuity at the layer boundaries.

## What is NOT claimed
A standard atmosphere, not the weather: real density at a given place and day differs by tens of percent. Above 86 km
the standard uses a different formulation, not implemented here. Above 80 km the temperature returned is the
molecular-scale temperature (0.04 % above the kinetic temperature at 86 km); see the module docstring.
