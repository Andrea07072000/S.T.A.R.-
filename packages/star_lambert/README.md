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
Multi-revolution transfers; transfer angles of exactly 0 or 180 deg; any statement of flight qualification.
