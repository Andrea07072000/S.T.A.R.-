# star_quantile — median, quantiles, IQR and MAD, correctly rounded

The order statistics that resist outliers: median, any quantile, interquartile range and median absolute deviation,
each computed exactly in rational arithmetic and rounded once. Standard library only.

```python
import star_quantile as sq
sq.median([1, 2, 3, 4, 100])              # 3.0: the outlier does not move it
sq.quantile([1, 2, 3, 4], 0.25)           # 1.75
sq.iqr([1, 1, 2, 2, 4, 6, 9])             # 3.5
sq.mad([1, 1, 2, 2, 4, 6, 9])             # 1.0
```

## Requirements
- R1 `quantile(values, q)` is definition 7 of Hyndman and Fan (linear interpolation between order statistics at
  position (n - 1) q), the default of R and NumPy; `median` is the 0.5 quantile; `iqr` is the 0.75 quantile minus the
  0.25 quantile; `mad` is the median of the absolute deviations from the median, not scaled.
- R2 Each result is the float nearest to the exact value of its definition on the numbers given (q included, as the
  exact value of its float); the order of the values does not matter.
- R3 Measured on 500 datasets of 1 to 60 values (2000 values): every value identical to the exact rational value
  (SymPy) rounded once; NumPy, SciPy and CPython's `statistics` within 7e-16 of the largest |value|.
- R4 Every function returns a float or raises `ValueError`: data that are not a list or tuple of 1 to 100000 finite
  numbers within 1e150 (booleans refused), q outside [0, 1] or not a finite number.

## Evidence
- Published: Hyndman and Fan (1996), definition 7; the worked example of the MAD on (1, 1, 2, 2, 4, 6, 9). Small cases
  by hand.
- `crosscheck_quantile.py`: SymPy (exact rationals), NumPy, SciPy and CPython, each in its own interpreter.

## What is NOT claimed
One quantile definition out of the nine in use: results differ from packages that default to another one, and the
module does not offer the others. The MAD is returned unscaled (multiply by 1.4826 to estimate a Gaussian standard
deviation: that factor is an assumption about the data, not applied here). No weighted quantiles, no confidence
intervals, no streaming estimate. "Exact" refers to the floats supplied.
