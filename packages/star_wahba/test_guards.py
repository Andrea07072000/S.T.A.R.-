"""Guard tests of star_wahba written by the reviewer: attitudes built here from an axis and an angle with Rodrigues'
formula (no quaternion), optimality checked by the loss itself (no eigenvector), hand cases, and every refusal by
name. Relative tolerances carry abs=0."""
import math
import random

import pytest

import star_wahba as sw

IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
QUARTER_Z = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def frame_turned(axis, angle):
    """Attitude matrix (reference to body) of a body frame turned by `angle` about `axis`: the transpose of Rodrigues'
    rotation of a vector, R = I cos + (1 - cos) n n^T + sin [n x]."""
    size = math.sqrt(sum(c * c for c in axis))
    n = [c / size for c in axis]
    c, s = math.cos(angle), math.sin(angle)
    cross = ((0.0, -n[2], n[1]), (n[2], 0.0, -n[0]), (-n[1], n[0], 0.0))
    rotation = [[c * (i == j) + (1 - c) * n[i] * n[j] + s * cross[i][j] for j in range(3)] for i in range(3)]
    return tuple(tuple(rotation[j][i] for j in range(3)) for i in range(3))


def apply(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def flat(m):
    return [c for row in m for c in row]


def random_direction(rnd):
    return tuple(rnd.gauss(0, 1) for _ in range(3))


def angle_between(u, v):
    cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return math.atan2(math.sqrt(sum(c * c for c in cross)), sum(a * b for a, b in zip(u, v)))


def test_hand_cases():
    refs, bodies = [(1, 0, 0), (0, 1, 0)], [(0, -1, 0), (1, 0, 0)]                          # the body is turned +90 deg about z
    assert flat(sw.triad(refs[0], refs[1], bodies[0], bodies[1])) == pytest.approx(flat(QUARTER_Z), abs=1e-15)
    q = sw.q_method(refs, bodies)
    assert q == pytest.approx((math.sqrt(0.5), 0.0, 0.0, math.sqrt(0.5)), abs=1e-15)
    assert flat(sw.rotation_matrix(q)) == pytest.approx(flat(QUARTER_Z), abs=1e-15) and sw.wahba_loss(q, refs, bodies) == pytest.approx(0.0, abs=1e-30)
    assert sw.q_method(refs, refs) == pytest.approx((1.0, 0.0, 0.0, 0.0), abs=1e-15) and flat(sw.triad(refs[0], refs[1], refs[0], refs[1])) == flat(IDENTITY)
    half_turn = sw.rotation_matrix(sw.q_method([(0, 1, 0), (0, 0, 1)], [(0, -1, 0), (0, 0, -1)]))
    assert flat(half_turn) == pytest.approx([1, 0, 0, 0, -1, 0, 0, 0, -1], abs=1e-15)
    t = 0.3
    assert flat(sw.rotation_matrix((math.cos(t / 2), math.sin(t / 2), 0, 0))) == pytest.approx([1, 0, 0, 0, math.cos(t), math.sin(t), 0, -math.sin(t), math.cos(t)], abs=1e-15)
    assert flat(sw.rotation_matrix((math.cos(t / 2), 0, math.sin(t / 2), 0))) == pytest.approx([math.cos(t), 0, -math.sin(t), 0, 1, 0, math.sin(t), 0, math.cos(t)], abs=1e-15)
    assert flat(sw.rotation_matrix((math.cos(t / 2), 0, 0, math.sin(t / 2)))) == pytest.approx([math.cos(t), math.sin(t), 0, -math.sin(t), math.cos(t), 0, 0, 0, 1], abs=1e-15)
    assert sw.rotation_matrix((2, 0, 0, 0)) == IDENTITY and sw.rotation_matrix([0.3, -0.4, 0.5, 0.6]) == sw.rotation_matrix((-0.3, 0.4, -0.5, -0.6))


@pytest.mark.parametrize("seed", range(6))
def test_noise_free_observations_give_back_the_attitude(seed):
    rnd = random.Random(seed)
    for _ in range(40):
        truth = frame_turned(random_direction(rnd), rnd.uniform(-3.1, 3.1))
        n = rnd.randint(2, 7)
        refs = [random_direction(rnd)]
        while len(refs) < n:
            v = random_direction(rnd)
            if len(refs) > 1 or 0.4 < angle_between(refs[0], v) < math.pi - 0.4:
                refs.append(v)
        bodies = [apply(truth, v) for v in refs]
        weights = [rnd.uniform(0.2, 5.0) for _ in refs]
        q = sw.q_method(refs, bodies, weights)
        assert flat(sw.rotation_matrix(q)) == pytest.approx(flat(truth), abs=1e-13) and q[0] >= 0.0
        assert math.sqrt(sum(c * c for c in q)) == pytest.approx(1.0, rel=4e-16, abs=0)
        assert flat(sw.triad(refs[0], refs[1], bodies[0], bodies[1])) == pytest.approx(flat(truth), abs=1e-13)
        assert sw.wahba_loss(q, refs, bodies, weights) < 1e-25
        # only directions and relative weights count
        scaled = sw.q_method([tuple(3.7 * c for c in v) for v in refs], [tuple(0.01 * c for c in v) for v in bodies], [7.0 * w for w in weights])
        assert scaled == pytest.approx(q, abs=1e-13)


def test_every_matrix_is_a_proper_rotation():
    rnd = random.Random(99)
    for _ in range(100):
        refs = [random_direction(rnd) for _ in range(4)]
        bodies = [random_direction(rnd) for _ in range(4)]                                  # unrelated: far from any exact attitude
        for m in (sw.rotation_matrix(sw.q_method(refs, bodies)), sw.triad(refs[0], refs[1], bodies[0], bodies[1]), sw.rotation_matrix(random_direction(rnd) + (rnd.gauss(0, 1),))):
            product = [sum(m[i][k] * m[j][k] for k in range(3)) for i in range(3) for j in range(3)]
            assert product == pytest.approx(flat(IDENTITY), abs=1e-14)
            det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
            assert det == pytest.approx(1.0, rel=1e-14, abs=0)
            assert isinstance(m, tuple) and all(isinstance(row, tuple) and all(isinstance(c, float) for c in row) for row in m)


def test_the_q_method_is_the_minimum_of_the_loss():
    rnd = random.Random(5)
    for _ in range(30):
        truth = frame_turned(random_direction(rnd), rnd.uniform(-3, 3))
        refs = [random_direction(rnd) for _ in range(5)]
        bodies = [tuple(c + rnd.gauss(0, 0.05) for c in apply(truth, v)) for v in refs]
        weights = [rnd.uniform(0.2, 5.0) for _ in refs]
        q = sw.q_method(refs, bodies, weights)
        best = sw.wahba_loss(q, refs, bodies, weights)
        assert 0.0 < best < 0.1
        for _ in range(40):                                                                # nearby attitudes: turned by a small angle about a random axis
            axis, angle = random_direction(rnd), rnd.choice([1e-3, 1e-5])
            size = math.sqrt(sum(c * c for c in axis))
            dw, dv = math.cos(angle / 2), [math.sin(angle / 2) * c / size for c in axis]
            w, x, y, z = q
            near = (w * dw - x * dv[0] - y * dv[1] - z * dv[2], w * dv[0] + x * dw + y * dv[2] - z * dv[1], w * dv[1] - x * dv[2] + y * dw + z * dv[0],
                    w * dv[2] + x * dv[1] - y * dv[0] + z * dw)
            assert sw.wahba_loss(near, refs, bodies, weights) > best
        assert all(sw.wahba_loss(random_direction(rnd) + (rnd.gauss(0, 1),), refs, bodies, weights) > best for _ in range(50))
        assert sw.wahba_loss(sw.q_method(refs, bodies), refs, bodies, weights) >= best      # the optimum of other weights is not better for these


def test_inconsistent_pairs_share_the_error_and_triad_does_not():
    refs = [(1, 0, 0), (0, 1, 0)]                                                           # 90 deg apart
    a = math.radians(80)
    bodies = [(1, 0, 0), (math.cos(a), math.sin(a), 0)]                                     # 80 deg apart
    q = sw.q_method(refs, bodies)
    assert sw.wahba_loss(q, refs, bodies) == pytest.approx(1 - math.cos(math.radians(5)), rel=1e-13, abs=0)       # each direction ends 5 deg away
    m = sw.rotation_matrix(q)
    assert angle_between(apply(m, refs[0]), bodies[0]) == pytest.approx(math.radians(5), rel=1e-12, abs=0)
    assert angle_between(apply(m, refs[1]), bodies[1]) == pytest.approx(math.radians(5), rel=1e-12, abs=0)
    t = sw.triad(refs[0], refs[1], bodies[0], bodies[1])
    assert apply(t, refs[0]) == pytest.approx(bodies[0], abs=1e-15)                         # TRIAD: the first pair exactly ...
    assert angle_between(apply(t, refs[1]), bodies[1]) == pytest.approx(math.radians(10), rel=1e-12, abs=0)       # ... the second takes all the error
    swapped = sw.triad(refs[1], refs[0], bodies[1], bodies[0])
    assert apply(swapped, refs[1]) == pytest.approx(bodies[1], abs=1e-15) and flat(swapped) != pytest.approx(flat(t), abs=1e-3)
    heavy = sw.rotation_matrix(sw.q_method(refs, bodies, [1e6, 1.0]))                       # a heavy first observation approaches TRIAD
    assert angle_between(apply(heavy, refs[0]), bodies[0]) == pytest.approx(math.sin(math.radians(10)) * 1e-6, rel=1e-3, abs=0)      # to first order (w2 / w1) sin(inconsistency)
    assert sw.wahba_loss(q, refs, bodies, [3.0, 3.0]) == pytest.approx(sw.wahba_loss(q, refs, bodies), rel=1e-15, abs=0)      # weights are normalised
    assert sw.wahba_loss((1, 0, 0, 0), refs, [(-1, 0, 0), (0, -1, 0)]) == pytest.approx(2.0, rel=1e-15, abs=0)               # the largest loss there is


def test_limits_and_sign_rule():
    assert (sw.MAX_PAIRS, sw.PARALLEL, sw.__version__, sw.__all__) == (1000, 1e-12, "0.1.0", ["triad", "q_method", "rotation_matrix", "wahba_loss"])
    many = [(1, 0, 0), (0, 1, 0)] * 500
    assert sw.q_method(many, many) == pytest.approx((1.0, 0.0, 0.0, 0.0), abs=1e-14)
    with pytest.raises(ValueError, match="between 2 and 1000 pairs"):
        sw.q_method(many + [(0, 0, 1)], many + [(0, 0, 1)])
    for angle in (3.0, -3.0, 3.14159, 6.0):                                                 # past half a turn the scalar part would be negative: the sign is flipped
        q = sw.q_method([(1, 0, 0), (0, 1, 0)], [apply(frame_turned((0, 0, 1), angle), v) for v in ((1, 0, 0), (0, 1, 0))])
        assert q[0] >= 0.0 and flat(sw.rotation_matrix(q)) == pytest.approx(flat(frame_turned((0, 0, 1), angle)), abs=1e-14)
    tiny, huge = (1e-200, 2e-200, 0.0), (1e200, 0.0, 3e200)                                 # no overflow or underflow in the norms
    assert flat(sw.triad(tiny, huge, tiny, huge)) == pytest.approx(flat(IDENTITY), abs=1e-15)
    nearly = [(1, 0, 0), (1, 1e-9, 0)]                                                      # 1e-9 rad apart: accepted (the README warns about sensitivity)
    assert flat(sw.triad(nearly[0], nearly[1], nearly[0], nearly[1])) == pytest.approx(flat(IDENTITY), abs=1e-6)


def test_refusals_name_the_argument():
    good = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    for bad in ((1, 0), (1, 0, 0, 0), "abc", None, 1.0, {1, 2, 3}):
        for position, name in enumerate(("r1", "r2", "b1", "b2")):
            args = [good[0], good[1], good[0], good[1]]
            args[position] = bad
            with pytest.raises(ValueError, match=f"{name} must be a list or tuple of 3 numbers"):
                sw.triad(*args)
        with pytest.raises(ValueError, match="a reference vector must be a list or tuple of 3 numbers"):
            sw.q_method([good[0], bad], [good[0], good[1]])
        with pytest.raises(ValueError, match="a body vector must be a list or tuple of 3 numbers"):
            sw.q_method([good[0], good[1]], [bad, good[1]])
    for bad in (True, "1", None, float("nan"), float("inf"), 1j, 10 ** 400):
        with pytest.raises(ValueError, match="r1 must hold finite real numbers"):
            sw.triad((1.0, bad, 0.0), good[1], good[0], good[1])
        with pytest.raises(ValueError, match="q must hold finite real numbers"):
            sw.rotation_matrix((1.0, 0.0, bad, 0.0))
        with pytest.raises(ValueError, match="weights must be positive finite numbers"):
            sw.q_method(list(good), list(good), [1.0, bad])
    with pytest.raises(ValueError, match="b2 is the zero vector"):
        sw.triad(good[0], good[1], good[0], (0, 0, 0))
    for second in ((2, 0, 0), (-1, 0, 0), (1, 1e-13, 0)):
        with pytest.raises(ValueError, match="the two reference directions are parallel"):
            sw.triad(good[0], second, good[0], good[1])
        with pytest.raises(ValueError, match="the two body directions are parallel"):
            sw.triad(good[0], good[1], good[0], second)
    for refs, bodies in (([(1, 0, 0), (1, 0, 0)], [(0, 1, 0), (0, 1, 0)]), ([(1, 0, 0), (2, 0, 0), (-1, 0, 0)], [(0, 1, 0), (0, 1, 0), (0, -1, 0)])):
        with pytest.raises(ValueError, match="do not fix an attitude"):
            sw.q_method(refs, bodies)
    for refs, bodies in (([good[0]], [good[0]]), ([], []), ([good[0]] * 1001, [good[0]] * 1001)):
        with pytest.raises(ValueError, match="between 2 and 1000 pairs"):
            sw.q_method(refs, bodies)
    for refs, bodies in (([good[0], good[1]], [good[0]]), ("ab", [good[0], good[1]]), ([good[0], good[1]], None)):
        with pytest.raises(ValueError, match="same length"):
            sw.q_method(refs, bodies)
        with pytest.raises(ValueError, match="same length"):
            sw.wahba_loss((1, 0, 0, 0), refs, bodies)
    for weights in ([1.0], [1.0, 1.0, 1.0], "ab", 2.0):
        with pytest.raises(ValueError, match="weights must be as many as the pairs"):
            sw.q_method(list(good), list(good), weights)
    for weights in ([1.0, 0.0], [1.0, -1.0], [-5e-324, 1.0]):
        with pytest.raises(ValueError, match="weights must be positive finite numbers"):
            sw.wahba_loss((1, 0, 0, 0), list(good), list(good), weights)
    for bad in ((1, 0, 0), (1, 0, 0, 0, 0), "wxyz", None):
        with pytest.raises(ValueError, match="q must be a list or tuple of 4 numbers"):
            sw.rotation_matrix(bad)
    with pytest.raises(ValueError, match="q is the zero quaternion"):
        sw.wahba_loss((0, 0, 0, 0), list(good), list(good))
