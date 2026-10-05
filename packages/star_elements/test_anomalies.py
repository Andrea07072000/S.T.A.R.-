"""Anomaly conversions. References: Vallado (4th ed.) Example 2-1 (M = 235.4 deg, e = 0.4 -> E = 220.512074767522 deg)
and Curtis (3rd ed.) Example 3.2 (M = 3.6029 rad, e = 0.37255 -> E = 3.4794 rad, printed to 5 figures)."""
import math
import random

import pytest

from star_elements import eccentric_to_mean, eccentric_to_true, mean_to_eccentric, true_to_eccentric


def test_vallado_example_2_1():
    assert abs(math.degrees(mean_to_eccentric(math.radians(235.4), 0.4)) - 220.512074767522) < 1e-9


def test_curtis_example_3_2():
    assert abs(mean_to_eccentric(3.6029, 0.37255) - 3.4794) <= 5e-5


def test_round_trips_up_to_e_0_999():
    rnd = random.Random(7)
    for _ in range(3000):
        e = rnd.choice([0.0, rnd.uniform(0, 0.9), rnd.uniform(0.9, 0.999)])
        M = rnd.uniform(0, 2 * math.pi)
        E = mean_to_eccentric(M, e)
        assert abs(math.remainder(eccentric_to_mean(E, e) - M, 2 * math.pi)) < 1e-11
        nu = eccentric_to_true(E, e)
        assert abs(math.remainder(true_to_eccentric(nu, e) - E, 2 * math.pi)) < 1e-9


def test_circular_orbit_all_anomalies_equal():
    for x in (0.1, 2.0, 5.5):
        assert abs(mean_to_eccentric(x, 0.0) - x) < 1e-14 and abs(eccentric_to_true(x, 0.0) - x) < 1e-14


@pytest.mark.parametrize("e", [1.0, 1.5, -0.1])
def test_non_elliptic_rejected(e):
    with pytest.raises(ValueError):
        mean_to_eccentric(1.0, e)


def test_non_convergence_is_an_error():
    with pytest.raises(RuntimeError):
        mean_to_eccentric(1.0, 0.99, max_iter=1)
