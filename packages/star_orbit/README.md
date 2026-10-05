# star-orbit

Cowell numerical orbit propagation (fixed-step RK4) with two-body + J2 gravity, federated with star-timescales for epochs.

## Requirements
- R1 `propagate_orbit(OrbitState, duration_sec, step_sec, include_j2=True, ...) -> list[OrbitState]`, SI units (m, s, m/s),
  mu = 3.986004418e14 m^3/s^2, Re = 6378137 m, J2 = 1.08262668e-3 (WGS-84 / EGM96).
- R2 Requesting a force that is not available (drag/SRP without star-weather) raises `RuntimeError`; a force is never
  silently dropped.
- Dependency: star-timescales >= 0.2.0 (declared). Drag and SRP need star-weather, which is NOT packaged yet: they are
  not part of this release.

## How it is verified
J2 secular rates vs analytic theory; XC-008 three engines (star_orbit RK4, SciPy DOP853, hapsira J2_perturbation)
4/4 AGREE within 5 cm; re-executed by `star verify`.

## Not supported / not claimed
Drag/SRP in the released package, higher-order geopotential, third bodies, published reference trajectory comparison,
any operational or flight use.
