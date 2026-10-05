"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_sidereal_20261004.json): the T^2 and T^3 terms are
invisible near J2000 (T^3 ~ 1e-9 s), so distant epochs are compared with ERFA gmst82 values frozen 2026-10-04
(pyerfa 2.0.1.5), independent code of the same IAU 1982 model. The default fraction argument is pinned too.
Verifies: R1, R2 (README)."""
import math

from star_sidereal import gmst82_deg, lst_deg

ERFA = [(2305447.5, 190.0971425518793), (2378496.5, 190.64694591496357),     # 1600, 1800 (+0.25 day)
        (2451545.0, 10.707030216571592), (2524593.5, 190.77021785736906)]    # 2000, 2200


def test_distant_epochs_match_erfa_full_polynomial():
    for jd, ref in ERFA:
        assert abs(gmst82_deg(jd, 0.25) - ref) < 1e-8, (jd, gmst82_deg(jd, 0.25), ref)


def test_default_fraction_is_zero():
    assert gmst82_deg(2451545.0) == gmst82_deg(2451545.0, 0.0)


def test_lst_wraparound_of_minus_one_ulp_returns_zero_not_360():
    # GMST + longitude = -1.8e-15 exactly; Python's % then yields 360.0, which the [0, 360) contract must fold to 0.0
    g = gmst82_deg(2451545.0, 0.25)
    lon = math.nextafter(-g, -1e9)
    assert (g + lon) % 360.0 == 360.0                     # the float trap really occurs on this input
    assert lst_deg(2451545.0, 0.25, lon) == 0.0


def test_lst_adds_east_longitude_and_wraps():
    g = gmst82_deg(2451545.0, 0.25)
    assert abs(lst_deg(2451545.0, 0.25, 90.0) - (g + 90.0)) < 1e-12
    assert abs(lst_deg(2451545.0, 0.25, 355.0) - (g + 355.0 - 360.0)) < 1e-12
    assert abs(lst_deg(2451545.0, 0.25, -20.0) - (g - 20.0 + 360.0)) < 1e-12
