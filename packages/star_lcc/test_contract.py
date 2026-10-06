"""Refusals and inclusive input limits of every public star_lcc function.

Hostile values are pinned; each numeric argument is tested independently.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (one refusal message expectation)."""
import math
from fractions import Fraction

import pytest

import star_lcc as sl

BAD = [
    float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400,
    1e300, -1e300, True, False, "10", None, 1j, [10.0], (1.0,),
]
BASE = {
    sl.lcc_forward: (35, -75, 33, 45, 23, -96, 6378137.0, sl.WGS84_F),
    sl.lcc_inverse: (0, 0, 33, 45, 23, -96, 6378137.0, sl.WGS84_F),
    sl.lcc_scale: (35, 33, 45, 6378137.0, sl.WGS84_F),
}
POSITIONS = {
    sl.lcc_forward: ("latitude", "longitude", "first standard parallel",
                     "second standard parallel", "latitude of origin",
                     "central meridian", "a", "f"),
    sl.lcc_inverse: ("x", "y", "first standard parallel",
                     "second standard parallel", "latitude of origin",
                     "central meridian", "a", "f"),
    sl.lcc_scale: ("latitude", "first standard parallel",
                   "second standard parallel", "a", "f"),
}


def test_pinned_public_interface_hostile_set_and_constants():
    assert len(BAD) == 14
    assert sl.__version__ == "0.1.0"
    assert sl.__all__ == [
        "lcc_forward", "lcc_inverse", "lcc_scale", "WGS84_A", "WGS84_F"
    ]
    assert sl.WGS84_A == 6378137.0
    assert sl.WGS84_F == 1 / 298.257223563
    assert sl.MAX_LAT == 89.0
    assert sl.MIN_PARALLEL == 1e-3


@pytest.mark.parametrize("func", list(BASE), ids=lambda f: f.__name__)
def test_every_argument_refuses_every_pinned_hostile_value(func):
    result = func(*BASE[func])
    values = result if isinstance(result, tuple) else (result,)
    assert all(type(v) is float and math.isfinite(v) for v in values)
    for bad in BAD:
        for index, name in enumerate(POSITIONS[func]):
            args = list(BASE[func])
            args[index] = bad
            with pytest.raises(ValueError, match=name):
                func(*args)


def _arguments_at(func, index, value):
    args = list(BASE[func])
    args[index] = value
    name = POSITIONS[func][index]
    # A negative standard parallel needs a second parallel on the same side.
    if name in ("first standard parallel", "second standard parallel") and value < 0:
        other = POSITIONS[func].index(
            "second standard parallel" if name == "first standard parallel"
            else "first standard parallel"
        )
        args[other] = -45
    return args


@pytest.mark.parametrize("func", list(BASE), ids=lambda f: f.__name__)
def test_inclusive_numeric_limits_and_immediately_adjacent_values(func):
    for index, name in enumerate(POSITIONS[func]):
        if name in ("x", "y"):
            # The coordinate guard has its own test below: its endpoints can
            # describe points outside the inverse projection's latitude domain.
            continue
        if name in ("latitude", "latitude of origin",
                    "first standard parallel", "second standard parallel"):
            low, high = -89.0, 89.0
        elif name in ("longitude", "central meridian"):
            low, high = -180.0, 180.0
        elif name == "a":
            low, high = 1e3, 1e9
        else:
            assert name == "f"
            low, high = 0.0, 0.1

        for value in (low, math.nextafter(low, high),
                      math.nextafter(high, low), high):
            if "standard parallel" in name and abs(value) < sl.MIN_PARALLEL:
                continue
            args = _arguments_at(func, index, value)
            result = func(*args)
            values = result if isinstance(result, tuple) else (result,)
            assert all(type(v) is float and math.isfinite(v) for v in values)
        for value in (math.nextafter(low, -math.inf),
                      math.nextafter(high, math.inf)):
            with pytest.raises(ValueError, match=name):
                func(*_arguments_at(func, index, value))


@pytest.mark.parametrize("func", list(BASE), ids=lambda f: f.__name__)
def test_both_parallels_refuse_degenerate_or_opposite_side_cones(func):
    first = POSITIONS[func].index("first standard parallel")
    second = POSITIONS[func].index("second standard parallel")
    for p1, p2 in (
        (33, -45), (-33, 45), (0, 0), (0, 10), (10, 0),
        (0.0005, 10), (10, 0.0005),
        (-0.0005, -10), (-10, -0.0005),
        (math.nextafter(sl.MIN_PARALLEL, 0), 10),
        (10, math.nextafter(sl.MIN_PARALLEL, 0)),
    ):
        args = list(BASE[func])
        args[first], args[second] = p1, p2
        with pytest.raises(ValueError, match="standard parallels"):
            func(*args)

    # At the threshold, p1=p2 is a valid tangent cone on either side.
    for p in (-sl.MIN_PARALLEL, sl.MIN_PARALLEL):
        args = list(BASE[func])
        args[first] = args[second] = p
        result = func(*args)
        values = result if isinstance(result, tuple) else (result,)
        assert all(math.isfinite(v) for v in values)


def test_inverse_coordinate_guards_at_both_ends():
    a = sl.WGS84_A
    for index, name in ((0, "x"), (1, "y")):
        for value in (
            math.nextafter(-1000 * a, -math.inf),
            math.nextafter(1000 * a, math.inf),
        ):
            args = list(BASE[sl.lcc_inverse])
            args[index] = value
            with pytest.raises(ValueError, match=name):
                sl.lcc_inverse(*args)

    # These are inside the coordinate guard and inverse to ordinary points.
    for lat, lon in ((-60, -96), (85, -96), (23, -156), (23, -36)):
        x, y = sl.lcc_forward(lat, lon, 33, 45, 23, -96)
        assert abs(x) < 1000 * a and abs(y) < 1000 * a
        assert sl.lcc_inverse(x, y, 33, 45, 23, -96) == pytest.approx(
            (lat, lon), abs=1e-9, rel=0
        )

    # At the exact coordinate limits the range guard accepts the value;
    # geometry then refuses it as beyond the cone's pole or latitude domain.
    for index in (0, 1):
        for value in (-1000 * a, 1000 * a):
            args = list(BASE[sl.lcc_inverse])
            args[index] = value
            with pytest.raises(ValueError, match="pole|latitude"):
                sl.lcc_inverse(*args)


def test_real_fractions_are_accepted_and_defaults_are_the_pinned_constants():
    assert sl.lcc_forward(35, -75, 33, 45, 23, -96) == sl.lcc_forward(
        35, -75, 33, 45, 23, -96, sl.WGS84_A, sl.WGS84_F
    )
    assert sl.lcc_scale(35, 33, 45) == sl.lcc_scale(
        35, 33, 45, sl.WGS84_A, sl.WGS84_F
    )
    assert sl.lcc_inverse(0, 0, 33, 45, 23, -96) == sl.lcc_inverse(
        0, 0, 33, 45, 23, -96, sl.WGS84_A, sl.WGS84_F
    )
    # Fraction(1, 2) is a real, and its float conversion is exactly 0.5.
    assert sl.lcc_forward(Fraction(1, 2), 0, 33, 45, 23, 0) == sl.lcc_forward(
        0.5, 0, 33, 45, 23, 0
    )
