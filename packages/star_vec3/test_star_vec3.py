"""star_vec3 against hand-derivable values, inverses and invariants.
Verifies basis operations, robust angles, decomposition identities and extreme scaling.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math
from fractions import Fraction

import pytest

import star_vec3 as sv

i, j, k = (1, 0, 0), (0, 1, 0), (0, 0, 1)
a = (1, 2, 3)
b = (-2, 0.5, 4)


def test_basis_and_exact_hand_values():
    assert sv.cross(i, j) == (0.0, 0.0, 1.0)
    assert sv.cross(j, k) == (1.0, 0.0, 0.0)
    assert sv.cross(k, i) == (0.0, 1.0, 0.0)
    assert sv.cross(b, a) == tuple(-x for x in sv.cross(a, b))
    assert sv.cross(a, a) == (0.0, 0.0, 0.0)
    assert sv.dot(i, j) == 0.0
    assert sv.dot(a, b) == 11.0  # 1*(-2)+2*0.5+3*4=-2+1+12=11
    assert sv.cross(a, b) == (6.5, -10.0, 4.5)  # (2*4-3*0.5, 3*(-2)-1*4, 1*0.5-2*(-2))
    assert sv.norm((3, 4, 0)) == 5.0
    assert sv.norm((1, 2, 2)) == 3.0
    assert sv.distance(a, b) == 3.5  # a-b=(3,1.5,-1), sqrt(9+2.25+1)=sqrt(12.25)=3.5
    assert sv.triple(a, b, (1, 1, 1)) == 1.0  # cross(a,b)·(1,1,1)=6.5-10+4.5
    assert sv.distance((1, 1, 1), (1, 1, 1)) == 0.0


def test_unit_project_reject_and_angles():
    ua = sv.unit(a)
    r14 = math.sqrt(14.0)
    assert ua == pytest.approx((1 / r14, 2 / r14, 3 / r14), abs=2e-16)
    p = sv.project(a, b)
    # |b|^2 = 4 + 0.25 + 16 = 20.25; projection factor = (a·b)/|b|^2 = 11/20.25
    f = 11.0 / 20.25
    assert p == pytest.approx((f * b[0], f * b[1], f * b[2]), abs=1e-15)
    r = sv.reject(a, b)
    assert r == pytest.approx((a[0] - p[0], a[1] - p[1], a[2] - p[2]), abs=1e-15)
    assert sv.angle_deg(i, j) == 90.0
    assert sv.angle_deg(i, (1, 1, 0)) == pytest.approx(45.0, abs=1e-13)
    assert sv.angle_deg(a, a) == 0.0
    assert sv.angle_deg(a, (-1, -2, -3)) == 180.0
    assert sv.angle_deg(a, b) == pytest.approx(49.2087297841, abs=1e-9)


def test_invariants_and_scaling():
    c = sv.cross(a, b)
    assert abs(sv.dot(c, a)) <= 1e-13 * sv.norm(c) * sv.norm(a)
    assert abs(sv.dot(c, b)) <= 1e-13 * sv.norm(c) * sv.norm(b)
    lhs = sv.norm(c) ** 2 + sv.dot(a, b) ** 2
    rhs = sv.norm(a) ** 2 * sv.norm(b) ** 2
    assert lhs == pytest.approx(rhs, rel=1e-14)
    p, r = sv.project(a, b), sv.reject(a, b)
    assert (p[0] + r[0], p[1] + r[1], p[2] + r[2]) == pytest.approx(a, abs=1e-15 * sv.norm(a))
    assert abs(sv.dot(r, b)) <= 1e-13 * sv.norm(r) * sv.norm(b)
    assert sv.norm(sv.cross(p, b)) <= 1e-13
    assert sv.project(a, (2 * b[0], 2 * b[1], 2 * b[2])) == pytest.approx(p, abs=1e-15)
    assert sv.reject(a, (2 * b[0], 2 * b[1], 2 * b[2])) == pytest.approx(r, abs=1e-15)
    assert sv.triple(a, b, (1, 1, 1)) == pytest.approx(sv.triple(b, (1, 1, 1), a), rel=1e-13)
    assert sv.triple(a, b, (1, 1, 1)) == pytest.approx(-sv.triple(b, a, (1, 1, 1)), rel=1e-13)
    assert sv.triple((1, 0, 0), (0, 1, 0), (1, 1, 0)) == 0.0


def test_extremes_and_types():
    assert sv.unit((0, 0, -7)) == (0.0, 0.0, -1.0)
    assert sv.unit((3e-300, 4e-300, 0)) == pytest.approx((0.6, 0.8, 0.0), abs=1e-15)
    assert sv.unit((3e99, 4e99, 0)) == pytest.approx((0.6, 0.8, 0.0), abs=1e-15)
    assert sv.norm((3e99, 4e99, 0)) == 5e99
    assert sv.angle_deg((1e-200, 0, 0), (0, 1e100, 0)) == 90.0
    tiny = 5.729577951308232e-08  # degrees(1e-9)
    assert sv.angle_deg((1, 0, 0), (1, 1e-9, 0)) == pytest.approx(tiny, rel=1e-15)
    assert sv.angle_deg((1, 0, 0), (-1, 1e-9, 0)) == pytest.approx(180.0 - tiny, abs=1e-13)
    assert sv.triple((1e100, 0, 0), (0, 1e100, 0), (0, 0, 1e100)) == 1e300
    assert sv.dot((1e100, 1e100, 1e100), (1e100, 1e100, 1e100)) == 3e200
    assert isinstance(sv.cross([1, 0, 0], (0, 1, 0)), tuple) and all(isinstance(x, float) for x in sv.cross(i, j))
    assert sv.dot([1, 2, 3], [Fraction(-2, 1), Fraction(1, 2), 4]) == 11.0
