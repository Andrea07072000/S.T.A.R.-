"""Refusals and inclusive range limits for every public star_mercator argument.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release."""
import math
from fractions import Fraction

import pytest

import star_mercator as sm


BAD = [
    float("nan"), float("inf"), float("-inf"),
    10 ** 400, -(10 ** 400), 1e300, -1e300,
    True, False, "10", None, 1j, [10.0], (1.0,),
]

# Each baseline is valid, with every positional argument explicitly supplied.
CASES = [
    (sm.mercator_forward, (20.0, 30.0, 10.0, 25.0, 6378137.0, 0.02)),
    (sm.mercator_inverse, (1000.0, 2000.0, 10.0, 25.0, 6378137.0, 0.02)),
    (sm.mercator_scale, (20.0, 25.0, 0.02)),
    (sm.web_mercator_forward, (20.0, 30.0)),
    (sm.web_mercator_inverse, (1000.0, 2000.0)),
]


def test_pinned_hostile_set_and_constants():
    assert len(BAD) == 14
    assert sm.__version__ == "0.1.0"
    assert sm.__all__ == [
        "mercator_forward", "mercator_inverse", "mercator_scale",
        "web_mercator_forward", "web_mercator_inverse", "WGS84_A", "WGS84_F",
    ]
    assert sm.WGS84_A == 6378137.0
    assert sm.WGS84_F == 1 / 298.257223563
    assert sm.MAX_LAT == 89.5
    assert sm.MAX_TS == 80.0


@pytest.mark.parametrize("func,args", CASES, ids=lambda case: (
    case.__name__ if callable(case) else None
))
def test_every_argument_refuses_every_hostile_value(func, args):
    result = func(*args)
    values = result if isinstance(result, tuple) else (result,)
    assert all(type(value) is float and math.isfinite(value)
               for value in values)
    for bad in BAD:
        for index in range(len(args)):
            changed = list(args)
            changed[index] = bad
            with pytest.raises(ValueError):
                func(*changed)


# Endpoints are inclusive. nextafter supplies the nearest float on either
# side, rather than a decimal offset that could round back to the endpoint.
LIMITS = [
    (sm.mercator_forward, (20., 30., 10., 25., 6378137., .02), 0,
     -89.5, 89.5, "latitude"),
    (sm.mercator_forward, (20., 30., 10., 25., 6378137., .02), 1,
     -180., 180., "longitude"),
    (sm.mercator_forward, (20., 30., 10., 25., 6378137., .02), 2,
     -180., 180., "central meridian"),
    (sm.mercator_forward, (20., 30., 10., 25., 6378137., .02), 3,
     -80., 80., "true scale"),
    (sm.mercator_forward, (20., 30., 10., 25., 6378137., .02), 4,
     1e3, 1e9, "a"),
    (sm.mercator_forward, (20., 30., 10., 25., 6378137., .02), 5,
     0., .1, "f"),
    (sm.mercator_inverse, (1000., 2000., 10., 25., 6378137., .02), 2,
     -180., 180., "central meridian"),
    (sm.mercator_inverse, (1000., 2000., 10., 25., 6378137., .02), 3,
     -80., 80., "true scale"),
    (sm.mercator_inverse, (1000., 2000., 10., 25., 6378137., .02), 4,
     1e3, 1e9, "a"),
    (sm.mercator_inverse, (1000., 2000., 10., 25., 6378137., .02), 5,
     0., .1, "f"),
    (sm.mercator_scale, (20., 25., .02), 0,
     -89.5, 89.5, "latitude"),
    (sm.mercator_scale, (20., 25., .02), 1,
     -80., 80., "true scale"),
    (sm.mercator_scale, (20., 25., .02), 2,
     0., .1, "f"),
    (sm.web_mercator_forward, (20., 30.), 0,
     -89.5, 89.5, "latitude"),
    (sm.web_mercator_forward, (20., 30.), 1,
     -180., 180., "longitude"),
]


@pytest.mark.parametrize("func,args,index,low,high,message", LIMITS)
def test_input_limits_both_ends(func, args, index, low, high, message):
    for value in (
        low, math.nextafter(low, high),
        math.nextafter(high, low), high,
    ):
        changed = list(args)
        changed[index] = value
        result = func(*changed)
        values = result if isinstance(result, tuple) else (result,)
        assert all(math.isfinite(v) for v in values)
        if func is sm.mercator_inverse:
            assert -89.5 <= result[0] <= 89.5
            assert -180 <= result[1] < 180
        elif func is sm.mercator_scale:
            assert result > 0
    for value in (
        math.nextafter(low, -math.inf),
        math.nextafter(high, math.inf),
    ):
        changed = list(args)
        changed[index] = value
        with pytest.raises(ValueError, match=message):
            func(*changed)


@pytest.mark.parametrize("func", [sm.mercator_inverse, sm.web_mercator_inverse])
def test_inverse_x_and_y_limits_both_ends(func):
    if func is sm.web_mercator_inverse:
        extra = ()
        ak0 = sm.WGS84_A
        e = 0.0
    else:
        # Test a nonzero true-scale latitude and nonzero eccentricity so
        # neither factor of the inverse bounds can be silently omitted.
        extra = (17.0, 40.0, 7000000.0, 0.02)
        a, f, t = extra[2], extra[3], math.radians(extra[1])
        e = math.sqrt(f * (2 - f))
        ak0 = a * math.cos(t) / math.sqrt(
            1 - (e * math.sin(t)) ** 2
        )

    # A half-turn has |x|=pi*a*k0. At MAX_LAT, the isometric latitude is
    # asinh(tan(phi))-e*atanh(e*sin(phi)); inverse y permits a 1e-12
    # relative rounding margin around its image.
    x_limit = math.pi * ak0
    phi = math.radians(89.5)
    y_limit = ak0 * (
        math.asinh(math.tan(phi)) - e * math.atanh(e * math.sin(phi))
    ) * (1 + 1e-12)

    for axis, bound, message in (
        (0, x_limit, "x"), (1, y_limit, "y")
    ):
        for sign in (-1, 1):
            endpoint = sign * bound
            inside = math.nextafter(endpoint, 0.0)
            outside = math.nextafter(endpoint, sign * math.inf)
            for value in (inside, endpoint):
                args = [0.0, 0.0]
                args[axis] = value
                lat, lon = func(*args, *extra)
                assert math.isfinite(lat) and math.isfinite(lon)
                assert -180 <= lon < 180
                if axis == 0:
                    assert abs(lat) < 1e-12
                else:
                    assert abs(lat - sign * 89.5) < 1e-9
            args = [0.0, 0.0]
            args[axis] = outside
            with pytest.raises(ValueError, match=message):
                func(*args, *extra)

    # The positive x endpoint is the same wrapped longitude as the negative
    # endpoint; neither inverse may return +180.
    lon0 = extra[0] if extra else 0.0                       # half a turn from the central meridian, reduced to [-180, 180)
    want = (lon0 + 180.0 + 180.0) % 360.0 - 180.0
    assert func(x_limit, 0.0, *extra)[1] == pytest.approx(want, abs=1e-12)
    assert func(-x_limit, 0.0, *extra)[1] == pytest.approx(want, abs=1e-12)


def test_inverses_refuse_far_outside_either_coordinate():
    for func in (sm.mercator_inverse, sm.web_mercator_inverse):
        with pytest.raises(ValueError, match="x"):
            func(1e9, 0)
        with pytest.raises(ValueError, match="x"):
            func(-1e9, 0)
        with pytest.raises(ValueError, match="y"):
            func(0, 1e9)
        with pytest.raises(ValueError, match="y"):
            func(0, -1e9)


def test_real_non_float_inputs_are_accepted():
    # A half turn is pi radians, so spherical x at 180 degrees wraps to
    # -pi*a; Fraction exercises the documented real-number path.
    x, y = sm.mercator_forward(
        Fraction(0), Fraction(180), Fraction(0),
        Fraction(0), Fraction(6378137), Fraction(0),
    )
    assert x == pytest.approx(-math.pi * 6378137, abs=1e-8)
    assert y == 0.0
    assert sm.mercator_inverse(
        Fraction(0), Fraction(0), Fraction(0),
        Fraction(0), Fraction(6378137), Fraction(0),
    ) == (0.0, 0.0)
    assert sm.mercator_scale(Fraction(0), Fraction(0), Fraction(0)) == 1.0
    assert sm.web_mercator_forward(Fraction(0), Fraction(0)) == (0.0, 0.0)
    assert sm.web_mercator_inverse(Fraction(0), Fraction(0)) == (0.0, 0.0)
