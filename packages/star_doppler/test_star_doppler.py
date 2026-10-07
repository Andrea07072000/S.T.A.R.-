"""star_doppler against published constants/examples and hand-derivable identities.
Verifies forward behaviour, inverses/invariants, edge cases and branch decisions.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_doppler as sd


def test_published_constant_and_exports():
    assert sd.C_KM_S == 299792.458
    assert sd.__all__ == ["range_and_rate", "received_frequency", "C_KM_S"]


def test_range_and_rate_hand_values():
    assert sd.range_and_rate((0, 0, 0), (0, 0, 0), (3, 4, 0), (1, 0, 0)) == pytest.approx((5.0, 0.6), abs=1e-12)
    assert sd.range_and_rate((0, 0, 0), (0, 0, 0), (10, 0, 0), (0, 5, 0)) == pytest.approx((10.0, 0.0), abs=1e-12)
    assert sd.range_and_rate((0, 0, 0), (0, 0, 0), (0, 0, 7), (0, 0, -2)) == pytest.approx((7.0, -2.0), abs=1e-12)
    assert sd.range_and_rate((0, 0, 0), (0, 0, 0), (0, 0, 7), (0, 0, 2)) == pytest.approx((7.0, 2.0), abs=1e-12)
    assert sd.range_and_rate((1, 2, 3), (0.1, 0.2, 0.3), (4, 6, 3), (0.1, 0.2, 0.3)) == pytest.approx((5.0, 0.0), abs=1e-12)
    assert sd.range_and_rate((0, 0, 0), (1, 0, 0), (10, 0, 0), (0, 0, 0)) == pytest.approx((10.0, -1.0), abs=1e-12)
    assert sd.range_and_rate((-1e15, 0, 0), (0, 0, 0), (1e15, 0, 0), (1e15, 0, 0)) == pytest.approx((2e15, 1e15), abs=1e-6)


def test_range_and_rate_invariants_and_exchange_symmetry():
    ro, vo = (1.2, -3.4, 5.6), (-0.7, 2.3, 4.5)
    rt, vt = (7.8, 9.1, -2.3), (3.2, -1.1, 0.4)
    d, r = sd.range_and_rate(ro, vo, rt, vt)
    shift_r, shift_v = (11, -13, 17), (19, -23, 29)
    d2, r2 = sd.range_and_rate(tuple(ro[i] + shift_r[i] for i in range(3)),
                               tuple(vo[i] + shift_v[i] for i in range(3)),
                               tuple(rt[i] + shift_r[i] for i in range(3)),
                               tuple(vt[i] + shift_v[i] for i in range(3)))
    d3, r3 = sd.range_and_rate(rt, vt, ro, vo)
    assert d2 == pytest.approx(d, abs=1e-12) and r2 == pytest.approx(r, abs=1e-12)
    assert d3 == pytest.approx(d, abs=1e-12) and r3 == pytest.approx(r, abs=1e-12)


def test_rate_bound_and_alignment_equality_case():
    ro, rt = (0, 0, 0), (3, 4, 0)  # line of sight unit is (0.6, 0.8, 0)
    vo, vt = (0, 0, 0), (1, 0, 0)
    _, rr = sd.range_and_rate(ro, vo, rt, vt)
    dv = math.hypot(vt[0] - vo[0], vt[1] - vo[1], vt[2] - vo[2])
    assert abs(rr) <= dv + 1e-15
    # equality when relative velocity is exactly along line of sight
    _, rr2 = sd.range_and_rate((0, 0, 0), (0, 0, 0), (10, 0, 0), (2, 0, 0))
    assert abs(rr2) == pytest.approx(2.0, abs=1e-12)


def test_received_frequency_published_values_and_zero_rate_identity():
    assert sd.received_frequency(1000.0, 0.6 * sd.C_KM_S) == pytest.approx(500.0, abs=1e-12)
    assert sd.received_frequency(1000.0, -0.6 * sd.C_KM_S) == pytest.approx(2000.0, abs=1e-12)
    assert sd.received_frequency(1000.0, 0.6 * sd.C_KM_S, False) == pytest.approx(400.0, abs=1e-12)
    assert sd.received_frequency(1000.0, -0.6 * sd.C_KM_S, False) == pytest.approx(1600.0, abs=1e-12)
    assert sd.received_frequency(1234.5, 0.0) == 1234.5
    assert sd.received_frequency(1234.5, 0.0, False) == 1234.5


def test_received_frequency_sign_product_linearity_and_7p5kms_example():
    f, v = 2345.6, 123.4
    fr, fa = sd.received_frequency(f, v), sd.received_frequency(f, -v)
    assert fr < f < fa
    assert fr * fa == pytest.approx(f * f, abs=1e-12)
    assert sd.received_frequency(f, v, False) == pytest.approx(f * (1 - v / sd.C_KM_S), abs=1e-12)

    f2, v2 = 2.2e9, 7.5
    rel = sd.received_frequency(f2, v2, True)
    lin = sd.received_frequency(f2, v2, False)
    assert rel == pytest.approx(2199944962.6127, abs=1e-3)
    assert lin == pytest.approx(2199944961.9243, abs=1e-3)
    # first non-linear term of sqrt((1-b)/(1+b)) is +b^2/2 over first-order result: delta ~= f*b^2/2
    b = v2 / sd.C_KM_S
    assert rel - lin == pytest.approx(f2 * b * b / 2.0, rel=3e-3)


def test_chain_range_and_rate_into_doppler():
    f = 8.4e9
    rr = sd.range_and_rate((0, 0, 0), (0, 0, 0), (1000, 0, 0), (3, 0, 0))[1]
    assert sd.received_frequency(f, rr) == pytest.approx(sd.received_frequency(f, 3.0), abs=1e-12)
