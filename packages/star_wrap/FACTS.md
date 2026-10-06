# Published values the tests of star_wrap may cite (checked by the reviewer against the computation)

1. Meeus, Astronomical Algorithms (2nd ed.), Example 25.a (the Sun on 1992 October 13): the mean longitude
   L0 = -2318.19280 deg reduces to 201.80720 deg and the mean anomaly M = -2241.00603 deg reduces to 278.99397 deg.
   wrap360 of each must equal the reduced value within 1e-9 deg.

Behaviour of the module (state it; derive the values by hand in a comment; do not call them published):
- wrap360 returns [0, 360): wrap360(360) == 0.0, wrap360(-90) == 270.0, wrap360(725) == 5.0, wrap360(-360) == 0.0, wrap360(-0.0) == 0.0 with a positive sign
  (math.copysign(1, wrap360(-0.0)) == 1.0), wrap360(-1e-20) == 0.0 (never 360.0), wrap360(359.99999999999994) stays below 360;
- wrap180 returns [-180, 180): wrap180(180) == -180.0, wrap180(-180) == -180.0, wrap180(540) == -180.0, wrap180(179.5) == 179.5, wrap180(190) == -170.0,
  wrap180(-190) == 170.0, wrap180(360) == 0.0, wrap180(-0.0) == 0.0 with a positive sign;
- difference(a, b) is a - b as the shortest signed rotation in [-180, 180): difference(10, 350) == 20.0, difference(350, 10) == -20.0,
  difference(180, 0) == -180.0, difference(0, 180) == -180.0, difference(7, 7) == 0.0, difference(725, 5) == 0.0;
  difference(1e9 + 10, 1e9) == 10.0 exactly (each angle is reduced first: 1e9 = 2777777 * 360 + 280);
- the reduction is exact: wrap360(1e9) == 280.0, wrap360(-1e9) == 80.0, wrap360(1e12) == 280.0 (1e12 = 2777777777 * 360 + 280);
- circular_mean: circular_mean([350, 10]) == 0.0 within 1e-12 (as a circular distance: 0 and 360 are the same direction, the result must be in [0, 360));
  circular_mean([90]) == 90.0 within 1e-12; circular_mean([0, 90]) == 45.0 within 1e-12; circular_mean([10, 20, 30]) == 20.0 within 1e-12;
  circular_mean([350, 10, 20]) == degrees(atan2(sin350+sin10+sin20, cos350+cos10+cos20)) = 6.704953... (NOT the arithmetic mean 126.67);
  adding 360 to any element or shuffling the order does not change the mean; a tuple is accepted as well as a list;
- circular_mean refuses (ValueError) when the unit vectors cancel: [0, 180], [0, 120, 240], [10, 190]; and an empty list, a string, a set, a generator,
  a dict, a number, a list holding one hostile value;
- limits: angles within [-1e12, 1e12] accepted, 1.0000001e12 refused; LIMIT == 1e12, MIN_RESULTANT == 1e-9, MAX_ITEMS == 1000000.
