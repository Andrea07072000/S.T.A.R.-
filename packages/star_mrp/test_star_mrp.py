"""star_mrp against published values and hand-derivable identities/invariants.
Verifies forward/inverse maps, shadow set, composition, DCM convention, short-rotation branch, and kinematics.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_mrp as sm


def _flat(m):
    return [c for row in m for c in row]


def _n(v):
    return math.sqrt(sum(c * c for c in v))


def _mm(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def test_published_core_values():
    assert sm.mrp_from_quaternion((0.5, 0.5, 0.5, 0.5)) == pytest.approx((1 / 3, 1 / 3, 1 / 3), rel=0, abs=0)
    assert sm.quaternion_from_mrp((1 / 3, 1 / 3, 1 / 3)) == pytest.approx((0.5, 0.5, 0.5, 0.5), rel=0, abs=2e-16)
    assert _flat(sm.dcm_from_mrp((1 / 3, 1 / 3, 1 / 3))) == pytest.approx((0, 1, 0, 0, 0, 1, 1, 0, 0), rel=0, abs=2e-16)

    # tan(22.5°) = sqrt(2)-1
    s = (math.tan(math.pi / 8), 0.0, 0.0)
    assert sm.mrp_from_rotation_vector((math.pi / 2, 0, 0)) == pytest.approx(s, rel=0, abs=1e-16)
    assert _flat(sm.dcm_from_mrp((0, 0, math.tan(math.pi / 8)))) == pytest.approx((0, 1, 0, -1, 0, 0, 0, 0, 1), rel=0, abs=5e-16)

    assert sm.quaternion_from_mrp((0, 0, 1)) == (0.0, 0.0, 0.0, 1.0)
    assert sm.rotation_vector_from_mrp((0, 0, 1)) == pytest.approx((0, 0, math.pi), rel=0, abs=0)

    assert sm.quaternion_from_mrp((0, 0, 0)) == (1.0, 0.0, 0.0, 0.0)
    assert sm.dcm_from_mrp((0, 0, 0)) == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    assert sm.rotation_vector_from_mrp((0, 0, 0)) == (0.0, 0.0, 0.0)
    assert sm.mrp_from_quaternion((2, 0, 0, 0)) == (0.0, 0.0, 0.0)


def test_shadow_switch_and_short_rotation_branch():
    assert sm.shadow((0, 0, 3)) == pytest.approx((0, 0, -1 / 3), rel=0, abs=0)
    assert sm.shadow((0.5, 0, 0)) == pytest.approx((-2.0, 0, 0), rel=0, abs=0)
    s = (0.2, -0.3, 0.4)
    assert sm.shadow(sm.shadow(s)) == pytest.approx(s, rel=0, abs=2e-16)
    assert sm.shadow((1, 0, 0)) == (-1.0, 0.0, 0.0)

    q1 = sm.quaternion_from_mrp((0, 0, 3))
    q2 = sm.quaternion_from_mrp((0, 0, -1 / 3))
    # Hand derivation for (-1/3): s2=1/9, w=(1-s2)/(1+s2)=(8/9)/(10/9)=0.8, z=2(-1/3)/(10/9)=-0.6
    assert q1 == pytest.approx((0.8, 0.0, 0.0, -0.6), rel=0, abs=2e-16)
    assert q2 == pytest.approx((0.8, 0.0, 0.0, -0.6), rel=0, abs=2e-16)

    assert sm.switch((2, 0, 0)) == pytest.approx((-0.5, 0, 0), rel=0, abs=0)
    assert sm.switch((0.6, 0, 0), 0.5) == pytest.approx((-1.6666666666666667, 0, 0), rel=0, abs=0)
    assert sm.switch((0.5, 0, 0), 0.5) == (0.5, 0.0, 0.0)
    assert sm.switch((1, 0, 0)) == (1.0, 0.0, 0.0)

    m = sm.mrp_from_quaternion((-0.5, 0.5, 0.5, 0.5))
    assert m == pytest.approx((-1 / 3, -1 / 3, -1 / 3), rel=0, abs=0)
    assert _n(m) <= 1.0
    assert sm.mrp_from_quaternion((0, 1, 0, 0)) == (1.0, 0.0, 0.0)


def test_compose_and_matrix_product_convention():
    q = math.tan(math.pi / 8)
    assert sm.compose((0, 0, q), (0, 0, q)) == pytest.approx((0, 0, 1), rel=0, abs=2e-16)
    assert sm.compose((0, 0, 1), (0, 0, 1)) == (0.0, 0.0, 0.0)

    s = (0.31, -0.27, 0.19)
    assert sm.compose(s, (-s[0], -s[1], -s[2])) == pytest.approx((0, 0, 0), rel=0, abs=1e-16)
    assert sm.compose(s, (0, 0, 0)) == pytest.approx(s, rel=0, abs=2e-16)

    a, b = (0.2, 0.0, 0.0), (0.0, 0.3, 0.0)
    assert sm.compose(a, b) != sm.compose(b, a)

    c_ab = sm.dcm_from_mrp(sm.compose(a, b))
    c_prod = _mm(sm.dcm_from_mrp(b), sm.dcm_from_mrp(a))
    assert _flat(c_ab) == pytest.approx(_flat(c_prod), rel=0, abs=1e-14)


def test_rotation_vectors_and_kinematics():
    rv = sm.rotation_vector_from_mrp((1 / 3, 1 / 3, 1 / 3))
    assert _n(rv) == pytest.approx(2 * math.pi / 3, rel=0, abs=1e-15)

    assert sm.mrp_from_rotation_vector((0, 0, 3 * math.pi / 2)) == pytest.approx((0, 0, -(math.tan(math.pi / 8))), rel=0, abs=1e-15)
    assert sm.mrp_from_rotation_vector((0, 2 * math.pi, 0)) == pytest.approx((0, 0, 0), rel=0, abs=1e-16)
    assert sm.rotation_vector_from_mrp((3, 0, 0)) == pytest.approx((-4 * math.atan(1 / 3), 0, 0), rel=0, abs=1e-15)

    assert sm.mrp_rate((0, 0, 0), (0.4, 0, 0)) == pytest.approx((0.1, 0, 0), rel=0, abs=0)
    assert sm.mrp_rate((0, 0, 1), (0, 0, 0.4)) == pytest.approx((0, 0, 0.2), rel=0, abs=0)
    # For s=(0.5,0,0), w=(0,0.4,0):
    # y term: (1-s^2)wy/4 = (1-0.25)*0.4/4 = 0.075 ; z term: (2*(s×w)_z)/4 = (2*0.2)/4 = 0.1
    assert sm.mrp_rate((0.5, 0, 0), (0, 0.4, 0)) == pytest.approx((0, 0.075, 0.1), rel=0, abs=1e-16)

    s, w, dt = (0.21, -0.17, 0.09), (0.3, -0.2, 0.4), 1e-6
    euler = tuple(s[i] + sm.mrp_rate(s, w)[i] * dt for i in range(3))
    comp = sm.compose(s, sm.mrp_from_rotation_vector(tuple(wi * dt for wi in w)))
    err = _n(tuple(euler[i] - comp[i] for i in range(3)))
    assert err <= 2 * (_n(tuple(wi * dt for wi in w)) ** 2)
