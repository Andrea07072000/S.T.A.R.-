"""star_anomaly against published values, hand-derivable values, inverses and invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math
import random

import pytest

import star_anomaly as sa


def test_published_vallado_values():
    e = sa.eccentric_from_mean(math.radians(235.4), 0.4)
    assert abs(math.degrees(e) - 220.512074767522) < 1e-11
    h = sa.hyperbolic_from_mean(math.radians(235.4), 2.4)
    assert abs(h - 1.6013761449) < 1e-10


def test_hand_derivable_kepler_equations():
    # mean_from_eccentric(E,e) = E - e sin(E). With E=pi/2,e=0.5: M = pi/2 - 0.5 exactly from sin(pi/2)=1.
    assert sa.mean_from_eccentric(math.pi / 2, 0.5) == pytest.approx(math.pi / 2 - 0.5, abs=1e-15)
    # E=1.2,e=0.3: M = 1.2 - 0.3*sin(1.2) = 0.9203882742098322
    assert sa.mean_from_eccentric(1.2, 0.3) == pytest.approx(0.9203882742098322, abs=1e-15)
    # mean_from_hyperbolic(F,e)=e sinh(F)-F. With F=1,e=2: 2*sinh(1)-1=1.3504023872876028
    assert sa.mean_from_hyperbolic(1.0, 2.0) == pytest.approx(1.3504023872876028, abs=1e-15)


def test_circular_fixed_points_and_special_values():
    x = 1.23456789
    assert sa.eccentric_from_mean(x, 0.0) == x
    assert sa.mean_from_eccentric(x, 0.0) == x
    assert sa.true_from_eccentric(x, 0.0) == x
    assert sa.eccentric_from_true(x, 0.0) == x
    assert sa.true_from_mean(x, 0.0) == x
    assert sa.mean_from_true(x, 0.0) == x
    for e in (0.0, 0.3, 0.9, 2.0):
        assert sa.eccentric_from_mean(0.0, min(e, 0.99)) == 0.0
        assert sa.mean_from_eccentric(0.0, min(e, 0.99)) == 0.0
        assert sa.true_from_eccentric(0.0, min(e, 0.99)) == 0.0
        assert sa.eccentric_from_true(0.0, min(e, 0.99)) == 0.0
        if e < 1:
            assert sa.true_from_mean(0.0, e) == 0.0
            assert sa.mean_from_true(0.0, e) == 0.0
        else:
            assert sa.hyperbolic_from_mean(0.0, e) == 0.0
            assert sa.mean_from_hyperbolic(0.0, e) == 0.0
            assert sa.true_from_hyperbolic(0.0, e) == 0.0
            assert sa.hyperbolic_from_true(0.0, e) == 0.0
    for e in (0.2, 0.9):
        assert sa.eccentric_from_mean(math.pi, e) == pytest.approx(math.pi, abs=5e-16)
        assert sa.true_from_eccentric(math.pi, e) == pytest.approx(math.pi, abs=5e-16)
        assert sa.eccentric_from_mean(-math.pi, e) == pytest.approx(-math.pi, abs=5e-16)
        assert sa.true_from_eccentric(-math.pi, e) == pytest.approx(-math.pi, abs=5e-16)


def test_oddness_all_ten_functions():
    e0, e1 = 0.63, 2.4
    x0, x1 = 1.1, 1.3
    assert sa.eccentric_from_mean(-x0, e0) == pytest.approx(-sa.eccentric_from_mean(x0, e0), abs=1e-14)
    assert sa.mean_from_eccentric(-x0, e0) == -sa.mean_from_eccentric(x0, e0)
    assert sa.true_from_eccentric(-x0, e0) == pytest.approx(-sa.true_from_eccentric(x0, e0), abs=1e-14)
    assert sa.eccentric_from_true(-x0, e0) == pytest.approx(-sa.eccentric_from_true(x0, e0), abs=1e-14)
    assert sa.true_from_mean(-x0, e0) == pytest.approx(-sa.true_from_mean(x0, e0), abs=1e-14)
    assert sa.mean_from_true(-x0, e0) == pytest.approx(-sa.mean_from_true(x0, e0), abs=1e-14)
    assert sa.hyperbolic_from_mean(-x1, e1) == pytest.approx(-sa.hyperbolic_from_mean(x1, e1), abs=1e-14)
    assert sa.mean_from_hyperbolic(-x1, e1) == pytest.approx(-sa.mean_from_hyperbolic(x1, e1), abs=1e-14)
    assert sa.true_from_hyperbolic(-x1, e1) == pytest.approx(-sa.true_from_hyperbolic(x1, e1), abs=1e-14)
    assert sa.hyperbolic_from_true(-1.0, e1) == pytest.approx(-sa.hyperbolic_from_true(1.0, e1), abs=1e-14)


def test_revolution_kept_and_bounds():
    e, m = 0.6, 1.234
    base = sa.eccentric_from_mean(m, e)
    for k in (7, -3, 1000):
        got = sa.eccentric_from_mean(m + 2 * math.pi * k, e)
        assert abs(got - (base + 2 * math.pi * k)) < 1e-12
    assert abs(base - m) <= e + 1e-15
    nu = sa.true_from_eccentric(base, e)
    assert abs(nu - base) <= math.pi + 1e-15


def test_ordering_between_perigee_and_apogee():
    e, m = 0.5, 1.0
    E = sa.eccentric_from_mean(m, e)
    nu = sa.true_from_mean(m, e)
    assert E == pytest.approx(1.4987011335178484, abs=1e-14)
    assert nu == pytest.approx(2.030806214849156, abs=1e-14)
    assert m < E < nu < math.pi


def test_half_angle_relation_and_pi_over_2_case():
    e, E = 0.5, math.pi / 2
    nu = sa.true_from_eccentric(E, e)
    assert nu == pytest.approx(2 * math.pi / 3, abs=1e-15)
    lhs = math.tan(nu / 2)
    rhs = math.sqrt((1 + e) / (1 - e)) * math.tan(E / 2)
    assert lhs == pytest.approx(rhs, rel=1e-13)


def test_inverse_relations():
    rnd = random.Random(7)
    for _ in range(40):
        e = rnd.uniform(0.0, 0.99)
        E = rnd.uniform(-3.0, 3.0)
        M = sa.mean_from_eccentric(E, e)
        assert sa.eccentric_from_mean(M, e) == pytest.approx(E, abs=1e-12)
        nu = sa.true_from_eccentric(E, e)
        assert sa.eccentric_from_true(nu, e) == pytest.approx(E, abs=1e-12)
    for _ in range(30):
        e = rnd.uniform(0.0, 0.9)
        M = rnd.uniform(-3.0, 3.0)
        assert sa.mean_from_true(sa.true_from_mean(M, e), e) == pytest.approx(M, abs=1e-12)
    for _ in range(30):
        e = rnd.uniform(1.01, 3.0)
        F = rnd.uniform(-5.0, 5.0)
        M = sa.mean_from_hyperbolic(F, e)
        assert sa.hyperbolic_from_mean(M, e) == pytest.approx(F, abs=1e-12)
        nu = sa.true_from_hyperbolic(F, e)
        assert sa.hyperbolic_from_true(nu, e) == pytest.approx(F, abs=1e-9)
