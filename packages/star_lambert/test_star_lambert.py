# -*- coding: utf-8 -*-
"""star_lambert tests: a PUBLISHED value (Curtis Ex. 5.2), a PHYSICAL property (propagating v1 for tof reaches r2,
checked with an independent RK4 two-body integrator), and the failure contract."""
import math

import pytest

from star_lambert import MU_EARTH, lambert

R1, R2, TOF = (5000.0, 10000.0, 2100.0), (-14600.0, 2500.0, 7000.0), 3600.0


def test_curtis_example_5_2_published_values():
    v1, v2 = lambert(R1, R2, TOF)
    for got, exp in zip(v1 + v2, (-5.9925, 1.9254, 3.2456, -3.3125, -4.1966, -0.38529)):
        assert abs(got - exp) < 1e-3


def _rk4(r, v, t, n=20000, mu=MU_EARTH):
    h = t / n
    def acc(p):
        d = math.sqrt(sum(x * x for x in p)) ** 3
        return [-mu * x / d for x in p]
    r, v = list(r), list(v)
    for _ in range(n):
        a1 = acc(r); k1r, k1v = v, a1
        r2 = [r[i] + h / 2 * k1r[i] for i in range(3)]; v2 = [v[i] + h / 2 * k1v[i] for i in range(3)]
        a2 = acc(r2); k2r, k2v = v2, a2
        r3 = [r[i] + h / 2 * k2r[i] for i in range(3)]; v3 = [v[i] + h / 2 * k2v[i] for i in range(3)]
        a3 = acc(r3); k3r, k3v = v3, a3
        r4 = [r[i] + h * k3r[i] for i in range(3)]; v4 = [v[i] + h * k3v[i] for i in range(3)]
        a4 = acc(r4); k4r, k4v = v4, a4
        r = [r[i] + h / 6 * (k1r[i] + 2 * k2r[i] + 2 * k3r[i] + k4r[i]) for i in range(3)]
        v = [v[i] + h / 6 * (k1v[i] + 2 * k2v[i] + 2 * k3v[i] + k4v[i]) for i in range(3)]
    return r


def test_propagated_v1_reaches_r2():
    v1, _ = lambert(R1, R2, TOF)
    rf = _rk4(R1, v1, TOF)
    assert math.dist(rf, R2) < 1e-3                     # km


def test_contract_errors():
    with pytest.raises(ValueError):
        lambert(R1, R2, -10)
    with pytest.raises(ValueError):
        lambert((0, 0, 0), R2, TOF)


def test_invalid_inputs_fail_explicitly():
    import pytest as _pt
    from star_lambert import lambert as _l
    with _pt.raises(ValueError):
        _l([0, 0, 0], [7000, 0, 0], 3600)            # zero position vector
    with _pt.raises(ValueError):
        _l([7000, 0, 0], [-8000, 0, 0], 3600)        # 180 deg: transfer plane undefined
    with _pt.raises(ValueError):
        _l([7000, 0, 0], [0, 8000, 0], -10)          # negative time of flight
