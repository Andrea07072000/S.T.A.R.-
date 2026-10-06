# star_gasdynamics — isentropic flow and normal shock of a perfect gas

The compressible-flow relations a nozzle or an inlet calculation starts from: static-to-stagnation ratios and area
ratio as functions of the Mach number, the Mach number from an area ratio on either branch, and the jump across a
normal shock. Standard library only.

```python
import star_gasdynamics as sg
sg.isentropic(2.0)                       # (0.5556, 0.1278, 0.2300, 1.6875): T/T0, p/p0, rho/rho0, A/A*
sg.mach_from_area_ratio(1.6875)          # 2.0 (supersonic branch);  ..., supersonic=False -> 0.3722
sg.normal_shock(2.0)                     # (0.5774, 4.5, 2.667, 1.6875, 0.7209): M2, p2/p1, rho2/rho1, T2/T1, p02/p01
```

## Requirements
- R1 `isentropic(mach, gamma)`: T/T0, p/p0, rho/rho0 and A/A* of a calorically perfect gas (NACA Report 1135).
  Reproduces the published table for gamma = 1.4 at Mach 0.5, 2, 3 and 5.
- R2 `mach_from_area_ratio(area_ratio, gamma, supersonic)`: the inverse on the branch asked for, by bisection to the
  last bit. `normal_shock(mach1, gamma)`: M2 and the four ratios; reproduces the published table at Mach 2, 3 and 5
  and satisfies the conservation of mass, momentum and energy across the shock.
- R3 Measured on 600 cases (Mach 0.01 to 20, gamma 1.05 to 1.67): T/T0, p/p0, A/A*, M2 and p2/p1 within 1.2e-15
  relative of scikit-aero; the pressure-temperature relation and the sonic ratios within 1.2e-15 of fluids; the Mach
  number from the area ratio within 2e-12 of scikit-aero where its root finder converged to the right branch.
- R4 Every function returns finite floats (A/A* is infinite at Mach 0) or raises `ValueError`: non-numeric,
  boolean, NaN or infinite input, Mach outside [0, 50] (shock: [1, 50]), gamma outside [1.01, 3], an area ratio
  below 1 or beyond the branch, `supersonic` not a bool.

## Evidence
- Published: NACA Report 1135 tables (gamma = 1.4). Exact rational values for gamma = 1.4 and the conservation laws
  across the shock, by hand.
- `crosscheck_gasdynamics.py`: scikit-aero and fluids, each in its own interpreter, each probed on the published
  table first.

## What is NOT claimed
A calorically perfect gas only: no real-gas effects, no dissociation, no variable gamma, so the results are not
valid for hot hypersonic flows whatever the Mach limit accepted. rho2/rho1, T2/T1 and p02/p01 have NO library
lineage: no installed library computes them; they rest on the published table and on the conservation laws.
scikit-aero's inverse of the area ratio did not converge, or converged to the other branch, in about a quarter of
the 600 cases (451 and 460 usable roots per branch): those cases were not compared; recorded as a candidate
observation about a third-party library, not investigated and not reported. No oblique shocks, no Prandtl–Meyer
expansion, no Fanno or Rayleigh flow.
