"""Tests written from mutation-testing survivors (12_EVIDENCE/mutation/star_elements_20261004.json, score 0.812).
Each test pins a boundary the original suite never touched."""
import math

import pytest

from star_elements import (MU_EARTH, coe_to_rv, eccentric_to_mean, eccentric_to_true, mean_to_eccentric, rv_to_coe,
                           true_to_eccentric)

TWO_PI = 2 * math.pi


def test_mu_constant_and_non_positive_mu():
    assert MU_EARTH == 398600.4418
    with pytest.raises(ValueError):
        rv_to_coe([7000, 0, 1000], [0, 7.0, 1.0], mu=0.0)
    with pytest.raises(ValueError):
        coe_to_rv(50000, 0.1, 0.5, 0.0, 0.0, 0.0, mu=0.0)


def test_angles_exactly_on_reference_directions_are_zero_not_two_pi():
    # node on +x (RAAN = 0), periapsis at the node (argp = 0), at periapsis (nu = 0)
    r, v = coe_to_rv(60000.0, 0.2, math.radians(30), 0.0, 0.0, 0.0)
    h, e, i, raan, argp, nu = rv_to_coe(r, v)
    for ang in (raan, argp, nu):
        assert 0.0 <= ang < TWO_PI
        assert min(ang, TWO_PI - ang) < 1e-9


def test_eccentric_anomaly_always_in_zero_two_pi():
    for M in (0.0, 1e-12, math.pi, TWO_PI - 1e-9, 7.0, -1.0):
        for e in (0.0, 0.5, 0.95):
            E = mean_to_eccentric(M, e)
            assert 0.0 <= E < TWO_PI


@pytest.mark.parametrize("fn", [eccentric_to_true, true_to_eccentric, eccentric_to_mean])
@pytest.mark.parametrize("e", [1.0, 1.2, -0.01])
def test_every_conversion_rejects_non_elliptic(fn, e):
    with pytest.raises(ValueError):
        fn(1.0, e)


@pytest.mark.parametrize("fn", [eccentric_to_true, true_to_eccentric, eccentric_to_mean])
def test_every_conversion_accepts_circular(fn):
    assert abs(fn(1.0, 0.0) - 1.0) < 1e-12
