"""Refusals of star_iod with hostile inputs (NaN, inf, huge integers, booleans, text, wrong shapes, impossible geometry).
Verifies: R4 (README).

Every function returns three finite floats or raises ValueError: never NaN, never a velocity for positions that do
not define an orbit."""
import math

import pytest

import star_iod as iod

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e100, -1e100, True, False, "1", None, 1j, [1.0], (1.0,)]
BAD_VEC = [None, 5, "abc", b"abc", (1, 2), (1, 2, 3, 4), [], {0: 1, 1: 2, 2: 3}, {1, 2, 3}, iter([1, 2, 3]), (0, 0, 0), (0.0, -0.0, 0.0)]
R = ((0.0, 0.0, 6378.137), (0.0, -4464.696, -5102.509), (0.0, 5740.323, 3189.068))
T = (0.0, 600.0, 1200.0)
CALLS = {"gibbs": lambda r1, r2, r3: iod.gibbs(r1, r2, r3), "herrick_gibbs": lambda r1, r2, r3: iod.herrick_gibbs(r1, r2, r3, *T),
         "separation_deg": lambda r1, r2, r3: iod.separation_deg(r1, r2, r3)}


def test_the_hostile_sets_and_the_constants_are_pinned():
    assert len(BAD) == 14 and len(BAD_VEC) == 12 and iod.__all__ == ["gibbs", "herrick_gibbs", "separation_deg"]
    assert iod.MU_EARTH == 398600.4418 and iod.__version__ == "0.1.0"


@pytest.mark.parametrize("name", sorted(CALLS))
def test_positions_refuse_hostile_values_and_shapes(name):
    f = CALLS[name]
    assert all(type(v) is float and math.isfinite(v) for v in f(*R))
    for k in range(3):
        for bad in BAD_VEC:
            args = list(R)
            args[k] = bad
            with pytest.raises(ValueError):
                f(*args)
        for bad in BAD:
            for i in range(3):
                args = [list(r) for r in R]
                args[k][i] = bad
                with pytest.raises(ValueError):
                    f(*args)


def test_scalars_refuse_hostile_values():
    for bad in BAD:
        with pytest.raises(ValueError):
            iod.gibbs(*R, mu=bad)
        with pytest.raises(ValueError):
            iod.gibbs(*R, coplanar_tol_deg=bad)
        with pytest.raises(ValueError):
            iod.herrick_gibbs(*R, *T, mu=bad)
        for k in range(3):
            t = list(T)
            t[k] = bad
            with pytest.raises(ValueError):
                iod.herrick_gibbs(*R, *t)
    for mu in (0, 0.0, -0.0, -1.0):
        with pytest.raises(ValueError, match="mu must be positive"):
            iod.gibbs(*R, mu=mu)
        with pytest.raises(ValueError, match="mu must be positive"):
            iod.herrick_gibbs(*R, *T, mu=mu)
    for tol in (0, 0.0, -1.0, 90.0000001, 180.0):
        with pytest.raises(ValueError, match="coplanar_tol_deg"):
            iod.gibbs(*R, coplanar_tol_deg=tol)
    assert iod.gibbs(*R, coplanar_tol_deg=90.0) == iod.gibbs(*R) == iod.gibbs(*R, coplanar_tol_deg=1e-9)


@pytest.mark.parametrize("r1, r2, r3, why", [
    ((7000, 0, 0), (0, 7000, 0), (0, 0, 7000), "not coplanar"), ((7000, 0, 600), (0, 7000, 0), (-7000, 0, 0), "not coplanar"),
    ((7000, 0, 0), (7000, 0, 0), (0, 7000, 0), "collinear or coincide"), ((7000, 0, 0), (0, 7000, 0), (0, 7000, 0), "collinear or coincide"),
    ((7000, 0, 0), (8000, 0, 0), (9000, 0, 0), "collinear or coincide"), ((7000, 0, 0), (-7000, 0, 0), (7000, 1e-9, 0), "collinear or coincide"),
    ((7000, 0, 0), (7000, 0, 0), (7000, 0, 0), "collinear or coincide")])
def test_positions_that_do_not_define_an_orbit_are_refused_by_gibbs(r1, r2, r3, why):
    with pytest.raises(ValueError, match=why):
        iod.gibbs(r1, r2, r3)


def test_coplanarity_tolerance_is_the_callers_choice():
    tilted = ((7000.0, 0.0, 7000.0 * math.tan(math.radians(2.0))), (0.0, 7000.0, 0.0), (-7000.0, 0.0, 0.0))
    assert all(map(math.isfinite, iod.gibbs(*tilted)))                       # 2 degrees off: inside the default 3
    with pytest.raises(ValueError, match=r"not coplanar: r1 is 2\.000 deg"):
        iod.gibbs(*tilted, coplanar_tol_deg=1.0)
    with pytest.raises(ValueError, match="not coplanar"):
        iod.herrick_gibbs(*tilted, *T, coplanar_tol_deg=1.0)


def test_order_gives_the_direction_and_a_path_curving_away_from_the_centre_is_refused():
    def p(nu, r=7000.0):
        return (r * math.cos(math.radians(nu)), r * math.sin(math.radians(nu)), 0.0)
    forward, backward = iod.gibbs(p(0), p(40), p(80)), iod.gibbs(p(80), p(40), p(0))
    assert all(a == pytest.approx(-b, rel=1e-12, abs=1e-12) for a, b in zip(forward, backward))     # the same arc flown backwards
    # three points of an ellipse are always in order for one of the two directions: 10 -> 200 -> 100 is the retrograde one
    e = [(8000 * 0.91 / (1 + 0.3 * math.cos(math.radians(n))) * math.cos(math.radians(n)),
          8000 * 0.91 / (1 + 0.3 * math.cos(math.radians(n))) * math.sin(math.radians(n)), 0.0) for n in (10, 100, 200)]
    retro, pro = iod.gibbs(e[0], e[2], e[1]), iod.gibbs(e[1], e[2], e[0])
    assert all(a == pytest.approx(-b, rel=1e-9, abs=1e-9) for a, b in zip(retro, pro))
    for middle in ((1000.0, 1000.0, 0.0), (100.0, 100.0, 0.0)):                                     # inside the chord: the path bends outward
        with pytest.raises(ValueError, match="no orbit about the centre"):
            iod.gibbs((7000, 0, 0), middle, (0, 7000, 0))
    assert all(map(math.isfinite, iod.gibbs((7000, 0, 0), (20000.0, 20000.0, 0.0), (0, 7000, 0))))      # a hyperbola-like arc is an orbit


@pytest.mark.parametrize("t", [(0.0, 0.0, 10.0), (0.0, 10.0, 10.0), (10.0, 5.0, 20.0), (0.0, 10.0, 5.0), (30.0, 20.0, 10.0), (5.0, 5.0, 5.0)])
def test_times_must_be_strictly_increasing(t):
    with pytest.raises(ValueError, match="strictly increasing"):
        iod.herrick_gibbs(*R, *t)


def test_extreme_magnitudes_do_not_return_non_finite_values():
    big = [[c * 1e90 for c in r] for r in R]
    for call in (lambda: iod.gibbs(*big), lambda: iod.herrick_gibbs(*big, *T), lambda: iod.gibbs(*[[c * 1e-150 for c in r] for r in R])):
        try:
            out = call()
        except ValueError:
            continue
        assert all(map(math.isfinite, out))
    assert all(type(v) is float for v in iod.gibbs([0, 0, 6378], [0, -4465, -5103], [0, 5740, 3189]))        # integers and lists
