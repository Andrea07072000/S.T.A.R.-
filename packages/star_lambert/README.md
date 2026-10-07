# star-lambert

Zero-revolution solver for Lambert's problem (universal variables, Stumpff functions, Newton on z; Bate-Mueller-White /
Curtis Algorithm 5.2). Standard library only.

## Requirements (what it must do)
- R1 `lambert(r1, r2, tof, mu=398600.4418, prograde=True) -> (v1, v2)`: velocities at r1 and r2 for a transfer of
  duration `tof`. Units: km, s, km/s, km^3/s^2.
- R2 Never return an unconverged result: `RuntimeError` instead.
- R3 Invalid input fails explicitly: `ValueError` for tof <= 0, zero position vectors, degenerate geometry (0 or 180 deg).

## How it is verified
Curtis Example 5.2 within printed precision; propagating v1 reaches r2; XC-006 cross-check against Izzo's algorithm
(hapsira, different lineage): 21/21 AGREE; re-executed by `star verify` with identical bundle hashes.

## Not supported / not claimed
Multi-revolution transfers; transfer angles within 1e-8 rad of 0 or 180 deg (refused: the transfer plane is not defined); any statement of flight qualification.

## Changes
- 0.1.3 (2026-10-07): positions exactly opposite each other could differ from 180 degrees by 1.5e-8 rad after rounding, pass the degeneracy check and return
  velocities in a plane chosen by rounding noise (85 of 399 opposite pairs in the new test). The transfer angle is now computed from the cross and the dot product and such
  pairs are always refused. Results for valid transfers are unchanged within the tolerance of the existing tests. Found while adding guard tests after a corrected
  mutation measurement (0.84 on 0.1.2).
