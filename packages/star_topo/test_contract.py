"""Refusals of star_topo with hostile inputs (NaN, inf, huge integers, booleans, text, out-of-range angles).
Verifies: R4 (README).

Every function either returns three finite floats or raises ValueError: never NaN, never another exception."""
import math

import pytest

import star_topo as t

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "1", None, 1j, [1.0], (1.0,)]
GOOD6 = (4000000.0, 300000.0, 5000000.0, 55.0, 5.0, 200.0)
FUNCS = {"ecef_to_enu": (t.ecef_to_enu, GOOD6), "enu_to_ecef": (t.enu_to_ecef, (10.0, 20.0, 30.0, 55.0, 5.0, 200.0)),
         "ecef_to_aer": (t.ecef_to_aer, GOOD6), "aer_to_ecef": (t.aer_to_ecef, (10.0, 20.0, 30.0, 55.0, 5.0, 200.0)),
         "enu_to_aer": (t.enu_to_aer, (10.0, 20.0, 30.0)), "aer_to_enu": (t.aer_to_enu, (10.0, 20.0, 30.0))}


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and sorted(FUNCS) == sorted(t.__all__) and len(t.__all__) == 6
    assert t.A == 6378137.0 and t.F == 1 / 298.257223563 and abs(t.B - 6356752.314245179) < 1e-9
    assert abs(t.E2 - 0.0066943799901413165) < 1e-18 and t.__version__ == "0.1.0"


@pytest.mark.parametrize("name", sorted(FUNCS))
def test_every_argument_refuses_every_hostile_value(name):
    f, good = FUNCS[name]
    assert all(isinstance(v, float) and math.isfinite(v) for v in f(*good))
    for i in range(len(good)):
        for bad in BAD:
            args = list(good)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("lat, lon, h", [(90.0000001, 0, 0), (-90.0000001, 0, 0), (0, 360.0000001, 0), (0, -360.0000001, 0),
                                         (0, 0, -6356752.314245179), (0, 0, -7e6), (0, 0, -1e299)])
def test_an_impossible_site_is_refused(lat, lon, h):
    for f in (t.ecef_to_enu, t.enu_to_ecef, t.ecef_to_aer):
        with pytest.raises(ValueError):
            f(1.0, 2.0, 3.0, lat, lon, h)
    with pytest.raises(ValueError):
        t.aer_to_ecef(1.0, 2.0, 3.0, lat, lon, h)


def test_the_limits_themselves_are_accepted():
    for lat, lon, h in ((90.0, 360.0, -6356752.0), (-90.0, -360.0, 1e9), (0, 0, 0)):
        assert all(map(math.isfinite, t.ecef_to_enu(1.0, 2.0, 3.0, lat, lon, h)))
    for az, el in ((360.0, 90.0), (-360.0, -90.0), (0, 0)):
        assert all(map(math.isfinite, t.aer_to_enu(az, el, 1e-300)))
    assert t.aer_to_enu(0, 0, 5) == (0.0, 5.0, 0.0) and t.enu_to_aer(0, 3, 4)[2] == 5.0     # integers are numbers


@pytest.mark.parametrize("az, el, rng", [(0, 90.0000001, 1), (0, -90.0000001, 1), (360.0000001, 0, 1), (-360.0000001, 0, 1),
                                         (0, 0, 0.0), (0, 0, -0.0), (0, 0, -1.0), (0, 0, -1e-300)])
def test_an_impossible_direction_or_range_is_refused(az, el, rng):
    with pytest.raises(ValueError):
        t.aer_to_enu(az, el, rng)
    with pytest.raises(ValueError):
        t.aer_to_ecef(az, el, rng, 10.0, 20.0, 30.0)


def test_a_target_on_the_site_has_no_direction():
    with pytest.raises(ValueError, match="coincides"):
        t.enu_to_aer(0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="coincides"):
        t.enu_to_aer(-0.0, 0.0, -0.0)
    site = t.enu_to_ecef(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="coincides"):
        t.ecef_to_aer(*site, 0.0, 0.0, 0.0)
    assert t.enu_to_aer(0.0, 0.0, 5e-324) == (0.0, 90.0, 5e-324) and t.enu_to_aer(0.0, 0.0, -5e-324)[1] == -90.0


def test_an_overflowing_result_is_refused_not_returned():
    big = 9e299
    for f, args in ((t.ecef_to_enu, (big, big, big, 45.0, 45.0, 0.0)), (t.enu_to_ecef, (big, big, big, 45.0, 45.0, 0.0)),
                    (t.enu_to_aer, (big, big, big)), (t.ecef_to_aer, (big, -big, big, -45.0, 45.0, 0.0))):
        try:
            out = f(*args)
        except ValueError:
            continue
        assert all(map(math.isfinite, out))
    assert t._out(1.0, 2.0) == (1.0, 2.0)
    for bad in (NAN, INF, -INF):
        with pytest.raises(ValueError, match="out of range"):
            t._out(1.0, bad)
