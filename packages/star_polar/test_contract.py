"""Refusals and exact boundary contracts of every public star_polar function.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release."""
import math
from fractions import Fraction

import pytest

import star_polar as sp


BAD = [
    float("nan"), float("inf"), float("-inf"), 10 ** 400, -(10 ** 400),
    1e300, -1e300, True, False, "10", None, 1j, [10.0], (1.0,),
]


def test_pinned_constants_and_hostile_set():
    assert len(BAD) == 14
    assert sp.__version__ == "0.1.0"
    assert sp.__all__ == [
        "ps_forward", "ps_inverse", "ps_scale", "ups_forward",
        "ups_inverse", "WGS84_A", "WGS84_F",
    ]
    assert sp.WGS84_A == 6378137.0
    assert sp.WGS84_F == 1 / 298.257223563
    assert sp.K0_UPS == 0.994
    assert sp.FALSE_UPS == 2000000.0
    assert sp.FAR_SIDE == 60.0


@pytest.mark.parametrize(
    "function,good,indices",
    [
        (sp.ps_forward, (60, 25, "N", -10, 71, 1, 6378137, 0), (0, 1, 3, 4, 5, 6, 7)),
        (sp.ps_inverse, (1000, -2000, "N", -10, 71, 1, 6378137, 0), (0, 1, 3, 4, 5, 6, 7)),
        (sp.ps_scale, (60, "N", 71, 1, 6378137, 0), (0, 2, 3, 4, 5)),
        (sp.ups_forward, (70, 25), (0, 1)),
        (sp.ups_inverse, ("N", 2001000, 1998000), (1, 2)),
    ],
    ids=lambda row: row.__name__ if callable(row) else None,
)
def test_every_numeric_argument_refuses_every_hostile_value(function, good, indices):
    result = function(*good)
    assert all(math.isfinite(v) for v in (result if isinstance(result, tuple) else (result,)) if isinstance(v, float))
    for index in indices:
        for bad in BAD:
            if bad is None and good[index] == 71:
                continue                                    # None is the documented 'true scale at the pole'
            args = list(good)
            args[index] = bad
            with pytest.raises(ValueError):
                function(*args)


@pytest.mark.parametrize(
    "function,good,index",
    [
        (sp.ps_forward, (60, 25, "N"), 2),
        (sp.ps_inverse, (1000, -2000, "N"), 2),
        (sp.ps_scale, (60, "N"), 1),
        (sp.ups_inverse, ("N", 2001000, 1998000), 0),
    ],
)
def test_every_pole_argument_refuses_hostile_and_unknown_values(function, good, index):
    for bad in BAD + ["n", "s", "", "North", 1, b"N"]:
        args = list(good)
        args[index] = bad
        with pytest.raises(ValueError, match="pole"):
            function(*args)


@pytest.mark.parametrize(
    "name,lower,upper,good,call",
    [
        ("k0", 0.5, 2.0, 1.0, lambda v: sp.ps_forward(60, 25, "N", k0=v)),
        ("a", 1e3, 1e9, 6378137.0, lambda v: sp.ps_forward(60, 25, "N", a=v)),
        ("f", 0.0, 0.1, 0.003, lambda v: sp.ps_forward(60, 25, "N", f=v)),
    ],
)
def test_setup_limits_are_inclusive_and_outside_values_refused(name, lower, upper, good, call):
    for value in (lower, math.nextafter(lower, upper),
                  math.nextafter(upper, lower), upper):
        result = call(value)
        assert len(result) == 2 and all(math.isfinite(v) for v in result)
    for value in (math.nextafter(lower, -math.inf),
                  math.nextafter(upper, math.inf)):
        with pytest.raises(ValueError, match=name):
            call(value)
    assert all(math.isfinite(v) for v in call(good))


def test_setup_limits_apply_to_inverse_and_scale_too():
    for keyword, low, high in (("k0", 0.5, 2.0), ("a", 1e3, 1e9),
                               ("f", 0.0, 0.1)):
        for function, args in ((sp.ps_inverse, (100, -200, "N")),
                               (sp.ps_scale, (60, "N"))):
            for value in (low, high):
                assert function(*args, **{keyword: value}) is not None
            for value in (math.nextafter(low, -math.inf),
                          math.nextafter(high, math.inf)):
                with pytest.raises(ValueError, match=keyword):
                    function(*args, **{keyword: value})


def test_latitude_endpoints_and_far_side_in_both_directions():
    for pole, sign in (("N", 1), ("S", -1)):
        for latitude in (sign * 90, sign * 60, -sign * 60):
            xy = sp.ps_forward(latitude, 0, pole, f=0)
            assert all(math.isfinite(v) for v in xy)
        for latitude in (math.nextafter(sign * 90, 0),
                         math.nextafter(-sign * 60, 0)):
            assert all(math.isfinite(v) for v in sp.ps_forward(latitude, 0, pole))
        with pytest.raises(ValueError, match="latitude"):
            sp.ps_forward(sign * 90.000000001, 0, pole)
        with pytest.raises(ValueError, match="beyond"):
            sp.ps_forward(-sign * 60.000000001, 0, pole)
        for function in (sp.ps_forward, sp.ps_scale):
            with pytest.raises(ValueError, match="beyond"):
                function(-sign * 61, *(((0, pole) if function is sp.ps_forward else (pole,))))
    assert sp.ups_forward(90, 0)[0] == "N"
    assert sp.ups_forward(-90, 0)[0] == "S"
    for latitude in (-90.000000001, 90.000000001):
        with pytest.raises(ValueError, match="latitude"):
            sp.ups_forward(latitude, 0)


def test_inverse_far_side_boundary_is_inclusive():
    a = 1000.0
    # Sphere with pole true scale: rho(phi) = 2a tan(45 - phi/2).
    # phi = -60 lies exactly on the far-side boundary; phi = -61 is beyond it.
    for pole, sign in (("N", 1), ("S", -1)):
        for phi in (-60, math.nextafter(-60, 0)):
            rho = 2 * a * math.tan(math.radians(45 - phi / 2))
            lat, lon = sp.ps_inverse(0, -sign * rho, pole, a=a, f=0)
            assert lat == pytest.approx(sign * phi, rel=0, abs=1e-12)
            assert lon == pytest.approx(0, rel=0, abs=1e-12)
        rho = 2 * a * math.tan(math.radians(45 + 61 / 2))
        with pytest.raises(ValueError, match="beyond"):
            sp.ps_inverse(0, -sign * rho, pole, a=a, f=0)


def test_true_scale_latitude_sign_one_degree_and_ninety_degree_limits():
    for pole, sign in (("N", 1), ("S", -1)):
        for magnitude in (1, 1.000000001, 71, 89.999999999, 90):
            ts = sign * magnitude
            assert sp.ps_scale(ts, pole, ts) == pytest.approx(
                1, rel=0, abs=1e-13
            )
        for ts in (0, sign * 0.5, sign * 0.999999999, -sign * 1,
                   -sign * 71, -sign * 90):
            with pytest.raises(ValueError, match="true scale"):
                sp.ps_scale(sign * 60, pole, ts)
        for ts in (-90.000000001, 90.000000001):
            with pytest.raises(ValueError, match="latitude of true scale"):
                sp.ps_scale(sign * 60, pole, ts)


def test_longitude_and_meridian_limits_in_forward_and_inverse():
    # At longitude -180 or +180 the spherical 60-degree point is on
    # the opposite ray: x = 0, y = +rho for the north map.
    rho = 2 * 1000 * math.tan(math.radians(15))
    for longitude in (-180, math.nextafter(-180, 0),
                      math.nextafter(180, 0), 180):
        x, y = sp.ps_forward(60, longitude, "N", a=1000, f=0)
        assert abs(x) < 1e-10
        assert y == pytest.approx(rho, rel=0, abs=1e-11)
        lat, lon = sp.ps_inverse(0, -rho, "N", longitude, a=1000, f=0)
        assert lat == pytest.approx(60, rel=0, abs=1e-12)
        assert -180.0 <= lon < 180.0 and abs((lon - longitude + 180.0) % 360.0 - 180.0) < 1e-12      # +180 comes back as -180
    for outside in (math.nextafter(-180, -math.inf),
                    math.nextafter(180, math.inf)):
        with pytest.raises(ValueError, match="longitude"):
            sp.ps_forward(60, outside, "N")
        with pytest.raises(ValueError, match="central meridian"):
            sp.ps_forward(60, 0, "N", outside)
        with pytest.raises(ValueError, match="central meridian"):
            sp.ps_inverse(0, -1000, "N", outside)


def test_inverse_coordinate_limits_inclusive_on_both_axes():
    a = 1000.0
    # With f=0 and k0=2, C=4a. At either axial endpoint rho=10a;
    # latitude = 90 - 2 atan(rho/C), so the inverse remains within
    # the allowed far side even when both coordinates reach endpoints.
    for x in (-10 * a, 10 * a):
        for y in (-10 * a, 10 * a):
            latitude, longitude = sp.ps_inverse(x, y, "N", k0=2, a=a, f=0)
            rho = math.hypot(x, y)
            expected = 90 - 2 * math.degrees(math.atan(rho / (4 * a)))
            assert latitude == pytest.approx(expected, rel=0, abs=1e-12)
            assert longitude == pytest.approx(
                (math.degrees(math.atan2(x, -y)) + 180) % 360 - 180,
                rel=0, abs=1e-12,
            )
    for outside in (math.nextafter(-10 * a, -math.inf),
                    math.nextafter(10 * a, math.inf)):
        with pytest.raises(ValueError, match=r"x \(m\)"):
            sp.ps_inverse(outside, 0, "N", k0=2, a=a, f=0)
        with pytest.raises(ValueError, match=r"y \(m\)"):
            sp.ps_inverse(0, outside, "N", k0=2, a=a, f=0)


def test_ups_input_limits_and_projected_coordinate_limits():
    for axis in ("easting", "northing"):
        for endpoint in (-1e8, 1e8):
            args = {"easting": 2000000, "northing": 2000000}
            args[axis] = endpoint
            # The UPS input endpoint passes its own guard, but its offset
            # exceeds the inverse projection's 10a coordinate limit.
            with pytest.raises(ValueError, match=r"[xy] \(m\)"):
                sp.ups_inverse("N", **args)
        for outside in (math.nextafter(-1e8, -math.inf),
                        math.nextafter(1e8, math.inf)):
            args = {"easting": 2000000, "northing": 2000000}
            args[axis] = outside
            with pytest.raises(ValueError, match=axis):
                sp.ups_inverse("N", **args)
    assert sp.ups_inverse("N", 2000000, 2000000) == (90.0, 0.0)
    assert sp.ups_inverse("S", 2000000, 2000000) == (-90.0, 0.0)


def test_real_numbers_are_accepted_and_defaults_use_wgs84():
    assert sp.ps_forward(Fraction(60), Fraction(25), "N") == sp.ps_forward(
        60, 25, "N", 0, None, 1, 6378137.0, 1 / 298.257223563
    )
    xy = sp.ps_forward(60, 25, "N")
    assert sp.ps_inverse(*xy, "N") == pytest.approx(
        sp.ps_inverse(*xy, "N", 0, None, 1, 6378137.0, 1 / 298.257223563),
        rel=0, abs=1e-12,
    )
    assert sp.ps_scale(60, "N") == sp.ps_scale(
        60, "N", None, 1, 6378137.0, 1 / 298.257223563
    )
