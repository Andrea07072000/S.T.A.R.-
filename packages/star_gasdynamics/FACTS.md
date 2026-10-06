# Published values the tests of star_gasdynamics may cite (checked by the reviewer against the computation)

1. NACA Report 1135 ("Equations, Tables, and Charts for Compressible Flow", Ames Research Staff, 1953), tables for gamma = 1.4.
   Isentropic flow (T/T0, p/p0, rho/rho0, A/A*):
     Mach 0.5:  0.9524, 0.8430, 0.8852, 1.340        Mach 2:  0.5556, 0.1278, 0.2300, 1.688
     Mach 3:    0.3571, 0.02722, 0.07623, 4.235      Mach 5:  0.1667, 0.001890, 0.01134, 25.00
   Normal shock (M2, p2/p1, rho2/rho1, T2/T1, p02/p01):
     Mach 2:  0.5774, 4.500, 2.667, 1.687, 0.7209    Mach 3:  0.4752, 10.33, 3.857, 2.679, 0.3283
     Mach 5:  0.4152, 29.00, 5.000, 5.800, 0.06172
   The tables print four significant figures: tolerance 5e-4 RELATIVE for each value.

Exact values for gamma = 1.4 that follow from the formulas (derive them in a comment; they are NOT "published"):
- isentropic: T/T0 = 1 / (1 + M^2 / 5): Mach 2 -> 5/9, Mach 3 -> 5/14, Mach 5 -> 1/6; p/p0 = (T/T0)^3.5; rho/rho0 = (T/T0)^2.5;
  A/A* = (1 / M) ((5 + M^2) / 6)^3: Mach 2 -> 27/16 = 1.6875, Mach 3 -> 343/81, Mach 5 -> 25.0 exactly; Mach 1 -> T/T0 = 5/6, A/A* = 1;
  Mach 0 -> (1, 1, 1, inf);
- normal shock: p2/p1 = (7 M^2 - 1) / 6: 4.5 at Mach 2, 31/3 at Mach 3, 29 at Mach 5; rho2/rho1 = 6 M^2 / (M^2 + 5): 8/3, 27/7, 5;
  M2^2 = (M^2 + 5) / (7 M^2 - 1): 1/3 at Mach 2; T2/T1 = (p2/p1) / (rho2/rho1): 27/16 at Mach 2; Mach 1 -> (1, 1, 1, 1, 1);
  the strong-shock limits: rho2/rho1 -> (gamma + 1) / (gamma - 1) = 6 and M2 -> sqrt((gamma - 1) / (2 gamma)) = 0.37796 (at Mach 50: within 1e-3).

Physics that every result must obey, for ANY gamma in [1.01, 3] (write the checks with the module's outputs only):
- isentropic: rho/rho0 == (p/p0) / (T/T0) and p/p0 == (rho/rho0)^gamma (relative 1e-13); the ratios decrease with Mach; A/A* has its minimum 1 at Mach 1;
- across the shock, with u ~ M sqrt(T) (speed of sound ~ sqrt(T)): mass rho1 u1 = rho2 u2  <=>  M1 = (rho2/rho1) M2 sqrt(T2/T1);
  momentum p1 (1 + gamma M1^2) = p2 (1 + gamma M2^2); energy T1 (1 + (gamma - 1) M1^2 / 2) = T2 (1 + (gamma - 1) M2^2 / 2) (total temperature conserved);
  second law: p02/p01 <= 1 with equality only at Mach 1, and it equals [p2/p1] * [p/p0 at M1] / [p/p0 at M2] computed with isentropic() (relative 1e-12);
  M2 < 1 < M1 for M1 > 1;
- mach_from_area_ratio inverts isentropic on each branch: for M in (1, 50] mach_from_area_ratio(isentropic(M, g)[3], g, True) == M, and for M in
  [1e-6, 1) with supersonic=False (relative 1e-9 away from Mach 1; next to Mach 1 the root is ill-conditioned: at |M - 1| = 1e-3 expect 1e-6);
  mach_from_area_ratio(1.0, g, True) == mach_from_area_ratio(1.0, g, False) == 1.0; the two branches of the same area ratio are different numbers
  (1.6875 -> 2.0 supersonic and 0.37224 subsonic for gamma 1.4).

Constants and limits (state them): MACH_MAX == 50.0, MACH_MIN_SUBSONIC == 1e-6, GAMMA_MIN == 1.01, GAMMA_MAX == 3.0; default gamma 1.4 (isentropic(2.0) ==
isentropic(2.0, 1.4), normal_shock(2.0) == normal_shock(2.0, 1.4), mach_from_area_ratio(1.6875) == mach_from_area_ratio(1.6875, 1.4, True)).
Refusals: Mach < 0 or > 50 (isentropic), < 1 or > 50 (shock: 0.9999999 refused, 1 accepted); gamma 1.0099999 or 3.0000001; area ratio 0.9999999 (below 1),
above the one of Mach 50 on the supersonic branch (use isentropic(50.0, g)[3] * 1.0000001) or above the one of Mach 1e-6 on the
subsonic branch; supersonic given as 1, 0, None or "yes" (must be a bool); booleans, strings, None, NaN, inf, complex, lists as numbers.
