"""The auditor itself must be right: an exact library scores ~0, a library with a KNOWN injected error is measured with
that error, and the envelope is reported per altitude band (the oracle of the auditor is the injected defect).
Verifies: R1, R2, R3 (README).
"""
import pytest

from star_audit import ALTITUDES_M, audit_function, envelope, points
from star_geodesy import ecef_to_geodetic


def test_exact_library_has_zero_envelope():
    e = audit_function(ecef_to_geodetic)
    assert e["worst"]["pos_err_m"] < 1e-6 and e["n_points"] == len(points())


def test_injected_height_error_is_measured_in_the_right_band():
    def biased(x, y, z):
        la, lo, h = ecef_to_geodetic(x, y, z)
        return la, lo, h + (0.25 if h > 1e6 else 0.0)        # 25 cm error only above 1000 km
    e = audit_function(biased)
    assert abs(e["bands"]["5000000.0"]["h_err_m"] - 0.25) < 1e-6
    assert e["bands"]["0.0"]["h_err_m"] < 1e-6
    assert abs(e["worst"]["pos_err_m"] - 0.25) < 1e-6 and e["worst"]["altitude_m"] > 1e6


def test_injected_latitude_error_shows_as_position_error():
    def skewed(x, y, z):
        la, lo, h = ecef_to_geodetic(x, y, z)
        return la + 1e-6, lo, h                                 # 1e-6 deg ~ 0.11 m at the surface
    e = audit_function(skewed)
    assert abs(e["bands"]["0.0"]["lat_err_deg"] - 1e-6) < 1e-12
    assert 0.10 < e["bands"]["0.0"]["pos_err_m"] < 0.12


def test_all_altitude_bands_reported_and_mismatch_rejected():
    e = audit_function(ecef_to_geodetic)
    assert len(e["bands"]) == len(ALTITUDES_M)
    with pytest.raises(ValueError):
        envelope(points(), [])


def test_audit_is_deterministic():
    from star_geodesy import ecef_to_geodetic as f
    assert audit_function(f) == audit_function(f)
