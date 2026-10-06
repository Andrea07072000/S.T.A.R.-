"""Refusals of star_atmosphere with hostile inputs (NaN, inf, huge integers, booleans, text, altitudes outside the model).
Verifies: R4 (README).

Every function returns finite positive values or raises ValueError: never NaN, never an extrapolation."""
import math
from fractions import Fraction

import pytest

import star_atmosphere as a

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "1", None, 1j, [1.0], (1.0,)]
FUNCS = (a.ussa1976, a.geopotential_m, a.geometric_m)


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and a.__all__ == ["ussa1976", "geopotential_m", "geometric_m"] and a.__version__ == "0.1.0"
    assert (a.G0, a.R_STAR, a.M0, a.R_EARTH, a.GAMMA, a.T0, a.P0) == (9.80665, 8.31432, 0.0289644, 6356766.0, 1.4, 288.15, 101325.0)
    assert (a.Z_MIN, a.Z_MAX) == (-5000.0, 86000.0) and len(a.LAYERS) == 7
    assert a.LAYERS == ((0.0, -0.0065), (11000.0, 0.0), (20000.0, 0.001), (32000.0, 0.0028), (47000.0, 0.0), (51000.0, -0.0028), (71000.0, -0.002))
    assert a.H_MIN == pytest.approx(-5003.9359, abs=1e-3) and a.H_MAX == pytest.approx(84852.0458, abs=1e-3)


@pytest.mark.parametrize("f", FUNCS)
def test_every_hostile_value_is_refused(f):
    for bad in BAD:
        with pytest.raises(ValueError):
            f(bad)


@pytest.mark.parametrize("z", [-5000.001, 86000.001, -1e9, 1e9, 87000, 100000, -6000])
def test_altitudes_outside_the_model_are_refused_not_extrapolated(z):
    with pytest.raises(ValueError, match="outside"):
        a.ussa1976(z)
    with pytest.raises(ValueError, match="outside"):
        a.geopotential_m(z)


@pytest.mark.parametrize("h", [-5003.94, 84852.05, -1e9, 1e9, 6356766.0, 86000.0])
def test_geopotential_altitudes_outside_the_model_are_refused(h):
    with pytest.raises(ValueError, match="outside"):
        a.geometric_m(h)


def test_the_limits_themselves_are_accepted_and_results_are_finite_positive_floats():
    for z in (-5000.0, -5000, 0, 0.0, -0.0, 86000.0, 86000, Fraction(86000), 5e-324):
        out = a.ussa1976(z)
        assert len(out) == 4 and all(isinstance(v, float) and math.isfinite(v) and v > 0 for v in out)
        assert isinstance(a.geopotential_m(z), float)
    assert a.ussa1976(Fraction(1000)) == a.ussa1976(1000.0) == a.ussa1976(1000)
    assert a.geometric_m(a.H_MAX + 5e-7) == 86000.0 and a.geometric_m(a.H_MIN - 5e-7) == -5000.0     # rounding of the caller


def test_num_reports_the_reason():
    with pytest.raises(ValueError, match="^altitude must be a finite real number$"):
        a.ussa1976("high")
    assert a._num(3) == 3.0 and isinstance(a._num(3), float)
    assert a._layer(288.15, 101325.0, 0.0, 0.0, 0.0) == (288.15, 101325.0)
    t, p = a._layer(216.65, 22632.06, 11000.0, 0.0, 12000.0)
    assert t == 216.65 and p == pytest.approx(22632.06 * math.exp(-9.80665 * 0.0289644 * 1000 / (8.31432 * 216.65)), rel=1e-15)
