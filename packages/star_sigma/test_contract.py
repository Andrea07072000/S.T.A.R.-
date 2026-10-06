"""Refusal contract and range limits for every public star_sigma function, plus pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (a bound of 2e-16 in FACTS.md was below one unit in the last place: 4e-16)."""


import pytest

import star_sigma as ss

BAD_NUM = [True, False, "1", None, float("nan"), float("inf"), float("-inf"), 1j, [1.0]]


def test_pinned_constants_and_exports():
    assert ss.__version__ == "0.1.0"
    assert ss.__all__ == ["normal_cdf", "normal_sf", "normal_quantile", "sigma_coverage", "sigma_tail", "sigma_for_coverage"]
    assert ss.Z_MAX == 38.0
    assert ss.SERIES_BELOW == 1.0


@pytest.mark.parametrize("f", [ss.normal_cdf, ss.normal_sf], ids=lambda f: f.__name__)
def test_normal_cdf_sf_z_limits_and_refusals(f):
    assert type(f(-38.0)) is float
    assert type(f(38.0)) is float
    with pytest.raises(ValueError):
        f(38.0000001)
    with pytest.raises(ValueError):
        f(-38.0000001)
    for bad in BAD_NUM:
        with pytest.raises(ValueError):
            f(bad)


def test_normal_quantile_open_interval_and_refusals():
    assert ss.normal_quantile(0.5) == 0.0
    for p in (0.0, 1.0, -0.1, 1.1):
        with pytest.raises(ValueError):
            ss.normal_quantile(p)
    for bad in BAD_NUM:
        with pytest.raises(ValueError):
            ss.normal_quantile(bad)


def test_sigma_coverage_tail_argument_contract():
    for f in (ss.sigma_coverage, ss.sigma_tail):
        assert type(f(0.0, 1)) is float
        assert type(f(38.0, 3)) is float
        with pytest.raises(ValueError):
            f(-1e-12, 1)
        with pytest.raises(ValueError):
            f(38.0000001, 1)

    bad_dims = [0, 4, 2.0, "2", None, True]
    for d in bad_dims:
        with pytest.raises(ValueError):
            ss.sigma_coverage(1.0, d)
        with pytest.raises(ValueError):
            ss.sigma_tail(1.0, d)

    for bad in BAD_NUM:
        with pytest.raises(ValueError):
            ss.sigma_coverage(bad, 1)
        with pytest.raises(ValueError):
            ss.sigma_tail(bad, 1)


def test_sigma_for_coverage_contract_and_range_edges():
    assert ss.sigma_for_coverage(0.0, 1) == 0.0
    assert type(ss.sigma_for_coverage(1.0 - 1e-15, 3)) is float
    for p in (1.0, 1.0000001, -1e-12):
        with pytest.raises(ValueError):
            ss.sigma_for_coverage(p, 1)

    for d in (0, 4, 2.0, "2", None, True):
        with pytest.raises(ValueError):
            ss.sigma_for_coverage(0.5, d)

    for bad in BAD_NUM:
        with pytest.raises(ValueError):
            ss.sigma_for_coverage(bad, 1)
