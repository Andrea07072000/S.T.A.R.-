# conjunction-screen-sgp4

Screening of close approaches between objects of TLE catalogues (who to look at), NOT a collision-probability tool.

## Requirements
- R1 `screen(tle_paths, start, hours, step, coarse_km, final_km, cross_only, refine)` returns encounters (TCA in UTC,
  miss distance km, age of the older TLE) below `final_km`, excluding pairs that stay close (formations).
- R2 TLEs are propagated with SGP4 only (mean elements); propagation errors are reported, never replaced.
- R3 `refine_tca(state_at, step)`: closed-form TCA from relative motion, shared by screening and tests.

## How it is verified
Unit tests on real CelesTrak debris TLEs (fixtures, provenance in fixtures/README.md); TCA refinement reproduces the
official CCSDS 508.0-B-1 example 3.6.2 (TCA within 36 us, miss 715.747 m); existing crosscheck (grid vs linear refinement).

## Not supported / not claimed
Probability of collision, covariance, manoeuvre advice, accuracy below the ~1 km TLE error. Advisory screening only.
