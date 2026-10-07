# star_stats — summary statistics, correctly rounded

Mean, variance, standard deviation, root mean square and weighted mean, each computed exactly in rational arithmetic
and rounded once. Standard library only.

```python
import star_stats as st
st.variance([1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16])   # 30.0, exactly (the one-pass textbook formula cancels here)
st.mean([1e16, 1, -1e16])                             # 0.3333333333333333 (summing the floats in order gives 0.0)
st.stdev([2, 4, 4, 4, 5, 5, 7, 9], sample=False)      # 2.0
st.weighted_mean([10, 20], [1, 3])                    # 17.5
```

## Requirements
- R1 `mean`, `variance`, `stdev`, `rms` and `weighted_mean` return the float nearest to the exact value of their
  formula applied to the numbers given (a float is an exact fraction). The result does not depend on the order of
  the values.
- R2 `variance` and `stdev` are the sample statistics (divisor n - 1) by default and the population statistics with
  `sample=False`. Square roots are rounded correctly from the exact fraction, with no underflow or overflow of the
  squares.
- R3 Measured on 500 datasets of 2 to 60 values (mixed magnitudes, large offsets, equal values, integers): all seven
  statistics are identical to mpmath at 400 digits rounded once, and to CPython's `statistics` module where it has
  them; NumPy and SciPy differ by at most 5e-16 of the natural scale, which is their own rounding.
- R4 Every function returns a float or raises `ValueError`: data that are not a list or tuple of 1 to 100000 finite
  numbers within 1e150 (booleans refused), a sample statistic of a single value, a `sample` that is not a bool,
  weights that are negative, all zero, not finite or of another length.

## Evidence
- Published: NIST Statistical Reference Datasets NumAcc1 and NumAcc2 (mean and standard deviation); the textbook
  example 2, 4, 4, 4, 5, 5, 7, 9. Small cases by hand.
- `crosscheck_stats.py`: mpmath, CPython `statistics`, NumPy and SciPy, each in its own interpreter.

## What is NOT claimed
"Exact" refers to the floats supplied: 0.1 is not one tenth, and the statistics of measurements carry the error of
the measurements, which no arithmetic removes. On Python 3.12 the standard `statistics` module returns the same
mean, variance and standard deviation: this package adds the root mean square, the exact weighted mean, the stated
limits and refusals, and the independent check. Exact arithmetic is slower than floating point (about one second
for 100000 values): it is for results that must not depend on rounding, not for large arrays. No medians,
quantiles, covariance, regression or uncertainty of the estimates.
