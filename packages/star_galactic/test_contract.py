"""Refusals of star_galactic with hostile inputs (NaN, inf, huge integers, booleans, text, values outside ranges).
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release.

Every function returns finite floats in the documented ranges or raises ValueError: nothing is wrapped silently."""
import math
from fractions import Fraction

import pytest

import star_galactic as sg

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400,
       1e300, -1e300, True, False, "10", None, 1j, [10.0], (1.0,)]
G = (180.0, 30.0, "icrs")


def test_the_hostile_set_is_pinned():
    assert len(BAD) == 14 and sg.__version__ == "0.1.0"
    assert sg.__all__ == ["equatorial_to_galactic", "galactic_to_equatorial"]
    assert sorted(sg.SYSTEMS) == ["b1950", "icrs"]
    assert sg.SYSTEMS["icrs"] == (192.85948, 27.12825, 122.93192)
    assert sg.SYSTEMS["b1950"] == (192.25, 27.4, 123.0)


@pytest.mark.parametrize("f", [sg.equatorial_to_galactic, sg.galactic_to_equatorial], ids=lambda f: f.__name__)
def test_every_argument_refuses_every_hostile_value(f):
    assert all(type(v) is float and math.isfinite(v) for v in f(*G))
    for bad in BAD:
        for i in range(3):
            args = list(G)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("f", [sg.equatorial_to_galactic, sg.galactic_to_equatorial], ids=lambda f: f.__name__)
@pytest.mark.parametrize("system", ["ICRS", "B1950", "", " icrs", b"icrs", None, 2006, 1980.0, ["icrs"], True])
def test_unknown_systems_are_refused(f, system):
    with pytest.raises(ValueError, match="system"):
        f(180.0, 30.0, system)


@pytest.mark.parametrize("args, why", [
    ((360.0000001, 0.0, "icrs"), "right ascension"),
    ((-360.0000001, 0.0, "icrs"), "right ascension"),
    ((0.0, 90.0000001, "icrs"), "declination"),
    ((0.0, -90.0000001, "icrs"), "declination"),
])
def test_equatorial_angles_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        sg.equatorial_to_galactic(*args)


@pytest.mark.parametrize("args, why", [
    ((360.0000001, 0.0, "icrs"), "galactic longitude"),
    ((-360.0000001, 0.0, "icrs"), "galactic longitude"),
    ((0.0, 90.0000001, "icrs"), "galactic latitude"),
    ((0.0, -90.0000001, "icrs"), "galactic latitude"),
])
def test_galactic_angles_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        sg.galactic_to_equatorial(*args)


def test_limits_are_accepted_and_results_stay_in_range():
    for system in ("icrs", "b1950"):
        for args in ((360, 90, system), (-360, -90, system), (0, 0, system),
                     (Fraction(1, 2), Fraction(1, 3), system), (359.9999999999, 0.0, system)):
            for f in (sg.equatorial_to_galactic, sg.galactic_to_equatorial):
                lon, lat = f(*args)
                assert 0.0 <= lon < 360.0 and -90.0 <= lat <= 90.0
                assert type(lon) is float and type(lat) is float
                assert math.isfinite(lon) and math.isfinite(lat)
