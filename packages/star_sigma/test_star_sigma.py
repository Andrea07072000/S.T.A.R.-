"""star_sigma against published distribution values, closed forms derivable by hand, inverses and invariants.
Verifies the numerical meaning of n-sigma in 1/2/3D and branch behaviour at SERIES_BELOW and limits.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (a bound of 2e-16 in FACTS.md was below one unit in the last place: 4e-16)."""

import math

import pytest

import star_sigma as ss


def test_published_normal_and_sigma_table_values():
    assert abs(ss.normal_cdf(1.0) - 0.8413447) < 5e-7
    assert abs(ss.normal_cdf(1.959964) - 0.975000) < 5e-7
    assert abs(ss.normal_cdf(2.575829) - 0.995000) < 5e-7

    assert abs(ss.sigma_coverage(1.0, 1) - 0.6826895) < 5e-7
    assert abs(ss.sigma_coverage(2.0, 1) - 0.9544997) < 5e-7
    assert abs(ss.sigma_coverage(3.0, 1) - 0.9973002) < 5e-7

    assert abs(ss.sigma_for_coverage(0.95, 1) ** 2 - 3.841) < 5e-4
    assert abs(ss.sigma_for_coverage(0.95, 2) ** 2 - 5.991) < 5e-4
    assert abs(ss.sigma_for_coverage(0.95, 3) ** 2 - 7.815) < 5e-4
    assert abs(ss.sigma_for_coverage(0.99, 1) ** 2 - 6.635) < 5e-4
    assert abs(ss.sigma_for_coverage(0.99, 2) ** 2 - 9.210) < 5e-4
    assert abs(ss.sigma_for_coverage(0.99, 3) ** 2 - 11.345) < 5e-4


def test_closed_forms_by_hand_all_dims():
    n = 2.0
    t = n / math.sqrt(2.0)
    assert ss.sigma_coverage(n, 1) == pytest.approx(math.erf(t), abs=1e-15)  # dims=1: coverage = erf(n/sqrt(2))
    assert ss.sigma_tail(n, 1) == pytest.approx(math.erfc(t), abs=1e-15)      # dims=1: tail = erfc(n/sqrt(2))

    # dims=2: coverage = 1-exp(-n^2/2), tail = exp(-n^2/2)
    assert ss.sigma_coverage(n, 2) == pytest.approx(1.0 - math.exp(-0.5 * n * n), abs=1e-15)
    assert ss.sigma_tail(n, 2) == pytest.approx(math.exp(-0.5 * n * n), abs=1e-15)

    # dims=3: coverage = erf(n/sqrt(2)) - sqrt(2/pi) n exp(-n^2/2), tail = erfc(...) + ...
    c3 = math.erf(t) - math.sqrt(2.0 / math.pi) * n * math.exp(-0.5 * n * n)
    q3 = math.erfc(t) + math.sqrt(2.0 / math.pi) * n * math.exp(-0.5 * n * n)
    assert ss.sigma_coverage(n, 3) == pytest.approx(c3, abs=1e-15)
    assert ss.sigma_tail(n, 3) == pytest.approx(q3, abs=1e-15)


def test_invariants_monotonicity_and_dimension_ordering():
    for d in (1, 2, 3):
        assert ss.sigma_coverage(0.0, d) == 0.0
        assert ss.sigma_tail(0.0, d) == 1.0
        for n in (0.0, 1e-6, 0.3, 1.0, 2.0, 5.0, 10.0):
            c = ss.sigma_coverage(n, d)
            q = ss.sigma_tail(n, d)
            assert abs((c + q) - 1.0) < 4e-16
    for n1, n2 in ((0.1, 0.2), (0.9, 1.1), (2.0, 3.0)):
        for d in (1, 2, 3):
            assert ss.sigma_coverage(n1, d) < ss.sigma_coverage(n2, d)
            assert ss.sigma_tail(n1, d) > ss.sigma_tail(n2, d)
    for n in (1e-6, 0.1, 1.0, 3.0):
        assert ss.sigma_coverage(n, 1) > ss.sigma_coverage(n, 2) > ss.sigma_coverage(n, 3)


def test_normal_identities_and_inverses():
    assert ss.normal_cdf(0.0) == 0.5
    assert ss.normal_quantile(0.5) == 0.0
    for z in (-5.0, -1.0, 0.0, 1.0, 5.0):
        assert abs((ss.normal_cdf(z) + ss.normal_sf(z)) - 1.0) < 4e-16
        assert ss.normal_cdf(-z) == ss.normal_sf(z)
    for p in (0.1, 0.01, 1e-6):
        assert ss.normal_quantile(1.0 - p) == pytest.approx(-ss.normal_quantile(p), abs=1e-9)
    for p in (1e-12, 1e-9, 1e-6, 1e-3, 0.1, 0.5):
        assert ss.normal_cdf(ss.normal_quantile(p)) == pytest.approx(p, rel=1e-12, abs=0.0)
    for p in (0.6, 0.9, 1 - 1e-12):
        z = ss.normal_quantile(p)
        assert ss.normal_sf(z) == pytest.approx(1.0 - p, rel=1e-12, abs=0.0)


def test_sigma_inverse_and_defaults():
    for d in (1, 2, 3):
        assert ss.sigma_for_coverage(0.0, d) == 0.0
        for p in (1e-12, 1e-6, 1e-3, 0.1, 0.5):
            n = ss.sigma_for_coverage(p, d)
            assert ss.sigma_coverage(n, d) == pytest.approx(p, rel=1e-12, abs=0.0)
        for p in (0.6, 0.9, 1 - 1e-12):
            n = ss.sigma_for_coverage(p, d)
            assert ss.sigma_tail(n, d) == pytest.approx(1.0 - p, rel=1e-12, abs=0.0)

    n = 1.234
    p = 0.321
    assert ss.sigma_coverage(n) == ss.sigma_coverage(n, 1)
    assert ss.sigma_tail(n) == ss.sigma_tail(n, 1)
    assert ss.sigma_for_coverage(p) == ss.sigma_for_coverage(p, 1)


def test_digits_and_branch_join_for_dim3():
    assert ss.sigma_tail(5.0, 1) == pytest.approx(5.733031437583878e-07, rel=1e-12)
    assert ss.normal_sf(5.0) == pytest.approx(0.5 * ss.sigma_tail(5.0, 1), rel=1e-12)
    assert ss.sigma_tail(10.0, 2) == math.exp(-50.0)

    sf37 = ss.normal_sf(37.0)
    assert sf37 > 0.0 and sf37 == pytest.approx(5.7e-300, rel=0.2)
    assert ss.normal_quantile(1e-300) == pytest.approx(-37.047, abs=1e-3)

    # small-n 3D leading term: coverage ~ sqrt(2/pi) * n^3 / 3 ; at n=1e-3 this is 2.6596e-10
    assert ss.sigma_coverage(1e-3, 3) == pytest.approx(2.6596e-10, abs=1e-13)
    assert abs(ss.sigma_coverage(1.0 - 1e-9, 3) - ss.sigma_coverage(1.0, 3)) < 1e-9
    assert ss.sigma_coverage(1.0 - 1e-9, 3) < ss.sigma_coverage(1.0, 3)
