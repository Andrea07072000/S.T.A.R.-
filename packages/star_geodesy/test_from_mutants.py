"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_geodesy_20261004.json, score 0.833): pole heights
and the inclusive +-90 deg latitude bound were never asserted.
Verifies: R1, R2 (README)."""
import pytest

from star_geodesy import B, ecef_to_geodetic, geodetic_to_ecef


@pytest.mark.parametrize("sign", [1, -1])
def test_pole_heights(sign):
    lat, lon, h = ecef_to_geodetic(0.0, 0.0, sign * (B + 100.0))
    assert lat == 90.0 * sign and lon == 0.0 and abs(h - 100.0) < 1e-6


def test_latitude_bounds_inclusive():
    assert abs(geodetic_to_ecef(90.0, 0.0, 0.0)[2] - B) < 1e-6
    assert abs(geodetic_to_ecef(-90.0, 0.0, 0.0)[2] + B) < 1e-6
    for bad in (90.000001, -90.000001):
        with pytest.raises(ValueError):
            geodetic_to_ecef(bad, 0.0, 0.0)
