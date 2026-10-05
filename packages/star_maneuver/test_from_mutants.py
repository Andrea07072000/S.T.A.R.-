"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_maneuver_20261004.json, score 0.564).
The original suite never checked the time of flight, the default mu, or the zero boundaries.
Verifies: R1, R2, R3 (README)."""
import math

import pytest

from star_maneuver import bielliptic, combined_dv, hohmann, plane_change, vis_viva

MU = 398600.4418


def half_period(a):
    """Independent: Kepler's third law, T = 2 pi sqrt(a^3 / mu); a transfer half-ellipse takes T / 2."""
    return 2 * math.pi * math.sqrt(a ** 3 / MU) / 2


def test_hohmann_time_of_flight_is_half_the_transfer_period():
    r1, r2 = 6678.0, 42164.0
    assert math.isclose(hohmann(r1, r2)["tof_s"], half_period((r1 + r2) / 2), rel_tol=1e-12)
    assert 5.2 * 3600 < hohmann(r1, r2)["tof_s"] < 5.3 * 3600      # LEO -> GEO transfer ~5.27 h


def test_bielliptic_time_of_flight_is_two_half_periods():
    r1, r2, rb = 7000.0, 105000.0, 210000.0
    exp = half_period((r1 + rb) / 2) + half_period((r2 + rb) / 2)
    assert math.isclose(bielliptic(r1, r2, rb)["tof_s"], exp, rel_tol=1e-12)


def test_default_mu_is_used_and_is_the_standard_value():
    assert math.isclose(vis_viva(7000.0, 7000.0), math.sqrt(MU / 7000.0), rel_tol=1e-15)
    assert hohmann(6678, 42164) == hohmann(6678, 42164, mu=MU)
    assert bielliptic(7000, 105000, 210000) == bielliptic(7000, 105000, 210000, mu=MU)
    assert hohmann(6678, 42164)["dv_total"] != hohmann(6678, 42164, mu=MU + 1)["dv_total"]


@pytest.mark.parametrize("call", [lambda: vis_viva(0.0, 7000.0), lambda: vis_viva(7000.0, 0.0),
                                  lambda: hohmann(0.0, 7000.0), lambda: hohmann(7000.0, 0.0),
                                  lambda: bielliptic(0.0, 7000.0, 9000.0), lambda: bielliptic(7000.0, 0.0, 9000.0),
                                  lambda: bielliptic(7000.0, 8000.0, 0.0), lambda: combined_dv(-0.1, 1.0, 0.1),
                                  lambda: combined_dv(1.0, -0.1, 0.1)])
def test_zero_and_negative_inputs_raise(call):
    with pytest.raises(ValueError):
        call()


def test_zero_speed_is_allowed_and_gives_zero():
    assert plane_change(0.0, 1.0) == 0.0
    assert combined_dv(0.0, 0.0, 1.0) == 0.0
    assert combined_dv(7.5, 7.5, 0.0) == 0.0          # identical velocities: no burn


def test_individual_burns_match_independent_vis_viva():
    r1, r2 = 6678.0, 42164.0
    a = (r1 + r2) / 2
    vv = lambda r, a_: math.sqrt(MU * (2 / r - 1 / a_))
    h = hohmann(r1, r2)
    assert math.isclose(h["dv1"], vv(r1, a) - vv(r1, r1), rel_tol=1e-12)
    assert math.isclose(h["dv2"], vv(r2, r2) - vv(r2, a), rel_tol=1e-12)
    rb = 3 * r2
    b = bielliptic(r1, r2, rb)
    a1, a2 = (r1 + rb) / 2, (r2 + rb) / 2
    assert math.isclose(b["dv1"], vv(r1, a1) - vv(r1, r1), rel_tol=1e-12)
    assert math.isclose(b["dv2"], vv(rb, a2) - vv(rb, a1), rel_tol=1e-12)
    assert math.isclose(b["dv3"], vv(r2, a2) - vv(r2, r2), rel_tol=1e-12)
    assert math.isclose(b["dv_total"], b["dv1"] + b["dv2"] + b["dv3"], rel_tol=1e-15)
