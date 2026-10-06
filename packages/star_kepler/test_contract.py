"""Hostile-input contract of star_kepler.propagate, and the closed-form corpus of the propagation audit.
Verifies: R3, R4 (README).

Every invalid input raises ValueError before any iteration (a third-party solver was measured never returning on NaN:
each call here runs with a deadline, so a regression to an endless loop FAILS instead of hanging the suite). The corpus
is the one of star_audit.propagation_audit rebuilt here from the closed-form equations (no dependency on that package):
450 known orbits, eccentricity 0 to 0.95, 0 and 10 whole revolutions."""
import itertools
import math
import threading

import pytest

from star_kepler import MU_EARTH as MU, propagate

NAN, INF = math.nan, math.inf
R0, V0 = (7000.0, 0.0, 0.0), (0.0, 7.5, 0.0)


def call(*args, seconds=20.0, **kw):
    out = {}

    def run():
        try:
            out["v"] = propagate(*args, **kw)
        except BaseException as e:  # noqa: BLE001
            out["e"] = e
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), f"propagate did not return within {seconds} s"
    if "e" in out:
        raise out["e"]
    return out["v"]


@pytest.mark.parametrize("args", [
    (R0, V0, NAN), (R0, V0, INF), (R0, V0, -INF), ((NAN, 0.0, 0.0), V0, 100.0), (R0, (0.0, INF, 0.0), 100.0),
    ((0.0, 0.0, 0.0), V0, 100.0), (R0, V0, 100.0, -1.0), (R0, V0, 100.0, 0.0), (R0, V0, 100.0, NAN),
    (R0, (3.0, 0.0, 0.0), 100.0), (R0, (0.0, 0.0, 0.0), 100.0), ((7000.0, 0.0), V0, 100.0), (R0, (0.0, 7.5), 100.0),
])
def test_invalid_input_is_a_value_error_and_returns_promptly(args):
    with pytest.raises(ValueError):
        call(*args)


def test_huge_and_negative_times_are_answered_not_refused():
    for tof in (1e12, -3600.0, 1e-9):
        r, v = call(R0, V0, tof)
        assert all(map(math.isfinite, (*r, *v)))
        assert abs(0.5 * sum(x * x for x in v) - MU / math.dist(r, (0, 0, 0)) - (0.5 * 7.5 ** 2 - MU / 7000.0)) < 1e-8


def test_iteration_budget_too_small_is_refused_not_answered():
    with pytest.raises(RuntimeError):
        call((6800.0, 500.0, 1200.0), (-1.0, 7.2, 2.5), 5000.0, max_iter=1)


def _rot(i, raan, argp, x, y):
    cO, sO, ci, si, cw, sw = math.cos(raan), math.sin(raan), math.cos(i), math.sin(i), math.cos(argp), math.sin(argp)
    return [(cO * cw - sO * sw * ci) * x + (-cO * sw - sO * cw * ci) * y,
            (sO * cw + cO * sw * ci) * x + (-sO * sw + cO * cw * ci) * y, (sw * si) * x + (cw * si) * y]


def _state(a, e, inc, nu):
    p = a * (1 - e * e)
    h, rm = math.sqrt(MU * p), p / (1 + e * math.cos(nu))
    raan, argp = math.radians(40.0), math.radians(25.0)
    return (_rot(inc, raan, argp, rm * math.cos(nu), rm * math.sin(nu)),
            _rot(inc, raan, argp, -MU / h * math.sin(nu), MU / h * (e + math.cos(nu))))


def _mean(nu, e):
    E = 2.0 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
    return E - e * math.sin(E)


GRID = list(itertools.product((7000.0, 26600.0, 42164.0), (0.0, 0.1, 0.5, 0.8, 0.95), (5.0, 63.4, 98.0),
                              (15.0, 100.0, 179.0, 181.0, 300.0), (0, 10)))


@pytest.mark.parametrize("e", (0.0, 0.1, 0.5, 0.8, 0.95))
def test_known_orbits_to_a_millimetre_including_ten_revolutions(e):
    worst_r = worst_v = 0.0
    n = 0
    for k, (a, ecc, inc, dnu, revs) in enumerate(GRID):
        if ecc != e:
            continue
        nu1 = math.radians((41.0 * k) % 360.0)
        r0, v0 = _state(a, e, math.radians(inc), nu1)
        rt, vt = _state(a, e, math.radians(inc), nu1 + math.radians(dnu))
        dM = (_mean(nu1 + math.radians(dnu), e) - _mean(nu1, e)) % (2 * math.pi)
        # 13 = measured worst case of the safeguarded Newton on this corpus (median 5): a variant that falls back
        # to plain bisection needs ~50 and fails here
        r, v = propagate(r0, v0, (dM + 2 * math.pi * revs) / math.sqrt(MU / a ** 3), max_iter=13)
        worst_r, worst_v, n = max(worst_r, math.dist(r, rt)), max(worst_v, math.dist(v, vt)), n + 1
    assert n == 90 and worst_r < 1e-6 and worst_v < 1e-8            # 1e-6 km = 1 mm


@pytest.mark.parametrize("c", [0.001, -0.002, 0.0037, 1.0, -1e-6])
@pytest.mark.parametrize("r", [(1000.0, 2000.0, 3000.0), (-6871.3, 412.9, 1777.1), (0.3, -0.7, 9000.0)])
def test_rectilinear_motion_in_any_direction_is_refused(r, c):
    with pytest.raises(ValueError):
        call(r, tuple(c * x for x in r), 100.0)


def test_a_slightly_non_rectilinear_orbit_is_not_refused():
    r, v = call((7000.0, 0.0, 0.0), (5.0, 0.01, 0.0), 100.0)        # sin of the flight-path offset = 2e-3 >> 1e-6
    assert all(map(math.isfinite, (*r, *v)))
