"""Refusals of star_coverage with hostile inputs (NaN, inf, huge integers, booleans, text, impossible geometry).
Verifies: R4 (README).

Every function returns a finite float or raises ValueError: never NaN from an arc-sine out of range."""
import math
from fractions import Fraction

import pytest

import star_coverage as c

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e150, -1e150, True, False, "1", None, 1j, [1.0], (1.0,)]
WITH_ELEV = (c.central_angle_deg, c.nadir_angle_deg, c.slant_range, c.coverage_fraction, c.footprint_area)


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and c.EARTH_RADIUS_KM == 6378.137 and c.__version__ == "0.1.0" and len(WITH_ELEV) == 5
    assert c.__all__ == ["central_angle_deg", "nadir_angle_deg", "slant_range", "coverage_fraction", "footprint_area", "elevation_deg"]


@pytest.mark.parametrize("f", WITH_ELEV + (c.elevation_deg,))
def test_every_argument_refuses_every_hostile_value(f):
    assert isinstance(f(800.0, 10.0), float) and math.isfinite(f(800.0, 10.0))
    for bad in BAD:
        with pytest.raises(ValueError):
            f(bad, 10.0)
        with pytest.raises(ValueError):
            f(800.0, bad)
        with pytest.raises(ValueError):
            f(800.0, 10.0, radius=bad)


@pytest.mark.parametrize("f", WITH_ELEV + (c.elevation_deg,))
def test_altitude_and_radius_must_be_positive(f):
    for h in (0, 0.0, -0.0, -1.0, -1e-300):
        with pytest.raises(ValueError, match="altitude must be positive"):
            f(h, 10.0)
    for r in (0, 0.0, -1.0):
        with pytest.raises(ValueError, match="radius must be positive"):
            f(800.0, 10.0, radius=r)
    for h in (1e-300, 1e-20):                                  # R / (R + h) rounds to 1: no geometry left
        with pytest.raises(ValueError, match="not resolvable"):
            f(h, 10.0)
    with pytest.raises(ValueError, match="not resolvable"):
        f(1e140, 10.0, radius=1e-200)


@pytest.mark.parametrize("f", WITH_ELEV)
def test_minimum_elevation_range(f):
    for e in (-1e-9, -10.0, 90.000001, 180.0):
        with pytest.raises(ValueError, match="minimum elevation"):
            f(800.0, e)
    assert math.isfinite(f(800.0, 0)) and math.isfinite(f(800.0, 90)) and f(800.0) == f(800.0, 0.0)
    assert f(Fraction(800), Fraction(10)) == f(800.0, 10.0)


def test_central_angle_range_for_elevation():
    for lam in (-1e-9, 180.000001, 360.0):
        with pytest.raises(ValueError, match="central angle"):
            c.elevation_deg(800.0, lam)
    assert -90.0 <= c.elevation_deg(800.0, 180) <= 90.0 and c.elevation_deg(800.0, 0) == 90.0


def test_results_stay_in_range_at_the_extremes():
    for h in (1e-6, 1e-3, 1.0, 1e3, 1e6, 1e9, 1e12):
        for e in (0.0, 1e-9, 45.0, 90.0 - 1e-9, 90.0):
            lam, eta, rho, frac = c.central_angle_deg(h, e), c.nadir_angle_deg(h, e), c.slant_range(h, e), c.coverage_fraction(h, e)
            assert 0.0 <= lam <= 90.0 and 0.0 <= eta <= 90.0 and 0.0 <= frac <= 0.5
            assert h * (1 - 1e-9) <= rho <= math.sqrt(h * (2 * 6378.137 + h)) * (1 + 1e-9)       # between altitude and horizon distance
    assert c.slant_range(1e-6) == pytest.approx(math.sqrt(2 * 6378.137 * 1e-6), rel=1e-6)        # a millimetre above the ground


def test_precision_is_kept_for_a_satellite_skimming_the_ground_and_for_one_far_away():
    # found by this contract: written with R + h the slant range at h = 1 mm was 1.7e-7 off, and an arc-sine gave
    # exactly 90 deg (coverage fraction above one half) at h = 1e12 km
    r = 6378.137
    for h in (1e-9, 1e-6, 1e-3):
        assert c.slant_range(h) == pytest.approx(math.sqrt(h) * math.sqrt(2 * r + h), rel=1e-14)
        assert c.slant_range(h, 90.0) == pytest.approx(h, rel=1e-14)
        assert math.radians(c.central_angle_deg(h)) == pytest.approx(math.sqrt(2 * h / r), rel=1e-6)
    far = c.central_angle_deg(1e12)
    assert far < 90.0 and 90.0 - far == pytest.approx(math.degrees(r / (r + 1e12)), rel=1e-6)
    assert c.coverage_fraction(1e12) < 0.5 and c.coverage_fraction(1e140) <= 0.5
    with pytest.raises(ValueError):
        c.footprint_area(800.0, 10.0, radius=10 ** 400)
    assert math.isfinite(c.footprint_area(9e149, 0.0, radius=9e149))                 # inputs are bounded: the area cannot overflow
