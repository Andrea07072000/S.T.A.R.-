"""star_wrap against published values, hand-derivable values, inverses and invariants.

Published: Meeus, Astronomical Algorithms (2nd ed.), Example 25.a:
L0 = -2318.19280 deg -> 201.80720 deg, M = -2241.00603 deg -> 278.99397 deg (wrap360), tol 1e-9 deg.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (the threshold test sat exactly on the threshold)."""
import math
import random


import star_wrap as sw


def circ_dist_deg(a, b):
    return sw.wrap180(a - b)


def test_published_meeus_example_25a_wrap360():
    assert abs(sw.wrap360(-2318.19280) - 201.80720) < 1e-9
    assert abs(sw.wrap360(-2241.00603) - 278.99397) < 1e-9


def test_wrap360_hand_values_edges_and_sign():
    assert sw.wrap360(360) == 0.0
    assert sw.wrap360(-90) == 270.0
    assert sw.wrap360(725) == 5.0
    assert sw.wrap360(-360) == 0.0
    assert sw.wrap360(-1e-20) == 0.0
    x = sw.wrap360(-0.0)
    assert x == 0.0 and math.copysign(1.0, x) == 1.0
    y = sw.wrap360(359.99999999999994)
    assert 0.0 <= y < 360.0 and y == 359.99999999999994


def test_wrap180_hand_values_edges_and_sign():
    assert sw.wrap180(180) == -180.0
    assert sw.wrap180(-180) == -180.0
    assert sw.wrap180(540) == -180.0
    assert sw.wrap180(179.5) == 179.5
    assert sw.wrap180(190) == -170.0
    assert sw.wrap180(-190) == 170.0
    assert sw.wrap180(360) == 0.0
    x = sw.wrap180(-0.0)
    assert x == 0.0 and math.copysign(1.0, x) == 1.0


def test_difference_hand_values_and_half_turn_convention():
    assert sw.difference(10, 350) == 20.0
    assert sw.difference(350, 10) == -20.0
    assert sw.difference(180, 0) == -180.0
    assert sw.difference(0, 180) == -180.0
    assert sw.difference(7, 7) == 0.0
    assert sw.difference(725, 5) == 0.0


def test_large_exact_reductions_and_difference_pre_reduction():
    # 1e9 = 2_777_777 * 360 + 280, so wrap360(1e9)=280 exactly; -1e9 gives 80.
    assert sw.wrap360(1e9) == 280.0
    assert sw.wrap360(-1e9) == 80.0
    # 1e12 = 2_777_777_777 * 360 + 280.
    assert sw.wrap360(1e12) == 280.0
    assert sw.difference(1e9 + 10, 1e9) == 10.0


def test_circular_mean_hand_values_and_known_non_arithmetic_case():
    assert abs(sw.circular_mean([350, 10]) - 0.0) < 1e-12
    assert abs(sw.circular_mean([90]) - 90.0) < 1e-12
    assert abs(sw.circular_mean([0, 90]) - 45.0) < 1e-12
    assert abs(sw.circular_mean([10, 20, 30]) - 20.0) < 1e-12

    # By definition: mean direction = atan2(sum sin, sum cos) in degrees, then wrapped to [0,360).
    vals = [350, 10, 20]
    s = math.sin(math.radians(350)) + math.sin(math.radians(10)) + math.sin(math.radians(20))
    c = math.cos(math.radians(350)) + math.cos(math.radians(10)) + math.cos(math.radians(20))
    expected = sw.wrap360(math.degrees(math.atan2(s, c)))
    got = sw.circular_mean(vals)
    assert abs(circ_dist_deg(got, expected)) < 1e-12
    assert abs(circ_dist_deg(got, (350 + 10 + 20) / 3.0)) > 1.0


def test_circular_mean_invariance_shift_and_permutation_and_tuple():
    base = [350, 10, 20, 30]
    m0 = sw.circular_mean(base)
    m1 = sw.circular_mean([a + 360.0 for a in base])
    m2 = sw.circular_mean([20, 350, 30, 10])
    m3 = sw.circular_mean(tuple(base))
    assert abs(circ_dist_deg(m0, m1)) < 1e-12
    assert abs(circ_dist_deg(m0, m2)) < 1e-12
    assert abs(circ_dist_deg(m0, m3)) < 1e-12


def test_random_inverse_and_range_invariants():
    rnd = random.Random(7)
    for _ in range(300):
        x = rnd.uniform(-1e12, 1e12)
        w360 = sw.wrap360(x)
        w180 = sw.wrap180(x)
        assert 0.0 <= w360 < 360.0
        assert -180.0 <= w180 < 180.0
        assert abs(circ_dist_deg(w180, sw.wrap180(w360))) < 1e-12
        y = rnd.uniform(-1e12, 1e12)
        d = sw.difference(x, y)
        assert -180.0 <= d < 180.0
        assert abs(circ_dist_deg(d, sw.wrap180(sw.wrap360(x) - sw.wrap360(y)))) < 1e-12
