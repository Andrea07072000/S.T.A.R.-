"""Refusals of star_utm with a pinned hostile set, exact constants and both ends of each input range.
Standard library only.

Every public argument is exercised, including the exceptional allowed None in utm_forward's zone.
Some outer limits are shadowed by stricter projection limits: acceptance by those validation stages
is checked separately, rather than falsely claiming the complete projection accepts such points.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release."""
import math
from fractions import Fraction

import pytest

import star_utm as st

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400,
       1e300, -1e300, True, False, "10", None, 1j, [10.0], (1.0,)]
A = 6378137.0
F = 1 / 298.257223563
K = 0.9996

CALLS = [
    (st.tm_forward, (10.0, 3.0, 3.0, A, F, K),
     ("latitude", "longitude", "central meridian", "a ", "f", "k0")),
    (st.tm_inverse, (0.0, 0.0, 3.0, A, F, K),
     ("x ", "y ", "central meridian", "a ", "f", "k0")),
    (st.utm_zone, (3.0,), ("longitude",)),
    (st.utm_forward, (10.0, 3.0, 31), ("latitude", "longitude", "zone")),
    (st.utm_inverse, (31, "N", 500000.0, 0.0),
     ("zone", "hemisphere", "easting", "northing")),
]


def near_limits(lo, hi):
    return (lo, math.nextafter(lo, hi), math.nextafter(hi, lo), hi)


def outside_limits(lo, hi):
    return (math.nextafter(lo, -math.inf), math.nextafter(hi, math.inf))


def test_pinned_constants_and_public_surface():
    # These six constants are exact by definition, not rounded numerical reference results.
    assert st.WGS84_A == 6378137.0
    assert st.WGS84_F == 1 / 298.257223563
    assert st.K0_UTM == 0.9996
    assert st.FALSE_EASTING == 500000.0
    assert st.FALSE_NORTHING == 10000000.0
    assert st.MAX_DLON == 12.0
    assert st.__version__ == "0.1.0"
    assert st.__all__ == [
        "tm_forward", "tm_inverse", "utm_zone", "utm_forward", "utm_inverse",
        "WGS84_A", "WGS84_F",
    ]
    assert len(BAD) == 14
    assert math.isnan(BAD[0])
    assert BAD[1:3] == [math.inf, -math.inf]
    assert BAD[3:7] == [10 ** 400, -10 ** 400, 1e300, -1e300]
    assert BAD[7] is True and BAD[8] is False and BAD[10] is None
    assert BAD[9] == "10" and BAD[11:] == [1j, [10.0], (1.0,)]


@pytest.mark.parametrize("func,good,names", CALLS, ids=[c[0].__name__ for c in CALLS])
def test_every_public_argument_against_every_hostile_value(func, good, names):
    for i, name in enumerate(names):
        for bad in BAD:
            args = list(good)
            args[i] = bad
            if func is st.utm_forward and i == 2 and bad is None:
                # None is explicitly permitted here: longitude 3 is in zone 31.
                assert func(*args) == func(*good)
            else:
                with pytest.raises(ValueError, match=name):
                    func(*args)


@pytest.mark.parametrize("bad", [0, 61, -1, 31.0, 1.0, 60.0, Fraction(31), "31", b"31"])
def test_zone_requires_an_integral_non_boolean_in_range(bad):
    with pytest.raises(ValueError, match="zone"):
        st.utm_forward(0, 3, bad)
    with pytest.raises(ValueError, match="zone"):
        st.utm_inverse(bad, "N", 500000, 0)


@pytest.mark.parametrize("bad", ["n", "s", "", " N", "N ", "NS", b"N", 0, 1, ["N"], {"N"}])
def test_hemisphere_is_exactly_uppercase_n_or_s(bad):
    with pytest.raises(ValueError, match="hemisphere"):
        st.utm_inverse(31, bad, 500000, 0)


@pytest.mark.parametrize("z", [1, 2, 59, 60])
def test_zone_limits_and_their_neighbours_are_accepted(z):
    # The zone centre is 6*z-183; at its equatorial origin only false easting remains.
    centre = 6 * z - 183
    assert st.utm_forward(0, centre, z) == (z, "N", 500000.0, 0.0)
    for h, n in (("N", 0), ("S", 10000000)):
        assert st.utm_inverse(z, h, 500000, n) == (0.0, float(centre))


@pytest.mark.parametrize("func", [st.tm_forward, st.tm_inverse], ids=lambda f: f.__name__)
@pytest.mark.parametrize("index,lo,hi,why", [
    (3, 1000.0, 1e9, "a "),
    (4, 0.0, 0.1, "f"),
    (5, 0.5, 2.0, "k0"),
])
def test_ellipsoid_ranges_both_ends(func, index, lo, hi, why):
    good = [0.0, 0.0, 0.0, A, F, K]
    # At the origin every term vanishes for every admitted ellipsoid and scale.
    for value in near_limits(lo, hi):
        args = good.copy()
        args[index] = value
        assert func(*args) == (0.0, 0.0)
    for value in outside_limits(lo, hi):
        args = good.copy()
        args[index] = value
        with pytest.raises(ValueError, match=why):
            func(*args)


@pytest.mark.parametrize("value", near_limits(-90.0, 90.0))
def test_tm_latitude_limits_are_accepted(value):
    # On the spherical central meridian y=a*phi, including the limiting poles.
    result = st.tm_forward(value, 0, 0, 1000, 0, 1)
    assert result == pytest.approx((0, 1000 * math.radians(value)), rel=0, abs=3e-13)


@pytest.mark.parametrize("value", outside_limits(-90.0, 90.0))
def test_tm_latitude_just_outside_is_refused(value):
    with pytest.raises(ValueError, match="latitude"):
        st.tm_forward(value, 0, 0)


@pytest.mark.parametrize("value", near_limits(-80.0, 84.0))
def test_utm_latitude_limits_are_accepted(value):
    # Subtracting the false origin must recover the same central-meridian TM ordinate.
    x, y = st.tm_forward(value, 3, 3)
    z, h, e, n = st.utm_forward(value, 3)
    assert (z, h, e) == (31, "S" if value < 0 else "N", 500000 + x)
    assert n == (10000000 + y if value < 0 else y)
    assert st.utm_inverse(z, h, e, n) == pytest.approx((value, 3), rel=0, abs=1e-9)


@pytest.mark.parametrize("value", outside_limits(-80.0, 84.0) + (-80.0000001, 84.0000001))
def test_utm_latitude_just_outside_is_refused(value):
    with pytest.raises(ValueError, match="latitude"):
        st.utm_forward(value, 3)


@pytest.mark.parametrize("value", near_limits(-180.0, 180.0))
def test_longitude_and_central_meridian_limits_are_accepted(value):
    # Equal longitudes give zero difference even at the date line; inverse wraps +180 to -180.
    assert st.tm_forward(0, value, value) == (0.0, 0.0)
    wrapped = (value + 180) % 360 - 180
    assert st.tm_inverse(0, 0, value) == (0.0, wrapped)
    expected_z = 1 if value < 0 else 60
    assert st.utm_zone(value) == expected_z
    lon0 = 6 * expected_z - 183
    x, y = st.tm_forward(0, value, lon0)
    assert st.utm_forward(0, value) == (expected_z, "N", 500000 + x, y)
    assert st.utm_forward(0, value, expected_z) == (expected_z, "N", 500000 + x, y)


@pytest.mark.parametrize("value", outside_limits(-180.0, 180.0))
def test_longitude_and_central_meridian_just_outside_are_refused(value):
    for func, args, why in (
        (st.tm_forward, (0, value, 0), "longitude"),
        (st.tm_forward, (0, 0, value), "central meridian"),
        (st.tm_inverse, (0, 0, value), "central meridian"),
        (st.utm_zone, (value,), "longitude"),
        (st.utm_forward, (0, value), "longitude"),
        (st.utm_forward, (0, value, 31), "longitude"),
    ):
        with pytest.raises(ValueError, match=why):
            func(*args)


@pytest.mark.parametrize("sign", [-1, 1])
def test_forward_difference_limits_including_date_line(sign):
    # On the spherical equator x=a*atanh(sin(lambda)), y=0.
    for delta in (11.9999999, 12.0):
        expected = 1000 * math.atanh(math.sin(math.radians(sign * delta)))
        for lon0 in (0, sign * 179):
            lon = (lon0 + sign * delta + 180) % 360 - 180
            assert st.tm_forward(0, lon, lon0, 1000, 0, 1) == pytest.approx(
                (expected, 0), rel=0, abs=1e-12)
    for delta in (12.0000001, 12.0001, 180.0):
        with pytest.raises(ValueError, match="central meridian"):
            st.tm_forward(0, sign * delta, 0)
    # Forced zone 31 is centred at 3 degrees, so its allowed interval is [-9,15].
    lon = 3 + sign * 12
    x, y = st.tm_forward(0, lon, 3)
    assert st.utm_forward(0, lon, 31) == (31, "N", 500000 + x, y)
    with pytest.raises(ValueError, match="central meridian"):
        st.utm_forward(0, 3 + sign * 12.0001, 31)


def test_inverse_difference_exact_boundary_and_adjacent_float():
    # Sphere, equator: lambda=atan(sinh(x/a)). A power-of-two radius introduces no
    # division rounding. Locate a floating x whose independently calculated lambda is
    # exactly 12 degrees, so equality is tested without assuming transcendental rounding.
    a = 1024.0
    centre = a * math.atanh(math.sin(math.radians(12)))
    candidates = [centre]
    lower = upper = centre
    for _ in range(32):
        lower = math.nextafter(lower, -math.inf)
        upper = math.nextafter(upper, math.inf)
        candidates.extend((lower, upper))
    equal = [x for x in candidates
             if math.degrees(math.atan2(math.sinh(x / a), 1)) == 12.0]
    assert equal, "the independently constructed floating-point boundary must exist"
    inside = min(equal)
    outside = math.nextafter(max(equal), math.inf)
    assert math.degrees(math.atan2(math.sinh(outside / a), 1)) > 12
    for sign in (-1, 1):
        assert st.tm_inverse(sign * inside, 0, 0, a, 0, 1) == (0.0, sign * 12.0)
        with pytest.raises(ValueError, match="central meridian"):
            st.tm_inverse(sign * outside, 0, 0, a, 0, 1)
        x = sign * a * math.atanh(math.sin(math.radians(11.9999)))
        assert st.tm_inverse(x, 0, 0, a, 0, 1) == pytest.approx(
            (0, sign * 11.9999), rel=0, abs=3e-14)


@pytest.mark.parametrize("a,k", [(1000.0, 0.5), (A, K), (1e9, 2.0)])
@pytest.mark.parametrize("sign", [-1, 1])
def test_inverse_x_and_y_validation_limits_are_not_confused_with_projection_limits(a, k, sign):
    # At x=0.25*ak on the sphere, lambda=atan(sinh(.25)) exceeds 12 degrees.
    # At y=1.6*ak, xi=1.6 exceeds pi/2. Thus the range endpoints pass _real but
    # are necessarily refused by later geometry guards; just outside must fail _real.
    scale = a * k
    for label, limit, later in (("x", 0.25 * scale, "central meridian"),
                                ("y", 1.6 * scale, "pole")):
        for magnitude in (math.nextafter(limit, 0), limit):
            x, y = (sign * magnitude, 0) if label == "x" else (0, sign * magnitude)
            with pytest.raises(ValueError, match=later):
                st.tm_inverse(x, y, 0, a, 0, k)
        value = sign * math.nextafter(limit, math.inf)
        x, y = (value, 0) if label == "x" else (0, value)
        with pytest.raises(ValueError, match=label + " "):
            st.tm_inverse(x, y, 0, a, 0, k)


@pytest.mark.parametrize("sign", [-1, 1])
def test_inverse_pole_guard_at_and_either_side(sign):
    # For f=0, beta=0 and R=a. With a=1024, y/a=pi/2 exactly at this boundary.
    a = 1024.0
    pole = a * (math.pi / 2)
    for y in (math.nextafter(pole, 0), pole):
        lat, lon = st.tm_inverse(0, sign * y, 3, a, 0, 1)
        assert lat == pytest.approx(sign * math.degrees(y / a), rel=0, abs=2e-14)
        assert lon == 3.0
    with pytest.raises(ValueError, match="pole"):
        st.tm_inverse(0, sign * math.nextafter(pole, math.inf), 3, a, 0, 1)
    with pytest.raises(ValueError, match="pole"):
        st.tm_inverse(0, sign * 1.0005e7, 3)


@pytest.mark.parametrize("hemisphere", ["N", "S"])
def test_utm_outer_coordinate_ranges_and_normalization(monkeypatch, hemisphere):
    # The easting interval [-1.1e6,2.1e6] includes values outside TM's tighter x
    # interval. Isolate this outer validation stage with an asserting downstream spy.
    calls = []

    def inverse_spy(x, y, lon0):
        calls.append((x, y, lon0))
        return (0.0, lon0)

    monkeypatch.setattr(st, "tm_inverse", inverse_spy)
    for e in near_limits(-1.1e6, 2.1e6):
        for n in near_limits(0.0, 10000000.0):
            calls.clear()
            assert st.utm_inverse(31, hemisphere, e, n) == (0.0, 3.0)
            # Removing the false origin is subtraction, with northing translated only for S.
            assert calls == [(e - 500000, n - 10000000 if hemisphere == "S" else n, 3.0)]
    for e in outside_limits(-1.1e6, 2.1e6):
        calls.clear()
        with pytest.raises(ValueError, match="easting"):
            st.utm_inverse(31, hemisphere, e, 0)
        assert calls == []
    for n in outside_limits(0.0, 10000000.0):
        calls.clear()
        with pytest.raises(ValueError, match="northing"):
            st.utm_inverse(31, hemisphere, 500000, n)
        assert calls == []


def test_actual_utm_outer_endpoints_reach_the_stricter_tm_guards():
    # +/-1600000 from the false easting exceeds 0.25*A*K.
    for e in (-1.1e6, 2.1e6):
        with pytest.raises(ValueError, match="x "):
            st.utm_inverse(31, "N", e, 0)
    # Ten million metres from the equator exceeds the WGS84 projected quarter meridian.
    for h, n in (("N", 10000000), ("S", 0)):
        with pytest.raises(ValueError, match="pole"):
            st.utm_inverse(31, h, 500000, n)
    # The other hemisphere/end combinations are exactly the equatorial origin.
    assert st.utm_inverse(31, "N", 500000, 0) == (0.0, 3.0)
    assert st.utm_inverse(31, "S", 500000, 10000000) == (0.0, 3.0)


def test_real_numbers_are_converted_but_booleans_are_not_numbers_here():
    # Fraction is a Real: converting these binary-exact fractions changes no input value.
    args = (Fraction(1, 2), Fraction(13, 4), Fraction(3), Fraction(1000),
            Fraction(0), Fraction(1))
    assert st.tm_forward(*args) == st.tm_forward(*(float(v) for v in args))
    assert st.tm_inverse(Fraction(0), Fraction(0), Fraction(3)) == (0.0, 3.0)
    assert st.utm_zone(Fraction(3)) == 31
    assert st.utm_forward(Fraction(0), Fraction(3)) == (31, "N", 500000.0, 0.0)
    assert st.utm_inverse(31, "N", Fraction(500000), Fraction(0)) == (0.0, 3.0)
