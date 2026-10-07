"""reviewer guards for star_mrp: conventions, the shadow set, the kinematic equation and the refusals, value by value."""
import math

import pytest

import star_mrp as sm

T = math.tan(math.pi / 8)          # 0.41421356237309503: a quarter turn
THIRD = 1.0 / 3.0


def flat(m):
    return [c for row in m for c in row]


def norm(v):
    return math.sqrt(sum(c * c for c in v))


def mat(a, b):
    return [sum(a[i][k] * b[k][j] for k in range(3)) for i in range(3) for j in range(3)]


# --- conversions, one axis at a time (a sign or an index swapped shows on exactly one of these) ---

@pytest.mark.parametrize("q, expected", [
    ((0.5, 0.5, 0.5, 0.5), (THIRD, THIRD, THIRD)),
    ((0.5, 0.5, 0.0, 0.0), (1.0, 0.0, 0.0)),          # not unit: normalised to (c, c, 0, 0), a quarter turn... see below
    ((0.0, 1.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
    ((0.0, 0.0, 1.0, 0.0), (0.0, 1.0, 0.0)),
    ((0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0)),
    ((2.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ((-3.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ((-0.5, 0.5, 0.5, 0.5), (-THIRD, -THIRD, -THIRD)),
])
def test_mrp_from_quaternion_values(q, expected):
    if q == (0.5, 0.5, 0.0, 0.0):
        # (1, 1, 0, 0) / sqrt(2) is 90 degrees about x: sigma = tan(22.5 deg)
        expected = (T, 0.0, 0.0)
    assert sm.mrp_from_quaternion(q) == pytest.approx(expected, rel=0, abs=2e-16)


def test_mrp_from_quaternion_each_axis_keeps_its_place_and_sign():
    # 0.6^2 + 0.8^2 = 1: sigma = 0.8 / 1.6 = 0.5 on the axis that carries the 0.8, zero elsewhere
    assert sm.mrp_from_quaternion((0.6, 0.8, 0.0, 0.0)) == pytest.approx((0.5, 0.0, 0.0), rel=0, abs=2e-16)
    assert sm.mrp_from_quaternion((0.6, 0.0, 0.8, 0.0)) == pytest.approx((0.0, 0.5, 0.0), rel=0, abs=2e-16)
    assert sm.mrp_from_quaternion((0.6, 0.0, 0.0, -0.8)) == pytest.approx((0.0, 0.0, -0.5), rel=0, abs=2e-16)
    # the same attitude written with the other sign
    assert sm.mrp_from_quaternion((-0.6, 0.0, 0.0, 0.8)) == pytest.approx((0.0, 0.0, -0.5), rel=0, abs=2e-16)


def test_quaternion_from_mrp_values():
    assert sm.quaternion_from_mrp((0, 0, 0)) == (1.0, 0.0, 0.0, 0.0)
    assert sm.quaternion_from_mrp((0, 0, 1)) == (0.0, 0.0, 0.0, 1.0)
    # s2 = 0.25: w = 0.75 / 1.25 = 0.6, v = 2 * 0.5 / 1.25 = 0.8
    assert sm.quaternion_from_mrp((0.5, 0, 0)) == pytest.approx((0.6, 0.8, 0.0, 0.0), rel=0, abs=2e-16)
    assert sm.quaternion_from_mrp((0, -0.5, 0)) == pytest.approx((0.6, 0.0, -0.8, 0.0), rel=0, abs=2e-16)
    assert sm.quaternion_from_mrp((0, 0, 0.5)) == pytest.approx((0.6, 0.0, 0.0, 0.8), rel=0, abs=2e-16)
    # beyond norm 1 the scalar part would be negative: the answer is the same attitude with w >= 0
    assert sm.quaternion_from_mrp((2, 0, 0)) == pytest.approx((0.6, -0.8, 0.0, 0.0), rel=0, abs=2e-16)
    assert sm.quaternion_from_mrp((0, 0, 3)) == pytest.approx((0.8, 0.0, 0.0, -0.6), rel=0, abs=2e-16)
    assert sm.quaternion_from_mrp((0, 0, -THIRD)) == pytest.approx((0.8, 0.0, 0.0, -0.6), rel=0, abs=2e-16)


@pytest.mark.parametrize("s", [(0.1, 0.2, 0.3), (-0.7, 0.1, 0.4), (0.0, 0.0, 1e-8), (0.57, -0.57, 0.57), (1e-150, 0.0, 0.0)])
def test_round_trip_through_the_quaternion(s):
    q = sm.quaternion_from_mrp(s)
    assert norm(q) == pytest.approx(1.0, rel=0, abs=4e-16)
    assert q[0] >= 0.0
    assert sm.mrp_from_quaternion(q) == pytest.approx(s, rel=4e-16, abs=1e-300)


def test_dcm_values_and_orientation():
    assert sm.dcm_from_mrp((0, 0, 0)) == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    # reference to body: a frame turned +90 degrees about z sees reference x along body -y
    assert flat(sm.dcm_from_mrp((0, 0, T))) == pytest.approx([0, 1, 0, -1, 0, 0, 0, 0, 1], rel=0, abs=5e-16)
    assert flat(sm.dcm_from_mrp((T, 0, 0))) == pytest.approx([1, 0, 0, 0, 0, 1, 0, -1, 0], rel=0, abs=5e-16)
    assert flat(sm.dcm_from_mrp((0, T, 0))) == pytest.approx([0, 0, -1, 0, 1, 0, 1, 0, 0], rel=0, abs=5e-16)
    assert flat(sm.dcm_from_mrp((THIRD, THIRD, THIRD))) == pytest.approx([0, 1, 0, 0, 0, 1, 1, 0, 0], rel=0, abs=2e-16)
    # half turns: diag(-1, -1, 1) about z, and so on
    assert flat(sm.dcm_from_mrp((0, 0, 1))) == pytest.approx([-1, 0, 0, 0, -1, 0, 0, 0, 1], rel=0, abs=2e-16)
    assert flat(sm.dcm_from_mrp((1, 0, 0))) == pytest.approx([1, 0, 0, 0, -1, 0, 0, 0, -1], rel=0, abs=2e-16)


@pytest.mark.parametrize("s", [(0.1, 0.2, 0.3), (-0.7, 0.1, 0.4), (2.0, -1.0, 0.5), (0.0, 4.0, 0.0)])
def test_dcm_is_a_rotation_and_the_shadow_has_the_same_one(s):
    c = sm.dcm_from_mrp(s)
    ct = tuple(zip(*c))
    assert mat(c, ct) == pytest.approx([1, 0, 0, 0, 1, 0, 0, 0, 1], rel=0, abs=1e-15)
    det = (c[0][0] * (c[1][1] * c[2][2] - c[1][2] * c[2][1]) - c[0][1] * (c[1][0] * c[2][2] - c[1][2] * c[2][0])
           + c[0][2] * (c[1][0] * c[2][1] - c[1][1] * c[2][0]))
    assert det == pytest.approx(1.0, rel=0, abs=1e-15)
    assert flat(sm.dcm_from_mrp(sm.shadow(s))) == pytest.approx(flat(c), rel=0, abs=1e-15)
    # the rotation axis is left where it is
    moved = [sum(c[i][k] * s[k] for k in range(3)) for i in range(3)]
    assert moved == pytest.approx(s, rel=0, abs=4e-15)


# --- shadow set and switching ---

def test_shadow_values():
    assert sm.shadow((0, 0, 3)) == (0.0, 0.0, -THIRD)
    assert sm.shadow((0.5, 0, 0)) == (-2.0, 0.0, 0.0)
    assert sm.shadow((0, -0.25, 0)) == (0.0, 4.0, 0.0)
    assert sm.shadow((1, 0, 0)) == (-1.0, 0.0, 0.0)
    # s2 = 4 + 4 = 8
    assert sm.shadow((2, 2, 0)) == (-0.25, -0.25, 0.0)
    assert sm.shadow(sm.shadow((0.1, 0.2, 0.3))) == pytest.approx((0.1, 0.2, 0.3), rel=4e-16, abs=0)
    # very small and very large, neither overflowing nor vanishing
    assert sm.shadow((1e-100, 0, 0)) == pytest.approx((-1e100, 0, 0), rel=4e-16, abs=0)
    assert sm.shadow((0, 1e100, 0)) == pytest.approx((0, -1e-100, 0), rel=4e-16, abs=0)


def test_switch_values_and_threshold():
    assert sm.switch((2, 0, 0)) == (-0.5, 0.0, 0.0)
    assert sm.switch((0.5, 0, 0)) == (0.5, 0.0, 0.0)
    assert sm.switch((1, 0, 0)) == (1.0, 0.0, 0.0)
    assert sm.switch((0, 0, -1)) == (0.0, 0.0, -1.0)
    assert sm.switch((0, 0, 0)) == (0.0, 0.0, 0.0)
    assert sm.switch((0.6, 0, 0), 0.5) == pytest.approx((-1.0 / 0.6, 0, 0), rel=2e-16, abs=0)
    assert sm.switch((0.5, 0, 0), 0.5) == (0.5, 0.0, 0.0)
    assert sm.switch((0.5, 0, 0), threshold=0.25) == (-2.0, 0.0, 0.0)
    assert sm.switch((2, 0, 0), 2) == (2.0, 0.0, 0.0)
    assert sm.switch((2, 0, 0), 4.0) == (2.0, 0.0, 0.0)
    assert sm.switch((0, 3, 0), 2.5) == (0.0, -THIRD, 0.0)
    # the norm decides, not one component: (0.8, 0.8, 0) has norm 1.13
    assert sm.switch((0.8, 0.8, 0)) == pytest.approx((-0.625, -0.625, 0.0), rel=4e-16, abs=0)
    assert isinstance(sm.switch((1, 2, 3)), tuple) and all(type(c) is float for c in sm.switch((1, 0, 0)))


@pytest.mark.parametrize("bad", [0, 0.0, -1, -1e-9, float("nan"), float("inf"), True, False, "1", None, 1j, [1.0], 1e151])
def test_switch_refuses_a_bad_threshold(bad):
    with pytest.raises(ValueError, match="threshold"):
        sm.switch((0.1, 0.2, 0.3), bad)


# --- composition ---

def test_compose_values():
    assert sm.compose((0, 0, T), (0, 0, T)) == pytest.approx((0, 0, 1), rel=0, abs=2e-16)
    assert sm.compose((T, 0, 0), (T, 0, 0)) == pytest.approx((1, 0, 0), rel=0, abs=2e-16)
    assert sm.compose((0, 0, 1), (0, 0, 1)) == (0.0, 0.0, 0.0)
    assert sm.compose((0, 0, 1), (0, 0, -1)) == (0.0, 0.0, 0.0)
    assert sm.compose((0, 0, 0), (0, 0, 0)) == (0.0, 0.0, 0.0)
    assert sm.compose((0.1, 0.2, 0.3), (0, 0, 0)) == pytest.approx((0.1, 0.2, 0.3), rel=4e-16, abs=0)
    assert sm.compose((0, 0, 0), (0.1, 0.2, 0.3)) == pytest.approx((0.1, 0.2, 0.3), rel=4e-16, abs=0)
    assert sm.compose((0.1, 0.2, 0.3), (-0.1, -0.2, -0.3)) == pytest.approx((0, 0, 0), rel=0, abs=1e-16)
    # three quarter turns about z are a quarter turn the other way
    assert sm.compose(sm.compose((0, 0, T), (0, 0, T)), (0, 0, T)) == pytest.approx((0, 0, -T), rel=0, abs=4e-16)
    # arguments given through the shadow set mean the same rotations
    assert sm.compose((0, 0, -1 / T), (0, 0, T)) == pytest.approx(sm.compose((0, 0, T), (0, 0, T)), rel=0, abs=4e-16)


def test_compose_order():
    a, b = (T, 0.0, 0.0), (0.0, T, 0.0)
    ab, ba = sm.compose(a, b), sm.compose(b, a)
    # quaternion of "a then b" is q_a q_b: vector part c s (x + y) + s^2 (x cross y), so +z; the other order gives -z
    assert ab == pytest.approx((THIRD, THIRD, THIRD), rel=0, abs=3e-16)
    assert ba == pytest.approx((THIRD, THIRD, -THIRD), rel=0, abs=3e-16)
    assert flat(sm.dcm_from_mrp(ab)) == pytest.approx(mat(sm.dcm_from_mrp(b), sm.dcm_from_mrp(a)), rel=0, abs=1e-15)
    assert flat(sm.dcm_from_mrp(ba)) == pytest.approx(mat(sm.dcm_from_mrp(a), sm.dcm_from_mrp(b)), rel=0, abs=1e-15)


@pytest.mark.parametrize("a, b", [((0.1, 0.2, 0.3), (-0.4, 0.1, 0.2)), ((0.9, 0.0, 0.3), (0.2, 0.8, -0.5)), ((3.0, -1.0, 0.5), (0.2, 0.2, 4.0))])
def test_compose_matches_the_matrix_product_and_stays_short(a, b):
    c = sm.compose(a, b)
    assert norm(c) <= 1.0 + 1e-15
    assert flat(sm.dcm_from_mrp(c)) == pytest.approx(mat(sm.dcm_from_mrp(b), sm.dcm_from_mrp(a)), rel=0, abs=2e-15)


# --- rotation vectors ---

def test_rotation_vector_values():
    assert sm.rotation_vector_from_mrp((0, 0, 0)) == (0.0, 0.0, 0.0)
    assert sm.rotation_vector_from_mrp((0, 0, 1)) == (0.0, 0.0, math.pi)
    assert sm.rotation_vector_from_mrp((T, 0, 0)) == pytest.approx((math.pi / 2, 0, 0), rel=0, abs=3e-16)
    assert sm.rotation_vector_from_mrp((0, -T, 0)) == pytest.approx((0, -math.pi / 2, 0), rel=0, abs=3e-16)
    assert sm.rotation_vector_from_mrp((3, 0, 0)) == pytest.approx((-4 * math.atan(THIRD), 0, 0), rel=0, abs=3e-16)
    each = 2 * math.pi / 3 / math.sqrt(3)
    assert sm.rotation_vector_from_mrp((THIRD, THIRD, THIRD)) == pytest.approx((each, each, each), rel=0, abs=5e-16)
    # for a small rotation the vector is four times the MRP
    assert sm.rotation_vector_from_mrp((1e-9, -2e-9, 0)) == pytest.approx((4e-9, -8e-9, 0), rel=1e-15, abs=0)
    assert sm.rotation_vector_from_mrp((1e-200, 0, 0)) == pytest.approx((4e-200, 0, 0), rel=1e-15, abs=0)


def test_mrp_from_rotation_vector_values():
    assert sm.mrp_from_rotation_vector((0, 0, 0)) == (0.0, 0.0, 0.0)
    assert sm.mrp_from_rotation_vector((math.pi / 2, 0, 0)) == pytest.approx((T, 0, 0), rel=0, abs=1e-16)
    assert sm.mrp_from_rotation_vector((0, -math.pi / 2, 0)) == pytest.approx((0, -T, 0), rel=0, abs=1e-16)
    assert sm.mrp_from_rotation_vector((0, 0, math.pi)) == pytest.approx((0, 0, 1), rel=0, abs=2e-16)
    assert sm.mrp_from_rotation_vector((0, 0, 3 * math.pi / 2)) == pytest.approx((0, 0, -T), rel=0, abs=1e-15)
    assert sm.mrp_from_rotation_vector((0, 2 * math.pi, 0)) == pytest.approx((0, 0, 0), rel=0, abs=1e-16)
    assert sm.mrp_from_rotation_vector((5 * math.pi / 2, 0, 0)) == pytest.approx((T, 0, 0), rel=0, abs=2e-15)
    assert sm.mrp_from_rotation_vector((4e-9, -8e-9, 0)) == pytest.approx((1e-9, -2e-9, 0), rel=1e-15, abs=0)
    assert sm.mrp_from_rotation_vector((4e-200, 0, 0)) == pytest.approx((1e-200, 0, 0), rel=1e-15, abs=0)


@pytest.mark.parametrize("v", [(0.3, -0.2, 0.1), (1.0, 2.0, -1.5), (0.0, 0.0, 3.0), (1e-6, 0.0, 0.0)])
def test_rotation_vector_round_trip(v):
    assert sm.rotation_vector_from_mrp(sm.mrp_from_rotation_vector(v)) == pytest.approx(v, rel=0, abs=2e-15)


# --- kinematic equation ---

def test_mrp_rate_values():
    assert sm.mrp_rate((0, 0, 0), (0.4, 0, 0)) == (0.1, 0.0, 0.0)
    assert sm.mrp_rate((0, 0, 0), (0, -0.4, 0.8)) == (0.0, -0.1, 0.2)
    assert sm.mrp_rate((0, 0, 1), (0, 0, 0.4)) == pytest.approx((0, 0, 0.2), rel=0, abs=1e-17)
    assert sm.mrp_rate((0.5, 0, 0), (0, 0.4, 0)) == pytest.approx((0, 0.075, 0.1), rel=0, abs=1e-16)
    # the cross term has a sign: sigma along x, omega along z gives -y
    assert sm.mrp_rate((0.5, 0, 0), (0, 0, 0.4)) == pytest.approx((0, -0.1, 0.075), rel=0, abs=1e-16)
    assert sm.mrp_rate((0, 0.5, 0), (0.4, 0, 0)) == pytest.approx((0.075, 0, -0.1), rel=0, abs=1e-16)
    # by the formula, all three terms at once: s2 = 0.14, s.w = 0.006, s x w = (0.012, 0, -0.004)
    assert sm.mrp_rate((0.1, 0.2, 0.3), (0.01, -0.02, 0.03)) == pytest.approx((0.00845, -0.0037, 0.00535), rel=0, abs=2e-18)
    # beyond norm 1 the first term changes sign: (1 - 4) * 0.4 / 4 = -0.3
    assert sm.mrp_rate((2, 0, 0), (0, 0.4, 0)) == pytest.approx((0, -0.3, 0.4), rel=0, abs=1e-16)
    assert sm.mrp_rate((0.3, -0.2, 0.9), (0, 0, 0)) == (0.0, 0.0, 0.0)


def test_mrp_rate_is_linear_in_the_body_rate():
    s, w1, w2 = (0.3, -0.2, 0.5), (0.01, 0.02, -0.03), (-0.05, 0.01, 0.02)
    r1, r2 = sm.mrp_rate(s, w1), sm.mrp_rate(s, w2)
    both = sm.mrp_rate(s, tuple(2 * a + b for a, b in zip(w1, w2)))
    assert both == pytest.approx(tuple(2 * a + b for a, b in zip(r1, r2)), rel=0, abs=1e-17)


@pytest.mark.parametrize("s, w", [((0.1, 0.2, 0.3), (0.5, -0.3, 0.2)), ((0.0, 0.0, 0.0), (0.1, 0.2, 0.3)), ((-0.6, 0.3, 0.1), (0.0, 0.0, 1.0))])
def test_mrp_rate_agrees_with_composing_a_small_rotation(s, w):
    dt = 1e-6
    step = sm.compose(s, sm.mrp_from_rotation_vector(tuple(c * dt for c in w)))
    slope = tuple((a - b) / dt for a, b in zip(step, s))
    assert slope == pytest.approx(sm.mrp_rate(s, w), rel=0, abs=2e-6)


# --- refusals ---

BAD_VECTORS = [None, 1.0, "abc", b"abc", {0.1, 0.2, 0.3}, {1: 1, 2: 2, 3: 3}, range(3), (1, 2), (1, 2, 3, 4), [], (x for x in (1, 2, 3))]
BAD_PARTS = [True, False, "1", None, 1j, float("nan"), float("inf"), float("-inf"), 1.1e150, -1.1e150, [1.0]]
ONE = (sm.quaternion_from_mrp, sm.shadow, sm.switch, sm.dcm_from_mrp, sm.rotation_vector_from_mrp, sm.mrp_from_rotation_vector)


@pytest.mark.parametrize("f", ONE)
@pytest.mark.parametrize("bad", BAD_VECTORS[:10])
def test_single_argument_functions_refuse_a_bad_vector(f, bad):
    with pytest.raises(ValueError):
        f(bad)


@pytest.mark.parametrize("f", ONE)
@pytest.mark.parametrize("bad", BAD_PARTS)
@pytest.mark.parametrize("place", [0, 1, 2])
def test_single_argument_functions_refuse_a_bad_component(f, bad, place):
    v = [0.1, 0.2, 0.3]
    v[place] = bad
    with pytest.raises(ValueError):
        f(v)


@pytest.mark.parametrize("f", [sm.compose, sm.mrp_rate])
@pytest.mark.parametrize("bad", BAD_VECTORS[:10] + [(0.1, True, 0.3), (0.1, 0.2, float("nan")), (float("inf"), 0, 0), (0, "2", 0), (0, 0, 1.1e150)])
def test_two_argument_functions_refuse_either_argument(f, bad):
    with pytest.raises(ValueError):
        f(bad, (0.1, 0.2, 0.3))
    with pytest.raises(ValueError):
        f((0.1, 0.2, 0.3), bad)


@pytest.mark.parametrize("bad", [None, 1.0, "abcd", (1, 2, 3), (1, 2, 3, 4, 5), [], {1, 2, 3, 4}, (1, True, 0, 0), (1, 0, float("nan"), 0),
                                 (float("inf"), 0, 0, 0), (1, 0, 0, "0"), (1, 0, 0, None), (1.1e150, 0, 0, 0), (1, 0, 0, 1j)])
def test_mrp_from_quaternion_refuses(bad):
    with pytest.raises(ValueError):
        sm.mrp_from_quaternion(bad)


def test_named_refusals():
    with pytest.raises(ValueError, match="zero quaternion"):
        sm.mrp_from_quaternion((0, 0, 0, 0))
    with pytest.raises(ValueError, match="zero quaternion"):
        sm.mrp_from_quaternion((0.0, -0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="no shadow set"):
        sm.shadow((0, 0, 0))
    with pytest.raises(ValueError, match="no shadow set"):
        sm.shadow((0.0, -0.0, 0.0))
    assert sm.switch((0, 0, 0), 1e-3) == (0.0, 0.0, 0.0)


def test_tiny_vectors_do_not_vanish():
    # the squared norm of 1e-200 underflows to zero: the answers must not
    assert sm.shadow((1e-200, 0, 0)) == pytest.approx((-1e200, 0, 0), rel=4e-16, abs=0)
    assert sm.shadow((3e-170, 4e-170, 0)) == pytest.approx((-1.2e169, -1.6e169, 0), rel=1e-15, abs=0)
    assert sm.switch((1e-200, 0, 0), 1e-250) == pytest.approx((-1e200, 0, 0), rel=4e-16, abs=0)
    assert sm.switch((1e-200, 0, 0), 1e-199) == (1e-200, 0.0, 0.0)
    assert sm.switch((0, 1e100, 0), 1e120) == (0.0, 1e100, 0.0)
    assert sm.rotation_vector_from_mrp((0, 0, -1e-300)) == pytest.approx((0, 0, -4e-300), rel=1e-15, abs=0)
    assert sm.quaternion_from_mrp((1e-200, 0, 0)) == (1.0, 2e-200, 0.0, 0.0)


def test_limits_of_the_accepted_range():
    # 1e150 is accepted, and the answers stay finite
    assert sm.shadow((1e150, 0, 0)) == pytest.approx((-1e-150, 0, 0), rel=4e-16, abs=0)
    assert sm.quaternion_from_mrp((1e150, 0, 0)) == pytest.approx((1.0, -2e-150, 0.0, 0.0), rel=4e-16, abs=0)
    assert sm.mrp_from_quaternion((1e150, 1e150, 1e150, 1e150)) == pytest.approx((THIRD, THIRD, THIRD), rel=0, abs=2e-16)
    assert sm.mrp_from_quaternion((1e-150, 1e-150, 1e-150, 1e-150)) == pytest.approx((THIRD, THIRD, THIRD), rel=0, abs=2e-16)
    assert flat(sm.dcm_from_mrp((1e150, 0, 0))) == pytest.approx([1, 0, 0, 0, 1, 0, 0, 0, 1], rel=0, abs=1e-15)
    assert sm.rotation_vector_from_mrp((0, 1e150, 0)) == pytest.approx((0, -4e-150, 0), rel=1e-15, abs=0)
    assert sm.compose((1e150, 0, 0), (0, 0, T)) == pytest.approx((0, 0, T), rel=0, abs=1e-15)
    assert all(math.isfinite(c) for c in sm.mrp_rate((1e100, 0, 0), (0, 1e-3, 0)))


def test_inputs_are_not_modified_and_ints_are_accepted():
    s, w = [1, 2, 3], [0, 0, 1]
    sm.shadow(s), sm.switch(s), sm.compose(s, w), sm.mrp_rate(s, w), sm.dcm_from_mrp(s)
    assert s == [1, 2, 3] and w == [0, 0, 1]
    assert sm.shadow([0, 0, 2]) == sm.shadow((0.0, 0.0, 2.0)) == (0.0, 0.0, -0.5)
