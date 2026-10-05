"""Plane change, combined burn, bi-elliptic (STAR-ORB-PLANE). References: closed-form identities and the classic
Hohmann / bi-elliptic crossovers R = 11.94 (rb -> infinity) and R = 15.58 (any rb > r2), Vallado,
Fundamentals of Astrodynamics and Applications, sec. 6.3. The rb -> infinity limit is computed with the
independent closed form sqrt(mu/r1) * (sqrt(2) - 1) * (1 + sqrt(r1/r2)), not with the code under test.
Verifies: R1, R2, R3 (README)."""
import math

import pytest

from star_maneuver import bielliptic, combined_dv, hohmann, plane_change

MU, R1 = 398600.4418, 6678.0


def test_plane_change_60_deg_equals_speed():
    assert math.isclose(plane_change(7.5, math.radians(60)), 7.5, rel_tol=1e-12)


def test_plane_change_zero_and_180():
    assert plane_change(7.5, 0) == 0
    assert math.isclose(plane_change(7.5, math.pi), 15.0, rel_tol=1e-12)


def test_combined_reduces_to_speed_change_and_plane_change():
    assert math.isclose(combined_dv(7.0, 3.0, 0.0), 4.0, rel_tol=1e-12)
    assert math.isclose(combined_dv(7.5, 7.5, 0.7), plane_change(7.5, 0.7), rel_tol=1e-12)


def test_combined_is_cheaper_than_separate_burns():
    v1, v2, di = 1.6, 3.07, math.radians(28.5)  # GTO apogee -> GEO-like numbers
    assert combined_dv(v1, v2, di) < abs(v2 - v1) + plane_change(v2, di)


def test_bielliptic_with_rb_equal_r2_is_hohmann():
    r2 = 42164.0
    assert math.isclose(bielliptic(R1, r2, r2)["dv_total"], hohmann(R1, r2)["dv_total"], rel_tol=1e-12)


def _ratio_delta(R):
    """Hohmann minus bi-elliptic at rb -> infinity (independent closed form); root at R = 11.9388."""
    be_inf = math.sqrt(MU / R1) * (math.sqrt(2) - 1) * (1 + math.sqrt(1 / R))
    return hohmann(R1, R * R1)["dv_total"] - be_inf


def test_crossover_rb_infinity_is_11_94():
    lo, hi = 5.0, 30.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if _ratio_delta(mid) > 0 else (mid, hi)
    assert abs(lo - 11.9388) < 1e-3


def test_large_rb_approaches_the_infinite_limit():
    R = 20.0
    be = bielliptic(R1, R * R1, 1e12 * R1)["dv_total"]
    be_inf = math.sqrt(MU / R1) * (math.sqrt(2) - 1) * (1 + math.sqrt(1 / R))
    assert abs(be - be_inf) / be_inf < 1e-4


@pytest.mark.parametrize("R", [16.0, 30.0])
def test_above_15_58_bielliptic_always_wins(R):
    h = hohmann(R1, R * R1)["dv_total"]
    for k in (1.01, 1.5, 3, 10, 100, 1000):
        assert bielliptic(R1, R * R1, k * R * R1)["dv_total"] < h


def test_between_11_94_and_15_58_it_depends_on_rb():
    R = 14.0
    h = hohmann(R1, R * R1)["dv_total"]
    assert bielliptic(R1, R * R1, 1.5 * R * R1)["dv_total"] > h
    assert bielliptic(R1, R * R1, 1e6 * R * R1)["dv_total"] < h


def test_below_11_94_hohmann_always_wins():
    R = 10.0
    h = hohmann(R1, R * R1)["dv_total"]
    for k in (1.01, 2, 10, 1e3, 1e6):
        assert bielliptic(R1, R * R1, k * R * R1)["dv_total"] > h


def test_invalid_inputs():
    with pytest.raises(ValueError):
        bielliptic(R1, 42164.0, 40000.0)
    with pytest.raises(ValueError):
        plane_change(-1.0, 0.1)
