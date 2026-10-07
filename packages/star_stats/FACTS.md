# Published values the tests of star_stats may cite (checked by the reviewer against the computation)

1. NIST Statistical Reference Datasets (StRD), univariate summary statistics, dataset NumAcc1: the three values 10000001, 10000003, 10000002:
   certified mean 10000002 and sample standard deviation 1, both exact. mean == 10000002.0 and stdev == 1.0 exactly.
2. NIST StRD, dataset NumAcc2: 1.2 followed by 500 pairs (1.1, 1.3), 1001 values: certified mean 1.2 and sample standard deviation 0.1.
   mean([1.2] + [1.1, 1.3] * 500) == 1.2 exactly; stdev within 1e-15 of 0.1 (it is 0.09999999999999998: the floats 1.1 and 1.3 are not the decimals 1.1 and 1.3,
   and the module returns the exact statistic of the floats given).
3. The textbook example of the population standard deviation (2, 4, 4, 4, 5, 5, 7, 9): mean 5, population variance 4, population standard deviation 2 exactly;
   sample variance 32/7.

Values derivable by hand (write the derivation in a comment). All results are floats:
- mean([1, 2, 3, 4]) == 2.5; variance([1, 2, 3, 4]) == 5/3 (sum of squares of deviations 5, divided by 3) to the last digit: == 1.6666666666666667;
  variance([1, 2, 3, 4], False) == 1.25; stdev([1, 2, 3, 4], False) == math.sqrt(1.25) exactly; stdev([1, 2, 3, 4]) == math.sqrt(5/3) within 2.3e-16;
  the default is the SAMPLE statistic: variance(x) == variance(x, True) != variance(x, False);
- one value: mean([7]) == 7.0, variance([7], False) == 0.0, stdev([7], False) == 0.0, rms([-5]) == 5.0;
- no cancellation: variance([1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]) == 30.0 exactly and population variance 22.5 exactly (deviations -6, -3, 3, 6 from the mean 1e9 + 10);
  variance([0.1] * 7) == 0.0 exactly (equal values); mean([1e16, 1, -1e16]) == 1/3 to the last digit (0.3333333333333333), where summing the floats in order gives 0;
  mean([0.1, 0.2, 0.3]) == 0.2 exactly (the float sum gives 0.20000000000000004);
- the order of the values does not matter: any permutation gives the identical float, for every function;
- rms([3, 4]) == math.sqrt(12.5) exactly; rms([1, -1, 1, -1]) == 1.0; rms([0, 0]) == 0.0; rms([5e-324]) == 5e-324 and rms([1e150] * 3) == 1e150 (no underflow or
  overflow of the squares); stdev([5e-324, 0.0]) == 5e-324;
- relations: stdev(x, s) ** 2 equals variance(x, s) within 4e-16 relative; rms(x)**2 == variance(x, False) + mean(x)**2 within 1e-12 for values of order 1;
  variance(x) * (n - 1) == variance(x, False) * n within 4e-16 relative; adding a constant to every value leaves the variance of small integers unchanged exactly;
- weighted_mean([10, 20], [1, 3]) == 17.5; weighted_mean([10, 20], [0, 3]) == 20.0 (a zero weight removes the value); equal weights give the mean exactly:
  weighted_mean(x, [2.5] * n) == mean(x); weighted_mean([1, 2, 3], [1, 1, 2]) == 2.25; scaling all the weights by a power of two changes nothing;
- zeros are +0.0: mean([-0.0, 0.0]), mean([-0.0]), weighted_mean([-0.0], [2]) all have math.copysign(1.0, r) == 1.0;
- a tuple and a list give the same result; integers are accepted.

Limits (state them): BIG == 1e150, MAX_VALUES == 100000. Refusals (ValueError):
- values: an empty list, a string, a generator, a number, None ("must be a list or tuple"); a value that is a bool, a string, None, nan, inf, a complex, or beyond 1e150
  (1.0000001e150; 1e150 itself accepted: mean([1e150, 1e150]) == 1e150) ("finite real numbers");
- variance and stdev with sample=True (the default) and one value ("at least 2 values"); sample that is not a bool: 1, 0, None, "yes" ("sample must be True or False");
- weighted_mean: weights of another length ("as many"), a negative weight ("must not be negative"), all zero ("must not be all zero"), a weight that is nan, inf, a bool,
  a string ("weights must be finite real numbers"), weights that are not a list or tuple ("weights must be a list or tuple").
Do NOT build a list of 100001 values more than once in the tests (it is slow): one test for the limit is enough ([0.0] * 100001 refused, [0.0] * 100000 accepted by mean).
