"""Refusals of star_horizon with hostile inputs (NaN, inf, huge integers, booleans, text, values outside their ranges).
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release."""
import math
from fractions import Fraction

import pytest

import star_horizon as sh

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "10", None, 1j, [10.0], (1.0,)]
G = (10.0, 20.0, 30.0)


def _all_finite(values):
    if isinstance(values, tuple):
        return all(type(v) is float and math.isfinite(v) for v in values)
    return type(values) is float and math.isfinite(values)


def test_the_hostile_set_and_public_constants_are_pinned():
    assert len(BAD) == 14 and sh.__version__ == "0.1.0"
    assert sh.__all__ == ["hadec_to_azel", "azel_to_hadec", "parallactic_angle_deg"]
    assert sh.TINY == 1e-15


@pytest.mark.parametrize("f", [sh.hadec_to_azel, sh.azel_to_hadec, sh.parallactic_angle_deg], ids=lambda f: f.__name__)
def test_every_argument_of_every_public_function_refuses_hostile_values(f):
    assert _all_finite(f(*G))
    for bad in BAD:
        for i in range(3):
            args = list(G)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("args, why", [
    ((360.0000001, 20.0, 30.0), "hour angle"),
    ((-360.0000001, 20.0, 30.0), "hour angle"),
    ((10.0, 90.0000001, 30.0), "declination"),
    ((10.0, -90.0000001, 30.0), "declination"),
    ((10.0, 20.0, 90.0000001), "latitude"),
    ((10.0, 20.0, -90.0000001), "latitude"),
])
def test_hadec_to_azel_angles_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        sh.hadec_to_azel(*args)


@pytest.mark.parametrize("args, why", [
    ((360.0000001, 20.0, 30.0), "azimuth"),
    ((-360.0000001, 20.0, 30.0), "azimuth"),
    ((10.0, 90.0000001, 30.0), "elevation"),
    ((10.0, -90.0000001, 30.0), "elevation"),
    ((10.0, 20.0, 90.0000001), "latitude"),
    ((10.0, 20.0, -90.0000001), "latitude"),
])
def test_azel_to_hadec_angles_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        sh.azel_to_hadec(*args)


@pytest.mark.parametrize("args, why", [
    ((360.0000001, 20.0, 30.0), "hour angle"),
    ((-360.0000001, 20.0, 30.0), "hour angle"),
    ((10.0, 90.0000001, 30.0), "declination"),
    ((10.0, -90.0000001, 30.0), "declination"),
    ((10.0, 20.0, 90.0000001), "latitude"),
    ((10.0, 20.0, -90.0000001), "latitude"),
])
def test_parallactic_angle_angles_out_of_range(args, why):
    with pytest.raises(ValueError, match=why):
        sh.parallactic_angle_deg(*args)


def test_limits_are_accepted_and_results_stay_in_range():
    # Hour angle / azimuth at the edges of [-360, 360].
    for angle in (-360.0, 360.0, -359.9999999999, 359.9999999999):
        az, el = sh.hadec_to_azel(angle, 0.0, 0.0)
        assert 0.0 <= az < 360.0 and -90.0 <= el <= 90.0
        assert type(az) is float and type(el) is float
        ha, dec = sh.azel_to_hadec(angle, 0.0, 0.0)
        assert -180.0 < ha <= 180.0 and -90.0 <= dec <= 90.0
    # Declination / elevation / latitude at the edges of [-90, 90].
    for x in (90.0, -90.0, 89.9999999999, -89.9999999999):
        assert _all_finite(sh.hadec_to_azel(0.0, x, 45.0))
        assert _all_finite(sh.azel_to_hadec(0.0, x, 45.0))
        assert _all_finite(sh.parallactic_angle_deg(0.0, x, 45.0))
        assert _all_finite(sh.hadec_to_azel(0.0, 0.0, x))
        assert _all_finite(sh.azel_to_hadec(0.0, 0.0, x))
        assert _all_finite(sh.parallactic_angle_deg(0.0, 0.0, x))
    # Non-float reals are accepted.
    assert sh.hadec_to_azel(Fraction(1, 2), 1, 2) == sh.hadec_to_azel(0.5, 1.0, 2.0)
