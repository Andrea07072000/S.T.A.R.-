# Published values the tests of star_doppler may cite (checked by the reviewer against the computation)

1. Speed of light in vacuum: 299 792 458 m/s exactly (SI definition, 17th CGPM 1983). C_KM_S == 299792.458.
2. The longitudinal relativistic Doppler factor for a source receding at v = b c is sqrt((1 - b) / (1 + b)) (any text on special relativity);
   the first-order ("radio") convention used in link budgets is 1 - b.

Values derivable by hand (write the derivation in a comment; compare within 1e-12 unless stated). All results are floats:
- range_and_rate(r_observer, v_observer, r_target, v_target) returns (range, range_rate):
  range_and_rate((0, 0, 0), (0, 0, 0), (3, 4, 0), (1, 0, 0)) == (5.0, 0.6) [line of sight (0.6, 0.8, 0); 0.6 * 1];
  range_and_rate((0, 0, 0), (0, 0, 0), (10, 0, 0), (0, 5, 0)) == (10.0, 0.0) (velocity across the line of sight);
  range_and_rate((0, 0, 0), (0, 0, 0), (0, 0, 7), (0, 0, -2)) == (7.0, -2.0) (approaching: a negative rate);
  range_and_rate((0, 0, 0), (0, 0, 0), (0, 0, 7), (0, 0, 2)) == (7.0, 2.0) (receding);
  equal velocities give a zero rate: range_and_rate((1, 2, 3), (0.1, 0.2, 0.3), (4, 6, 3), (0.1, 0.2, 0.3)) == (5.0, 0.0);
  only the differences matter: adding the same vector to both positions, or the same vector to both velocities, changes nothing (within 1e-12 for numbers of order 1);
  exchanging observer and target gives the same range and the same rate (the distance between two points changes at one rate);
  the observer's own velocity counts: range_and_rate((0, 0, 0), (1, 0, 0), (10, 0, 0), (0, 0, 0)) == (10.0, -1.0) (the observer moves towards the target);
  |range_rate| <= |v_target - v_observer| always, with equality when the relative velocity is along the line of sight;
  no overflow at the limit: range_and_rate((-1e15, 0, 0), (0, 0, 0), (1e15, 0, 0), (1e15, 0, 0)) == (2e15, 1e15);
- received_frequency(frequency, range_rate, relativistic=True): received_frequency(1000.0, 0.6 * C_KM_S) == 500.0 [sqrt(0.4 / 1.6) = 0.5];
  received_frequency(1000.0, -0.6 * C_KM_S) == 2000.0 (approaching: sqrt(1.6 / 0.4) = 2); received_frequency(1000.0, 0.6 * C_KM_S, False) == 400.0;
  received_frequency(1000.0, -0.6 * C_KM_S, False) == 1600.0; received_frequency(f, 0) == f and received_frequency(f, 0, False) == f exactly;
  a positive range rate lowers the frequency, a negative one raises it; the product received_frequency(f, v) * received_frequency(f, -v) == f * f (relativistic, within 1e-12);
  at 7.5 km/s on 2.2e9 Hz: relativistic 2199944962.6127 Hz, first order 2199944961.9243 Hz (within 1e-3 Hz): they differ by 0.69 Hz, that is f b^2 / 2;
  the first-order shift is exactly linear: received_frequency(f, v, False) == f * (1 - v / C_KM_S);
- the two functions chain: for a target receding along the line of sight at 3 km/s, received_frequency(f, range_and_rate(...)[1]) == received_frequency(f, 3.0).

Limits (state them): BIG == 1e15, MAX_FREQUENCY == 1e30. Refusals (ValueError):
- range_and_rate: a vector that is not a list or tuple of exactly 3 numbers ((1, 2), a string, None: "must be a list or tuple of 3 numbers"); a component that is a bool, a
  string, None, nan, inf, a complex, or beyond 1e15 ("a component of r_observer", "... v_observer", "... r_target", "... v_target"); the same position for observer and
  target ("coincide");
- received_frequency: frequency 0, negative, nan, inf, a bool, a string, None, or beyond 1e30 (1e30 accepted) ("frequency"); range_rate nan, inf, a bool, a string, None
  ("range_rate"); |range_rate| >= C_KM_S: exactly C_KM_S, -C_KM_S, 3e5 ("smaller than the speed of light"; 299792.457 is accepted);
  relativistic that is 0, 1, None, "yes" ("relativistic must be True or False").
