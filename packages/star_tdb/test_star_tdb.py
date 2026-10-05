"""TDB - TT vs ERFA dtdb (full Fairhead & Bretagnon series), values frozen 2026-10-04 with pyerfa 2.0.1.5, geocentre
(ut=0, observer at origin). Acceptance: the stated accuracy of USNO Circular 179 eq. 2.6, 10 microseconds.
Verifies: R2, R3 (README)."""
import pytest

from star_tdb import tdb_minus_tt

REF = [(2305447.5, 0.00013269239006530794), (2378496.5, 3.0482176538630544e-05), (2415020.5, -1.8460232010485015e-05), (2444239.5, -5.757956780826994e-05), (2451545.0, -9.930719894379447e-05), (2455197.5, -9.413734890986844e-05), (2459959.5, 0.00028241830057912793), (2460586.5, -0.0016393480141571142), (2469807.5, -8.018829477924309e-05), (2524593.5, -0.00020169908739398995)]


def test_against_erfa_full_series_within_stated_accuracy():
    for jd, ref in REF:
        assert abs(tdb_minus_tt(jd) - ref) <= 10e-6, (jd, tdb_minus_tt(jd), ref)


def test_amplitude_and_periodicity():
    vals = [tdb_minus_tt(2451545.0 + d) for d in range(0, 366)]
    assert 1.6e-3 < max(vals) < 1.75e-3 and -1.75e-3 < min(vals) < -1.6e-3   # dominant annual term 1.657 ms


def test_outside_validity_is_an_error():
    with pytest.raises(ValueError):
        tdb_minus_tt(2305447.5 - 400)      # before 1600
    with pytest.raises(ValueError):
        tdb_minus_tt(2524593.5 + 400)      # after 2200
