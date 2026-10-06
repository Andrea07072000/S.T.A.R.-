"""Refusals of star_sphere with hostile inputs (NaN, inf, huge integers, booleans, text, angles outside their ranges).
Verifies: R4 (README).

Every function returns finite floats in the documented ranges or raises ValueError: nothing is wrapped silently."""
import math
from fractions import Fraction

import pytest

import star_sphere as s

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e300, True, False, "10", None, 1j, [10.0], (1.0,), 361.0]
G = (10.0, 20.0, 30.0, 40.0)


def test_the_hostile_set_is_pinned():
    assert len(BAD) == 14 and s.__all__ == ["separation_deg", "position_angle_deg", "offset"] and s.__version__ == "0.1.0"


@pytest.mark.parametrize("f", [s.separation_deg, s.position_angle_deg, s.offset], ids=lambda f: f.__name__)
def test_every_argument_refuses_every_hostile_value(f):
    assert all(type(v) is float and math.isfinite(v) for v in (f(*G) if isinstance(f(*G), tuple) else (f(*G),)))
    for bad in BAD:
        for i in range(4):
            args = list(G)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("args, why", [((0, 90.0000001, 0, 0), "latitude"), ((0, -90.0000001, 0, 0), "latitude"), ((0, 0, 0, 91), "latitude"),
                                       ((360.0000001, 0, 0, 0), "longitude"), ((0, 0, -360.0000001, 0), "longitude")])
def test_points_out_of_range(args, why):
    for f in (s.separation_deg, s.position_angle_deg):
        with pytest.raises(ValueError, match=why):
            f(*args)


@pytest.mark.parametrize("args, why", [((0, 91, 0, 1), "latitude"), ((361, 0, 0, 1), "longitude"), ((0, 0, 360.0000001, 1), "position angle"),
                                       ((0, 0, -361, 1), "position angle"), ((0, 0, 0, -1e-9), "distance"), ((0, 0, 0, 180.0000001), "distance")])
def test_offset_arguments_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        s.offset(*args)


def test_limits_and_ranges_of_the_results():
    for args in ((360, 90, -360, -90), (-360, -90, 360, 90), (0, 0, 0, 0), (Fraction(1, 2), 1, 2, 3)):
        sep, pa = s.separation_deg(*args), s.position_angle_deg(*args)
        assert 0.0 <= sep <= 180.0 and 0.0 <= pa < 360.0 and type(sep) is float and type(pa) is float
    for args in ((360, 90, 360, 180), (-360, -90, -360, 0), (0, 90, 45, 90), (0, -90, 45, 10)):
        lon, lat = s.offset(*args)
        assert 0.0 <= lon < 360.0 and -90.0 <= lat <= 90.0
    assert s.position_angle_deg(5, 5, 5, 5) == 0.0 and s.position_angle_deg(0, 90, 0, 90) == 0.0          # undefined: returned as 0
    assert s._wrap360(-1e-20) == 0.0 and s._wrap360(360.0) == 0.0 and s._wrap360(-90.0) == 270.0 and s._wrap360(725.0) == 5.0
    assert s.separation_deg(0, 90, 123, 90) == pytest.approx(0.0, abs=1e-13) and s.separation_deg(0, 90, 55, -90) == pytest.approx(180.0, abs=1e-13)
