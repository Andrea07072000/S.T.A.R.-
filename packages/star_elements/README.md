# star-elements

Classical orbital elements to and from Cartesian state. Standard library only.

## Requirements
- R1 `rv_to_coe(r, v, mu=398600.4418) -> (h, e, i, raan, argp, nu)` (Curtis Algorithm 4.2); units km, km/s, radians.
- R2 `coe_to_rv(h, e, i, raan, argp, nu, mu) -> (r, v)` (Curtis Algorithm 4.5).
- R3 Singular or invalid cases raise `ValueError`: equatorial (no RAAN), circular (no argp), rectilinear, h <= 0,
  hyperbolic true anomaly beyond the asymptotes. No arbitrary angle is ever returned for an undefined element.

- R4 (0.2.0) Anomalies for 0 <= e < 1: `mean_to_eccentric` (Kepler, Newton; RuntimeError if not converged),
  `eccentric_to_true`, `true_to_eccentric`, `eccentric_to_mean`; e >= 1 raises `ValueError`.

## How it is verified
Curtis Examples 4.3 and 4.7 within half a unit of the printed last digit; 500-case round trip; XC-009 vs hapsira
(poliastro lineage): 5/5 AGREE to 1e-7 deg. Anomalies: Vallado Example 2-1 (E to 1e-9 deg), Curtis Example 3.2, 3000-case round
trips up to e = 0.999, XC-010 vs hapsira 21/21 AGREE.

## Not supported / not claimed
Hyperbolic/parabolic anomalies, equinoctial or other non-singular element sets (needed for equatorial/circular orbits), mean elements, any flight use.
