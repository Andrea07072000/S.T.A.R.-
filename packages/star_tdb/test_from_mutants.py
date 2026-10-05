"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_tdb_20261004.json, score 0.778).
The small series terms (2-14 us) are BELOW the 10 us verification tolerance against ERFA, so a wrong small term is
invisible to the correctness test by construction. The REGRESSION values below pin THIS implementation (frozen
2026-10-04): they detect any change of the code, they do NOT prove correctness (that is ERFA's job, within 10 us).
Verifies: R3 (README)."""
import pytest

from star_tdb import tdb_minus_tt

REG = [(2305447.5, 0.00013241365620755667), (2378496.5, 2.6864299070119658e-05), (2433282.5, -6.96864050288101e-05), (2451545.0, -9.575743486095212e-05), (2459959.5, 0.00029141479331223593), (2488070.5, -5.6504654873325584e-05), (2524593.0, -0.00021273864831590147)]


def test_regression_pins_the_implementation():
    for jd, v in REG:
        assert abs(tdb_minus_tt(jd) - v) < 1e-15


def test_validity_bounds_are_inclusive_and_exact():
    jd_2200 = 2451545.0 + 2.0 * 36525.0           # year exactly 2200.0 (T = 2)
    tdb_minus_tt(jd_2200)
    tdb_minus_tt(2451545.0 - 4.0 * 36525.0)       # year exactly 1600.0
    with pytest.raises(ValueError):
        tdb_minus_tt(jd_2200 + 1.0)
    with pytest.raises(ValueError):
        tdb_minus_tt(2451545.0 - 4.0 * 36525.0 - 1.0)
