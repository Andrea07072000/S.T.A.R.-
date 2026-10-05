"""References: Vallado (4th ed.) Example 3-5, 1992 Aug 20 12:14:00 UT1 -> GMST 152.578787810 deg, LST at 104 deg W
48.578787810 deg; IAU 1982 at J2000.0 12h UT1 = 280.46061837 deg (18h41m50.54841s)."""
import math

import pytest

from star_sidereal import gmst82_deg, lst_deg

JD_1992 = 2448854.5           # 1992 Aug 20 0h
FRAC = (12 + 14 / 60) / 24


def test_vallado_example_3_5():
    assert abs(gmst82_deg(JD_1992, FRAC) - 152.578787810) < 1e-7
    assert abs(lst_deg(JD_1992, FRAC, -104.0) - 48.578787810) < 1e-7


def test_value_at_j2000_noon():
    assert abs(gmst82_deg(2451545.0, 0.0) - 280.46061837) < 1e-7


def test_sidereal_day_is_shorter_than_solar_day():
    g0, g1 = gmst82_deg(JD_1992, 0.0), gmst82_deg(JD_1992 + 1, 0.0)
    advance = (g1 - g0) % 360.0          # ~0.9856 deg per solar day
    assert abs(advance - 0.98564736) < 1e-5


def test_range_and_wrap():
    for k in range(200):
        g = gmst82_deg(2451545.0 + k * 13.37, 0.123)
        assert 0.0 <= g < 360.0
    assert 0.0 <= lst_deg(JD_1992, FRAC, 359.9999) < 360.0


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_rejected(bad):
    with pytest.raises(ValueError):
        gmst82_deg(bad)
