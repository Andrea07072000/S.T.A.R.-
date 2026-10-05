"""Error contract of star_geodesy (written 2026-10-05 while linking tests to requirements).
Verifies: R2, R3 (README).

Found while writing it: ecef_to_geodetic(inf, 0, 0) returned (0.0, 0.0, inf) - a value for a non-finite input - and a
NaN input was reported as "iteration did not converge". Both now raise ValueError (invalid input); RuntimeError is kept
for a genuine non-convergence, which is forced here with an iteration budget too small to converge."""
import math

import pytest

from star_geodesy import ecef_to_geodetic, geodetic_to_ecef

VALLADO_3_3 = (6524834.0, 6862875.0, 6448296.0)


@pytest.mark.parametrize("budget", [0, 1])
def test_non_convergence_raises_instead_of_returning_a_value(budget):
    with pytest.raises(RuntimeError):
        ecef_to_geodetic(*VALLADO_3_3, max_iter=budget)


def test_default_budget_converges_on_the_same_point():
    lat, lon, h = ecef_to_geodetic(*VALLADO_3_3)
    assert all(map(math.isfinite, (lat, lon, h)))


@pytest.mark.parametrize("bad", [(math.inf, 0.0, 0.0), (0.0, 0.0, math.inf), (math.nan, 1e6, 1e6), (1e6, 1e6, -math.inf)])
def test_non_finite_ecef_is_invalid_input(bad):
    with pytest.raises(ValueError):
        ecef_to_geodetic(*bad)


@pytest.mark.parametrize("bad", [(math.nan, 0.0, 0.0), (0.0, math.nan, 0.0), (0.0, 0.0, math.inf), (0.0, math.inf, 0.0)])
def test_non_finite_geodetic_is_invalid_input(bad):
    with pytest.raises(ValueError):
        geodetic_to_ecef(*bad)


def test_earth_centre_is_invalid_input():
    with pytest.raises(ValueError):
        ecef_to_geodetic(0.0, 0.0, 0.0)
