# Published values the tests of star_sigma may cite (checked by the reviewer against the computation)

1. Tables of the normal distribution (e.g. Abramowitz and Stegun, Handbook of Mathematical Functions, table 26.1):
   Phi(1) = 0.8413447, Phi(1.959964) = 0.975000, Phi(2.575829) = 0.995000; the two-sided coverage of 1, 2 and 3 sigma is
   0.6826895, 0.9544997, 0.9973002 (the "68-95-99.7 rule"); tolerance 5e-7.
2. Chi-square percentage points (Abramowitz and Stegun, table 26.8): the 95 % point is 3.841 for 1 degree of freedom, 5.991 for 2
   and 7.815 for 3; the 99 % point is 6.635, 9.210 and 11.345. So sigma_for_coverage(0.95, d) ** 2 and sigma_for_coverage(0.99, d) ** 2
   must equal those within 5e-4.

Closed forms that the tests can evaluate themselves with the math module (derive them in a comment; they are not "published"):
- dims 1: coverage = erf(n / sqrt 2); tail = erfc(n / sqrt 2); normal_cdf(z) = erfc(-z / sqrt 2) / 2; normal_sf(z) = normal_cdf(-z);
- dims 2: coverage = 1 - exp(-n^2 / 2) (1 sigma: 0.39346934, 2 sigma: 0.86466472, 3 sigma: 0.98889100); tail = exp(-n^2 / 2);
  sigma_for_coverage(p, 2) = sqrt(-2 ln(1 - p)) (e.g. p = 0.5 gives 1.1774100225154747);
- dims 3: coverage = erf(n / sqrt 2) - sqrt(2 / pi) n exp(-n^2 / 2) (1 sigma: 0.19874804, 2 sigma: 0.73853587, 3 sigma: 0.97070911);
  tail = erfc(n / sqrt 2) + sqrt(2 / pi) n exp(-n^2 / 2); for small n the coverage behaves as sqrt(2 / pi) n^3 / 3 (leading term), e.g.
  sigma_coverage(1e-3, 3) = 2.6596e-10 within 1e-13 absolute, and the series and the closed form must join smoothly at n = 1
  (sigma_coverage(1 - 1e-9, 3) and sigma_coverage(1, 3) differ by less than 1e-9; the function is increasing across n = 1).

Properties to check with the module's outputs only:
- coverage + tail == 1 within 4e-16 for every n and every dims; both are monotonic in n; coverage(0) == 0 and tail(0) == 1 exactly;
- for the same n the coverage DEcreases with the number of dimensions: coverage(n, 1) > coverage(n, 2) > coverage(n, 3) for n > 0;
- normal_cdf(z) + normal_sf(z) == 1 within 4e-16; normal_cdf(-z) == normal_sf(z) exactly; normal_cdf(0) == 0.5; normal_quantile(0.5) == 0.0;
  normal_quantile(1 - p) == -normal_quantile(p) (within 1e-9 for p = 0.1, 0.01, 1e-6); sigma_coverage(n, 1) == normal_cdf(n) - normal_cdf(-n) within 4e-16;
- the tails keep their digits: sigma_tail(5, 1) = 5.733031437583878e-07 and normal_sf(5) is half of it (relative 1e-12); sigma_tail(10, 2) == exp(-50) exactly as computed
  by math.exp(-50.0); normal_sf(37) is about 5.7e-300 and positive; normal_quantile(1e-300) is about -37.047 (within 1e-3);
- inverses: normal_cdf(normal_quantile(p)) == p within 1e-12 relative for p from 1e-12 to 0.5, and normal_sf(normal_quantile(p)) == 1 - p for p above 0.5;
  sigma_tail(sigma_for_coverage(p, d), d) == 1 - p within 1e-12 relative for p above 0.5; sigma_coverage(sigma_for_coverage(p, d), d) == p for p up to 0.5;
  sigma_for_coverage(0, d) == 0.0 for every d;
- defaults: sigma_coverage(n) == sigma_coverage(n, 1), sigma_tail(n) == sigma_tail(n, 1), sigma_for_coverage(p) == sigma_for_coverage(p, 1).

Constants and limits (state them): Z_MAX == 38.0; SERIES_BELOW == 1.0.
Refusals: z beyond +-38 (38 accepted, 38.0000001 refused); n_sigma negative (-1e-12) or above 38; normal_quantile at 0, 1, -0.1, 1.1 (the interval is open);
sigma_for_coverage at 1 or above and below 0 (0 is accepted); dims 0, 4, 2.0, "2", None, True (True is not the integer 1 here); booleans, strings, None, NaN, inf,
complex and lists as numbers.
