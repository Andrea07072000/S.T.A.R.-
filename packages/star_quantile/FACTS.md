# Published values the tests of star_quantile may cite (checked by the reviewer against the computation)

1. Hyndman, R. J. and Fan, Y. (1996), "Sample quantiles in statistical packages", The American Statistician 50: definition 7 (the default of R, NumPy and
   spreadsheets): with the n values sorted as x[0..n-1], h = (n - 1) q, result x[floor h] + (h - floor h) (x[floor h + 1] - x[floor h]).
   For the values 1, 2, 3, 4, 5: quantile 0.25 is 2, 0.5 is 3, 0.75 is 4.
2. The usual worked example of the median absolute deviation, data (1, 1, 2, 2, 4, 6, 9): median 2; absolute deviations from it (1, 1, 0, 0, 2, 4, 7), whose
   median is 1: MAD = 1.

Values derivable by hand (write the derivation in a comment). All results are floats; the input need not be sorted:
- median([3, 1, 2]) == 2.0; median([4, 1, 3, 2]) == 2.5 (mean of the two middle values); median([5]) == 5.0; median([1, 2, 3, 4, 100]) == 3.0 (an outlier does not move it);
  median([1e9 + 1, 1e9 + 2]) == 1000000001.5; median([1e150, -1e150]) == 0.0; median equals quantile(values, 0.5) exactly;
- quantile([1, 2, 3, 4], 0.25) == 1.75 [h = 0.75]; quantile([1, 2, 3, 4], 0.75) == 3.25; quantile([10, 20, 30, 40], 0.5) == 25.0; quantile([0, 10], 0.1) == 1.0;
  quantile(v, 0) == min(v) and quantile(v, 1) == max(v) exactly; quantile([5], q) == 5.0 for every q; quantile([1, 3], 0.5) == 2.0;
  quantile is non-decreasing in q; for q = k / (n - 1) it returns the k-th sorted value exactly when that q is an exact float (n = 5: q = 0.25, 0.5, 0.75);
  q is taken as the exact value of its float: quantile([0, 1], 0.1) == 0.1 exactly;
- iqr([1, 2, 3, 4]) == 1.5 [3.25 - 1.75]; iqr([1, 2, 3, 4, 5]) == 2.0; iqr([1, 1, 2, 2, 4, 6, 9]) == 3.5 [quartiles at positions 1.5 and 4.5: 1.5 and 5];
  iqr([7, 7, 7]) == 0.0; iqr([5]) == 0.0; iqr(v) equals the exact difference of the two quartiles rounded once (it may differ in the last digit from
  quantile(v, 0.75) - quantile(v, 0.25) computed in floats);
- mad([1, 1, 2, 2, 4, 6, 9]) == 1.0; mad([1, 2, 3, 4, 5]) == 1.0 [deviations 2, 1, 0, 1, 2]; mad([1, 2, 3, 4, 100]) == 1.0 (the outlier does not move it);
  mad([5]) == 0.0; mad([7, 7, 7]) == 0.0; mad([0, 10]) == 5.0;
- invariances: every function gives the identical float for any permutation of the values; adding a constant c to integer data shifts median and quantile by c and
  leaves iqr and mad unchanged; multiplying by 2 doubles all four; mad and iqr are never negative;
- a tuple and a list give the same result; integers are accepted; zeros are returned as they come from exact arithmetic (median([-0.0, 0.0]) == 0.0).

Limits (state them): BIG == 1e150, MAX_VALUES == 100000. Refusals (ValueError):
- values: an empty list, a string, a generator, a number, None ("must be a list or tuple"); a value that is a bool, a string, None, nan, inf, a complex, or beyond 1e150
  (1.0000001e150; 1e150 accepted) ("finite real numbers");
- quantile: q = -0.1, 1.0000001, nan, inf, a bool, a string, None ("q must be a finite real number from 0 to 1"); q = 0 and q = 1 accepted, also as ints.
Do NOT build lists of 100001 values more than once in the tests (slow): one test for that limit is enough.
