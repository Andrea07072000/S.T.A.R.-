# star_sigma — what "n sigma" means in one, two and three dimensions

The probability that a Gaussian error stays within n sigma of the truth depends on how many dimensions the error
has: this module gives it, with its complement and its inverse, for a line, a covariance ellipse and a covariance
ellipsoid. Standard library only.

```python
import star_sigma as ss
ss.sigma_coverage(3.0, 1)        # 0.9973: the usual "3 sigma"
ss.sigma_coverage(3.0, 2)        # 0.9889: inside the 3-sigma ellipse
ss.sigma_coverage(3.0, 3)        # 0.9707: inside the 3-sigma ellipsoid
ss.sigma_for_coverage(0.99, 3)   # 3.368: the ellipsoid that holds 99 %
ss.sigma_tail(5.0, 1)            # 5.73e-07, computed directly
```

## Requirements
- R1 `normal_cdf`, `normal_sf`, `normal_quantile` for the standard normal distribution, accurate in both tails.
  Reproduce the published table values Φ(1), Φ(1.959964), Φ(2.575829).
- R2 `sigma_coverage(n, dims)` and `sigma_tail(n, dims)` for dims 1, 2, 3 (the chi-square law of the squared
  Mahalanobis distance), each computed directly so that neither loses digits; `sigma_for_coverage(p, dims)` is the
  inverse. Reproduce the 68-95-99.7 rule and the published chi-square percentage points for 1, 2 and 3 degrees of freedom.
- R3 Measured on 600 cases (z to ±37, n from 1e-4 to 12, probabilities from 1e-12 to 1 − 1e-12), as RELATIVE
  differences: distribution functions and tails within 1.9e-13 of mpmath at 40 digits and 2.4e-13 of SciPy;
  coverage within 8e-16 of mpmath; the inverses reproduce the requested tail probability within 1.3e-14.
- R4 Every function returns a finite float or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  z beyond ±38, n outside [0, 38], a probability outside the open or half-open interval stated, dims not 1, 2 or 3.

## Evidence
- Published: tables of the normal and chi-square distributions (Abramowitz and Stegun 26.1 and 26.8). Closed forms
  for each dimension evaluated by hand.
- `crosscheck_sigma.py`: SciPy and mpmath (40 digits), each in its own interpreter, each probed on the published table.

## What is NOT claimed
A Gaussian error with a known covariance: real orbit-determination errors are often not Gaussian and the
covariance is often optimistic, so these probabilities are those of the model, not of the truth. No collision
probability: that needs the geometry of the encounter. Dimensions 1, 2 and 3 only. The 1.9e-13 relative error in
the far tails comes from the platform's erfc. A coverage given as 1 − 1e-17 cannot be distinguished from 1: use the
tail.
