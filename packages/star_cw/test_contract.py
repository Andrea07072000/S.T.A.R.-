"""Refusals of star_cw with hostile inputs (NaN, inf, huge integers, booleans, text, wrong shapes, singular times).
Verifies: R4 (README).

Every function returns finite floats of the documented shape or raises ValueError: never NaN, never an empty result,
never an impulse computed by dividing by (almost) zero."""
import math

import pytest

import star_cw as cw

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e150, -1e150, True, False, "1", None, 1j, [1.0], (1.0,)]
BAD_SHAPE = [None, 5, "abcdef", b"abcdef", (1, 2, 3, 4, 5), (1, 2, 3, 4, 5, 6, 7), [], {1, 2, 3, 4, 5, 6}, iter([1, 2, 3, 4, 5, 6])]
N = 0.0011
T = 2 * math.pi / N
S = (1.0, 2.0, 3.0, 0.01, 0.02, 0.03)


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(BAD_SHAPE) == 9 and cw.__all__ == ["stm", "propagate", "rendezvous"]
    assert cw.SINGULAR_TOL == 1e-9 and cw.__version__ == "0.1.0"


def test_stm_and_propagate_refuse_hostile_values_and_shapes():
    for bad in BAD:
        with pytest.raises(ValueError):
            cw.stm(bad, 10.0)
        with pytest.raises(ValueError):
            cw.stm(N, bad)
        with pytest.raises(ValueError):
            cw.propagate(S, bad, 10.0)
        with pytest.raises(ValueError):
            cw.propagate(S, N, bad)
        for i in range(6):
            s = list(S)
            s[i] = bad
            with pytest.raises(ValueError):
                cw.propagate(s, N, 10.0)
    for bad in BAD_SHAPE:
        with pytest.raises(ValueError):
            cw.propagate(bad, N, 10.0)


@pytest.mark.parametrize("n", [0, 0.0, -0.0, -1e-3, -1e-300])
def test_mean_motion_must_be_positive(n):
    for call in (lambda: cw.stm(n, 10.0), lambda: cw.propagate(S, n, 10.0), lambda: cw.rendezvous((1, 2, 3), (0, 0, 0), (0, 0, 0), n, 10.0)):
        with pytest.raises(ValueError, match="positive"):
            call()


def test_rendezvous_refuses_hostile_values_and_shapes():
    good = [(1.0, 2.0, 3.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), N, 500.0]
    cw.rendezvous(*good)
    for bad in BAD:
        for k in (3, 4):
            args = list(good)
            args[k] = bad
            with pytest.raises(ValueError):
                cw.rendezvous(*args)
        for k in range(3):
            for i in range(3):
                args = [list(a) if isinstance(a, tuple) else a for a in good]
                args[k][i] = bad
                with pytest.raises(ValueError):
                    cw.rendezvous(*args)
    for bad in (None, 5, "abc", (1, 2), (1, 2, 3, 4), {1, 2, 3}):
        for k in range(3):
            args = list(good)
            args[k] = bad
            with pytest.raises(ValueError):
                cw.rendezvous(*args)


@pytest.mark.parametrize("t", [0.0, -0.0, -1.0, -500.0])
def test_transfer_time_must_be_positive(t):
    with pytest.raises(ValueError, match="positive"):
        cw.rendezvous((1, 2, 3), (0, 0, 0), (0, 0, 0), N, t)


def _in_plane_root():
    """The transfer angle between one and two revolutions where 8 (1 - cos) = 3 theta sin (bisection, independent of the module)."""
    g = lambda th: 8 * (1 - math.cos(th)) - 3 * th * math.sin(th)
    lo, hi = 2.5 * math.pi, 2.95 * math.pi
    assert g(lo) * g(hi) < 0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if g(lo) * g(mid) > 0 else (lo, mid)
    return 0.5 * (lo + hi)


@pytest.mark.parametrize("theta", [math.pi, 2 * math.pi, 3 * math.pi, 4 * math.pi, 1e-6, 2 * math.pi + 1e-10, _in_plane_root()])
def test_singular_transfer_times_are_refused(theta):
    with pytest.raises(ValueError, match="singular"):
        cw.rendezvous((100.0, -200.0, 50.0), (0, 0, 0), (0, 0, 0), N, theta / N)


def test_just_away_from_a_singularity_the_answer_is_finite_and_correct():
    for theta in (math.pi - 1e-3, math.pi + 1e-3, 2 * math.pi - 0.05, _in_plane_root() + 0.01, 0.01):
        t = theta / N
        dv1, dv2 = cw.rendezvous((100.0, -200.0, 50.0), (0.1, 0.0, -0.1), (1.0, 2.0, 3.0), N, t)
        assert all(map(math.isfinite, dv1 + dv2))
        arrive = cw.propagate((100.0, -200.0, 50.0, 0.1 + dv1[0], dv1[1], -0.1 + dv1[2]), N, t)
        assert max(abs(a - b) for a, b in zip(arrive[:3], (1.0, 2.0, 3.0))) < 1e-4


def test_results_are_finite_floats_of_the_documented_shape_and_overflow_is_refused():
    out = cw.propagate(S, N, 1234.5)
    assert isinstance(out, tuple) and len(out) == 6 and all(type(v) is float and math.isfinite(v) for v in out)
    assert cw.propagate([1, 2, 3, 0, 0, 0], 1, 2) == cw.propagate((1.0, 2.0, 3.0, 0.0, 0.0, 0.0), 1.0, 2.0)
    m = cw.stm(N, 1234.5)
    assert isinstance(m, tuple) and all(isinstance(r, tuple) and len(r) == 6 and all(type(v) is float for v in r) for r in m)
    assert cw._finite(x for x in (1.0, 2.0)) == (1.0, 2.0)
    for bad in (NAN, INF, -INF):
        with pytest.raises(ValueError, match="out of range"):
            cw._finite([1.0, bad])
    with pytest.raises(ValueError, match="out of range"):
        cw.propagate((9e149, 9e149, 9e149, 9e149, 9e149, 9e149), 9e149, 9e149)
