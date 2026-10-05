# star-maneuver

Impulsive manoeuvre arithmetic between circular coplanar orbits and plane changes. Standard library only.

## Requirements
- R1 `vis_viva(r, a, mu)`; `hohmann(r1, r2, mu)` and `bielliptic(r1, r2, rb, mu)` return per-burn and total delta-v
  (km/s) and time of flight (s). Units: km, s, km/s, km^3/s^2 (default mu = 398600.4418, IERS Conventions 2010).
- R2 `plane_change(v, di)` = 2 v sin(di/2); `combined_dv(v1, v2, di)` by the law of cosines (radians).
- R3 Invalid input fails explicitly with `ValueError` (non-positive radii, rb < max(r1, r2), negative speed).

## How it is verified
Curtis Ex. 6.1 and XC-007 (sympy closed form, hapsira): 5/5 AGREE, re-executed by `star verify`; bi-elliptic crossovers
11.94 / 15.58 reproduced (Vallado sec. 6.3); identity tests; 3/3 hand-made mutants killed.

## Not supported / not claimed
Finite burns, gravity losses, non-coplanar Hohmann with optimal plane-change split, any flight qualification.
