"""Refusals of star_geodesic with hostile inputs (NaN, inf, huge integers, booleans, text, out-of-range angles).
Verifies: R4 (README).

Every call returns three finite floats, raises ValueError for invalid input, or raises RuntimeError when the geodesic
is not unique or the iteration does not converge: never NaN, never an unconverged value, never another exception."""
import math
from fractions import Fraction

import pytest

import star_geodesic as g

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "1", None, 1j, [1.0], (1.0,)]
GOOD_INV, GOOD_DIR = (10.0, 20.0, 30.0, 40.0), (10.0, 20.0, 30.0, 40000.0)


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and g.__all__ == ["inverse", "direct"] and g.__version__ == "0.1.0"
    assert (g.A, g.F, g.MAX_ITER, g.MAX_DISTANCE_M, g.TOL, g.POLISH) == (6378137.0, 1 / 298.257223563, 200, 2.0e7, 1e-12, 2)
    assert abs(g.B - 6356752.314245179) < 1e-9


@pytest.mark.parametrize("f, good", [(g.inverse, GOOD_INV), (g.direct, GOOD_DIR)])
def test_every_argument_refuses_every_hostile_value(f, good):
    assert all(isinstance(v, float) and math.isfinite(v) for v in f(*good))
    for i in range(4):
        for bad in BAD:
            args = list(good)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("args", [(90.0000001, 0, 0, 0), (-90.0000001, 0, 0, 0), (0, 360.0000001, 0, 0), (0, -360.0000001, 0, 0),
                                  (0, 0, 90.0000001, 0), (0, 0, -90.0000001, 0), (0, 0, 0, 360.0000001), (0, 0, 0, -360.0000001)])
def test_inverse_refuses_coordinates_out_of_range(args):
    with pytest.raises(ValueError, match="must be within"):
        g.inverse(*args)


@pytest.mark.parametrize("args", [(90.0000001, 0, 0, 1), (0, 360.0000001, 0, 1), (0, 0, 360.0000001, 1), (0, 0, -360.0000001, 1),
                                  (0, 0, 0, -1e-9), (0, 0, 0, 2.0e7 + 1e-6), (0, 0, 0, -1.0)])
def test_direct_refuses_arguments_out_of_range(args):
    with pytest.raises(ValueError, match="must be within"):
        g.direct(*args)


def test_the_limits_themselves_are_accepted():
    for args in ((90, 360, -90, -360 + 1), (-90, -360, 89.5, 360), (0, 0, 0, 0)):
        try:
            out = g.inverse(*args)
        except RuntimeError:
            continue
        assert all(map(math.isfinite, out))
    for args in ((90, 360, 360, 2.0e7), (-90, -360, -360, 0), (0, 0, 0, 0.0), (45, 45, 45, 5e-324)):
        out = g.direct(*args)
        assert all(map(math.isfinite, out)) and -90 <= out[0] <= 90 and -180 <= out[1] < 180 and 0 <= out[2] < 360
    assert g.inverse(1, 2, 3, 4) == g.inverse(Fraction(1), 2, 3.0, 4) and g.direct(1, 2, 3, 4)[0] > 1


def test_azimuth_is_never_360_and_minus_zero_is_zero():
    assert g._az(-1e-20) == 0.0 and g._az(2 * math.pi) == 0.0 and g._az(-math.pi / 2) == 270.0 and g._az(0.0) == 0.0
    for args in ((0, 0, 1, 0), (0, 0, 1, -1e-13), (5, 5, 5.0001, 5)):
        _, a1, a2 = g.inverse(*args)
        assert 0.0 <= a1 < 360.0 and 0.0 <= a2 < 360.0


def test_the_iteration_budget_is_a_hard_limit(monkeypatch):
    monkeypatch.setattr(g, "MAX_ITER", 1)
    with pytest.raises(RuntimeError, match="does not converge"):
        g.inverse(10, 20, 30, 40)
    with pytest.raises(RuntimeError, match="did not converge"):
        g.direct(10, 20, 30, 4e6)
    monkeypatch.setattr(g, "MAX_ITER", 200)
    monkeypatch.setattr(g, "POLISH", 0)
    plain = g.inverse(27.93587, -143.73466, 27.93585, -143.73465)
    monkeypatch.setattr(g, "POLISH", 2)
    polished = g.inverse(27.93587, -143.73466, 27.93585, -143.73465)
    assert abs(plain[0] - polished[0]) < 1e-5 and plain != polished        # the two extra contractions do change the answer
