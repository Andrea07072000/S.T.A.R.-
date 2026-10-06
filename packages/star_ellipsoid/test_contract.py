"""Refusals of star_ellipsoid with hostile inputs (NaN, inf, huge integers, booleans, text, latitudes outside the range).
Verifies: R4 (README).

Every function returns a finite float or raises ValueError: a latitude of 91 degrees is not wrapped to 89."""
import math
from fractions import Fraction

import pytest

import star_ellipsoid as e

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 90.0000001, -90.0000001, 180, True, False, "45", None, 1j, [45.0]]
FUNCS = [e.meridian_radius, e.prime_vertical_radius, e.gaussian_radius, e.geocentric_radius, e.geocentric_latitude,
         e.parametric_latitude, e.meridian_arc, e.rectifying_latitude]


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(FUNCS) == 8 and e.__version__ == "0.1.0"
    assert e.__all__[:8] == [f.__name__ for f in FUNCS] and e.__all__[8:] == ["A", "F", "B", "E2", "MERIDIAN_QUADRANT"]
    assert e._N == pytest.approx(0.0016792203863837047, rel=1e-15) and len(e._ARC) == 5
    assert e._ARC[0] == pytest.approx(-1.5 * e._N, rel=1e-6) and e._ARC[1] == pytest.approx(15 / 16 * e._N ** 2, rel=1e-6)
    assert e._ARC[2] == pytest.approx(-35 / 48 * e._N ** 3, rel=1e-6) and e._ARC[3] == 315 / 512 * e._N ** 4 and e._ARC[4] == -693 / 1280 * e._N ** 5


@pytest.mark.parametrize("f", FUNCS, ids=lambda f: f.__name__)
def test_every_function_refuses_every_hostile_value(f):
    for bad in BAD:
        with pytest.raises(ValueError, match="latitude must be a real number"):
            f(bad)


@pytest.mark.parametrize("f", FUNCS, ids=lambda f: f.__name__)
def test_limits_and_number_types_are_accepted(f):
    for lat in (-90, -90.0, 0, 0.0, -0.0, 90, 90.0, Fraction(91, 2), 5e-324):
        out = f(lat)
        assert type(out) is float and math.isfinite(out)
    assert f(45) == f(45.0) == f(Fraction(45))


def test_results_stay_in_their_ranges():
    for k in range(-900, 901, 25):
        lat = k / 10
        lo, hi = 1 - 1e-14, 1 + 1e-14                                    # one unit of rounding at the two ends
        assert e.B * e.B / e.A * lo <= e.meridian_radius(lat) <= e.A * e.A / e.B * hi
        assert e.A * lo <= e.prime_vertical_radius(lat) <= e.A * e.A / e.B * hi
        assert e.B * lo <= e.geocentric_radius(lat) <= e.A * hi and e.B * lo <= e.gaussian_radius(lat) <= e.A * e.A / e.B * hi
        for f in (e.geocentric_latitude, e.parametric_latitude, e.rectifying_latitude):
            assert -90.0 <= f(lat) <= 90.0 and abs(f(lat)) <= abs(lat) + 1e-12
        assert abs(e.meridian_arc(lat)) <= e.MERIDIAN_QUADRANT * (1 + 1e-15)
