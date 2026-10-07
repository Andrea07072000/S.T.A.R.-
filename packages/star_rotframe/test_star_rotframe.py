"""star_rotframe against published values and hand-derivable checks: turns, transport term, inverse and invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math
import pytest

import star_rotframe as sr


def test_published_constants_and_equator_speed():
    assert sr.EARTH_RATE == 7.292115e-5
    # Published: a = 6378.137 km, w = 7.292115e-5 rad/s -> v = w*R
    assert sr.EARTH_RATE * 6378.137 == pytest.approx(0.46510108, abs=1e-8)


def test_hand_cases_no_rotation_and_quarter_half_turns():
    assert sr.to_rotating((1, 2, 3), (4, 5, 6), 0, 0) == ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    quarter = sr.to_rotating((1, 0, 0), (0, 0, 0), math.pi / 2, 0)                 # approx does not take nested tuples: compare part by part
    assert quarter[0] == pytest.approx((0, -1, 0), abs=1e-15) and quarter[1] == pytest.approx((0, 0, 0), abs=1e-15)
    quarter = sr.to_rotating((0, 1, 0), (0, 0, 0), math.pi / 2, 0)
    assert quarter[0] == pytest.approx((1, 0, 0), abs=1e-15) and quarter[1] == pytest.approx((0, 0, 0), abs=1e-15)
    assert sr.to_rotating((1, 2, 3), (0, 0, 0), math.pi, 0)[0] == pytest.approx((-1, -2, 3), abs=1e-15)


def test_z_components_unchanged_and_transport_term_signs():
    r, v = (3, 4, 5), (6, 7, 8)
    rr, vv = sr.to_rotating(r, v, 1.2345, -0.25)
    assert rr[2] == 5.0 and vv[2] == 8.0

    assert sr.to_rotating((1, 0, 0), (0, 0, 0), 0, 2.0)[1] == pytest.approx((0, -2, 0), abs=1e-15)
    assert sr.to_rotating((0, 1, 0), (0, 0, 0), 0, 2.0)[1] == pytest.approx((2, 0, 0), abs=1e-15)
    assert sr.to_rotating((3, 4, 5), (0, 0, 0), 0, 0.5)[1] == pytest.approx((2.0, -1.5, 0.0), abs=1e-15)
    assert sr.to_rotating((1, 0, 0), (0, 0, 0), 0, -2.0)[1] == pytest.approx((0, 2, 0), abs=1e-15)


def test_fixed_on_rotating_body_and_inverse_specific():
    R = 6378.137
    a = math.pi / 2
    w = sr.EARTH_RATE
    # For a point fixed in rotating frame at (R,0,0): inertial r=(R cos a, R sin a,0), v=(-wR sin a, wR cos a,0)
    r = (0.0, R, 0.0)
    v = (-w * R, 0.0, 0.0)
    rr, vv = sr.to_rotating(r, v, a, w)
    assert rr == pytest.approx((R, 0.0, 0.0), abs=1e-9)
    assert vv == pytest.approx((0.0, 0.0, 0.0), abs=1e-12)

    ri, vi = sr.to_inertial((R, 0, 0), (0, 0, 0), a)
    assert ri == pytest.approx((R * math.cos(a), R * math.sin(a), 0.0), abs=1e-12)
    assert vi == pytest.approx((-w * R * math.sin(a), w * R * math.cos(a), 0.0), abs=1e-12)


def test_inertially_fixed_seen_moving_backwards_default_rate():
    vv = sr.to_rotating((7000, 0, 0), (0, 0, 0), 0)[1]
    assert vv == pytest.approx((0.0, -7000.0 * sr.EARTH_RATE, 0.0), abs=1e-12)
    assert vv == pytest.approx((0.0, -0.51044805, 0.0), abs=1e-12)


def test_inverse_roundtrip_and_norm_invariants_and_2pi_periodicity():
    r = (1234.5, -6789.25, 42.125)
    v = (-1.25, 7.75, -0.5)
    a, w = 1.23456789, -0.75

    rr, vv = sr.to_rotating(r, v, a, w)
    r2, v2 = sr.to_inertial(rr, vv, a, w)
    assert r2 == pytest.approx(r, rel=1e-12, abs=1e-12)
    assert v2 == pytest.approx(v, rel=1e-12, abs=1e-12)

    ri, vi = sr.to_inertial(r, v, a, w)
    r3, v3 = sr.to_rotating(ri, vi, a, w)
    assert r3 == pytest.approx(r, rel=1e-12, abs=1e-12)
    assert v3 == pytest.approx(v, rel=1e-12, abs=1e-12)

    nr = math.sqrt(sum(c * c for c in r))
    nrr = math.sqrt(sum(c * c for c in rr))
    assert nrr == pytest.approx(nr, rel=1e-12)

    vv0 = sr.to_rotating(r, v, a, 0.0)[1]
    nv = math.sqrt(sum(c * c for c in v))
    nvv0 = math.sqrt(sum(c * c for c in vv0))
    assert nvv0 == pytest.approx(nv, rel=1e-12)

    rr2, vv2 = sr.to_rotating(r, v, a + 2 * math.pi, w)
    assert rr2 == pytest.approx(rr, rel=1e-9, abs=1e-12)
    assert vv2 == pytest.approx(vv, rel=1e-9, abs=1e-12)


def test_positive_zero_outputs_and_list_tuple_int_acceptance():
    rr, vv = sr.to_rotating([1, 0, 0], [0, 0, 0], math.pi / 2, 0)
    for x in (*rr, *vv):
        if x == 0.0:
            assert math.copysign(1.0, x) == 1.0

    t = sr.to_rotating((1, 2, 3), (4, 5, 6), 0, 0)
    from_lists = sr.to_rotating([1, 2, 3], [4, 5, 6], 0, 0)
    assert t == from_lists
