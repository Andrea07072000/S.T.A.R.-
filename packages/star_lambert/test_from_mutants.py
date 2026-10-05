"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_lambert_20261004.json, score 0.467): the original
suite checked only final velocities, so the Newton derivative, the small-|z| series, the hyperbolic branch and the
retrograde branch were never exercised."""
import math

import pytest

from star_lambert import MU_EARTH, _stumpff_c, _stumpff_s, _universal_functions, lambert

R1, R2 = (5000.0, 10000.0, 2100.0), (-14600.0, 2500.0, 7000.0)   # Curtis Ex. 5.2 geometry


def _exact_c(z):
    return (1 - math.cos(math.sqrt(z))) / z if z > 0 else (math.cosh(math.sqrt(-z)) - 1) / (-z)


def _exact_s(z):
    if z > 0:
        s = math.sqrt(z); return (s - math.sin(s)) / s ** 3
    s = math.sqrt(-z); return (math.sinh(s) - s) / s ** 3


@pytest.mark.parametrize("z", [-50.0, -5.0, -1e-3, -2e-8, 2e-8, 1e-3, 5.0, 30.0])
def test_stumpff_match_closed_forms_on_both_branches(z):
    assert math.isclose(_stumpff_c(z), _exact_c(z), rel_tol=1e-9)
    assert math.isclose(_stumpff_s(z), _exact_s(z), rel_tol=1e-6)


def test_stumpff_series_at_zero():
    assert _stumpff_c(0.0) == 0.5 and math.isclose(_stumpff_s(0.0), 1 / 6, rel_tol=1e-15)
    for z in (5e-9, -5e-9):                                  # inside the series branch, continuity with closed form
        assert math.isclose(_stumpff_c(z), 0.5 - z / 24, rel_tol=1e-12)
        assert math.isclose(_stumpff_s(z), 1 / 6 - z / 120, rel_tol=1e-12)


def _geometry():
    r1n, r2n = math.sqrt(sum(x * x for x in R1)), math.sqrt(sum(x * x for x in R2))
    cos_d = sum(a * b for a, b in zip(R1, R2)) / (r1n * r2n)
    d = math.acos(cos_d)
    if R1[0] * R2[1] - R1[1] * R2[0] < 0:
        d = 2 * math.pi - d
    return r1n, r2n, math.sin(d) * math.sqrt(r1n * r2n / (1 - math.cos(d)))


@pytest.mark.parametrize("z", [-3.0, -0.5, 1e-9, 0.5, 1.5, 3.0, 8.0])
def test_newton_derivative_matches_numerical_derivative(z):
    r1n, r2n, A = _geometry()
    y, F, dF = _universal_functions(r1n, r2n, A, MU_EARTH, 3600.0)
    if y(z - 1e-4) <= 0:
        pytest.skip("y(z) < 0 here: F undefined (outside the physical domain)")
    h = 1e-5 if abs(z) > 1e-6 else 1e-4
    num = (F(z + h) - F(z - h)) / (2 * h)
    assert math.isclose(dF(z), num, rel_tol=1e-5)


def test_retrograde_branch_reverses_angular_momentum():
    vp, _ = lambert(R1, R2, 3600.0, prograde=True)
    vr, _ = lambert(R1, R2, 3600.0, prograde=False)
    hz = lambda v: R1[0] * v[1] - R1[1] * v[0]
    assert hz(vp) > 0 and hz(vr) < 0


def test_boundaries():
    with pytest.raises(ValueError):
        lambert(R1, R2, 0.0)                                  # tof = 0 is not a transfer
    with pytest.raises(ValueError):
        lambert(R1, (0.0, 0.0, 0.0), 3600.0)
