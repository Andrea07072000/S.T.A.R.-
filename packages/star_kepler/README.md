# star_kepler — two-body propagation with universal variables

`propagate(r0, v0, tof, mu=398600.4418) -> (r, v)`: the state after `tof` seconds on the conic defined by `(r0, v0)`.
Standard library only.

## Requirements
- R1 `propagate` returns position and velocity for elliptic and hyperbolic orbits, any consistent units; it reproduces
  Vallado Example 2-4 within the printed precision (1e-3 km, 1e-5 km/s).
- R2 No orbit-geometry singularity: circular and equatorial orbits are propagated like any other; whole periods are
  removed on closed orbits, so a thousand revolutions return the initial state to 1e-4 km.
- R3 Accuracy: on 450 known orbits (eccentricity 0 to 0.95, 0 and 10 revolutions) the error is below 1e-6 km (1 mm) and
  1e-8 km/s; energy and angular momentum are conserved to 1e-9 relative.
- R4 Failure behaviour: non-finite input, zero position, `mu <= 0`, wrong vector length and rectilinear motion raise
  `ValueError` before any iteration; an exhausted iteration budget raises `RuntimeError`; the call cannot loop forever
  (bracketed root, bounded bisection).

## Evidence
- Published reference: Vallado, *Fundamentals of Astrodynamics and Applications*, Example 2-4.
- Independent methods: fixed-step RK4 integration of the equations of motion (in the tests) and, through
  `star_audit.propagation_audit`, hapsira (farnocchia and vallado), Orekit `KeplerianPropagator` and NAIF `prop2b`.
- In that audit (2026-10-06) the maximum position error over the 450 cases is 4.7e-7 km for star_kepler, 4.6e-7 km
  for hapsira farnocchia, 5.0e-7 km for Orekit and 5.1e-7 km for NAIF prop2b.

## What is NOT claimed
Two-body motion only (no perturbations). Parabolic orbits use the same series but are not separately validated.
Rectilinear orbits are refused. No flight heritage.
