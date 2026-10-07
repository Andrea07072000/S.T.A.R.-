"""Refusals and limits for every public function in star_anomaly.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_anomaly as sa

BAD = [True, False, "x", None, 1j, float("nan"), float("inf"), float("-inf")]


def test_pinned_constants_and_exports():
    assert sa.MAX_ANGLE == 1e9
    assert sa.MAX_HYPERBOLIC == 700.0
    assert sa.MAX_MEAN == 1e150
    assert sa.__version__ == "0.1.0"
    assert len(sa.__all__) == 10


@pytest.mark.parametrize("bad", BAD)
def test_all_functions_refuse_hostile_each_argument(bad):
    funcs = [
        (sa.eccentric_from_mean, [1.0, 0.2]),
        (sa.mean_from_eccentric, [1.0, 0.2]),
        (sa.true_from_eccentric, [1.0, 0.2]),
        (sa.eccentric_from_true, [1.0, 0.2]),
        (sa.true_from_mean, [1.0, 0.2]),
        (sa.mean_from_true, [1.0, 0.2]),
        (sa.hyperbolic_from_mean, [1.0, 2.0]),
        (sa.mean_from_hyperbolic, [1.0, 2.0]),
        (sa.true_from_hyperbolic, [1.0, 2.0]),
        (sa.hyperbolic_from_true, [1.0, 2.0]),
    ]
    for f, args in funcs:
        for i in range(2):
            a = list(args)
            a[i] = bad
            with pytest.raises(ValueError):
                f(*a)


def test_e_domain_closed_and_open_with_just_inside():
    e_closed_ok = math.nextafter(1.0, 0.0)
    assert isinstance(sa.mean_from_eccentric(1.0, e_closed_ok), float)
    for e in (1.0, 1.5, -0.1):
        for f in (sa.eccentric_from_mean, sa.mean_from_eccentric, sa.true_from_eccentric, sa.eccentric_from_true, sa.true_from_mean, sa.mean_from_true):
            with pytest.raises(ValueError):
                f(0.1, e)
    e_open_ok = math.nextafter(1.0, 2.0)
    assert isinstance(sa.mean_from_hyperbolic(0.1, e_open_ok), float)
    for e in (1.0, 0.5, 0.0):
        for f in (sa.hyperbolic_from_mean, sa.mean_from_hyperbolic, sa.true_from_hyperbolic, sa.hyperbolic_from_true):
            with pytest.raises(ValueError):
                f(0.1, e)


def test_closed_angle_limits():
    assert isinstance(sa.eccentric_from_mean(1e9, 0.3), float)
    assert isinstance(sa.mean_from_eccentric(-1e9, 0.3), float)
    with pytest.raises(ValueError):
        sa.eccentric_from_mean(1.0000001e9, 0.3)
    with pytest.raises(ValueError):
        sa.mean_from_eccentric(-1.0000001e9, 0.3)


def test_open_limits_and_asymptote_guards():
    assert isinstance(sa.mean_from_hyperbolic(700.0, 2.0), float)
    with pytest.raises(ValueError):
        sa.mean_from_hyperbolic(700.0000001, 2.0)
    assert isinstance(sa.hyperbolic_from_mean(1e150, 2.0), float)
    with pytest.raises(ValueError):
        sa.hyperbolic_from_mean(1.0000001e150, 2.0)
    assert isinstance(sa.hyperbolic_from_true(2.0, 2.0), float)
    for nu in (2.2, math.pi, -math.pi - 1e-12, math.pi + 1e-12):
        with pytest.raises(ValueError):
            sa.hyperbolic_from_true(nu, 2.0)


def test_mean_from_hyperbolic_overflow_refusal():
    with pytest.raises(ValueError):
        sa.mean_from_hyperbolic(700.0, 1e150)
