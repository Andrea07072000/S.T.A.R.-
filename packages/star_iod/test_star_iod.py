"""star_iod against published examples and orbits whose velocity is known in closed form.
Verifies: R1, R2, R3 (README).

Published: Vallado, Fundamentals of Astrodynamics and Applications, Example 7-3 (Gibbs): r1 = (0, 0, 6378.137),
r2 = (0, -4464.696, -5102.509), r3 = (0, 5740.323, 3189.068) km -> v2 = (0, 5.531148, -5.191806) km/s; Example 7-4
(Herrick-Gibbs): three positions 76.48 s and 76.56 s apart -> v2 = (-6.441557, 3.777559, ...) km/s. Only the first two
components of Example 7-4 are asserted. For the third, the value on record here (-1.720469) differs from the computed
one (-1.720568) by 1e-4 km/s; the book was not available to settle it and a conic-equation check does not discriminate
between the two (both within 2 m), so NO number is asserted for it.
Truth without any solver: positions and velocity of a circular and of an elliptic orbit from the conic equations.
The comparison with Orekit IodGibbs and with NAIF conics on 240 orbits is in crosscheck_iod.py."""
import math

import pytest

import star_iod as iod

MU = 398600.4418
G = ((0.0, 0.0, 6378.137), (0.0, -4464.696, -5102.509), (0.0, 5740.323, 3189.068))
HG = ((3419.85564, 6019.82602, 2784.60022), (2935.91195, 6326.18324, 2660.59584), (2434.95202, 6597.38674, 2521.52311))
HG_T = (0.0, 76.48, 153.04)


def conic(a, e, nu_deg, inc_deg=0.0):
    """Position and velocity on an orbit of semi-major axis a and eccentricity e at true anomaly nu (perifocal equations)."""
    nu, i = math.radians(nu_deg), math.radians(inc_deg)
    p = a * (1 - e * e)
    r = p / (1 + e * math.cos(nu))
    x, y = r * math.cos(nu), r * math.sin(nu)
    k = math.sqrt(MU / p)
    vx, vy = -k * math.sin(nu), k * (e + math.cos(nu))
    return (x, y * math.cos(i), y * math.sin(i)), (vx, vy * math.cos(i), vy * math.sin(i))


def rel(a, b):
    return math.hypot(*[x - y for x, y in zip(a, b)]) / math.hypot(*b)


def test_vallado_example_7_3_gibbs():
    v = iod.gibbs(*G)
    assert len(v) == 3 and all(abs(a - b) < 5e-7 for a, b in zip(v, (0.0, 5.531148, -5.191806)))
    assert v[0] == 0.0                                           # the three positions are in the plane x = 0


def test_vallado_example_7_4_herrick_gibbs():
    v = iod.herrick_gibbs(*HG, *HG_T)
    assert abs(v[0] + 6.441557) < 5e-7 and abs(v[1] - 3.777559) < 1e-6
    sep = iod.separation_deg(*HG)
    assert sep == pytest.approx((4.5, 4.5), abs=1e-4)            # the example states positions about 4.5 degrees apart
    # third component: not asserted against a number (see the module docstring). Independent property instead: r1 and r3
    # must lie on the conic defined by (r2, v2), i.e. |r| + e.r = h^2 / mu, within a few metres (the method is a series)
    r2 = HG[1]
    h = (r2[1] * v[2] - r2[2] * v[1], r2[2] * v[0] - r2[0] * v[2], r2[0] * v[1] - r2[1] * v[0])
    p = sum(c * c for c in h) / MU
    vxh = (v[1] * h[2] - v[2] * h[1], v[2] * h[0] - v[0] * h[2], v[0] * h[1] - v[1] * h[0])
    ecc = [vxh[i] / MU - r2[i] / math.hypot(*r2) for i in range(3)]
    for r in (HG[0], HG[2]):
        assert abs(math.hypot(*r) + sum(a * b for a, b in zip(ecc, r)) - p) < 0.005
    assert -1.7210 < v[2] < -1.7200


@pytest.mark.parametrize("a, e, inc, nus", [(7000.0, 0.0, 0.0, (10, 40, 70)), (7000.0, 0.0, 63.4, (350, 20, 50)), (26554.0, 0.72, 63.4, (100, 140, 170)),
                                            (8000.0, 0.1, 28.5, (0, 30, 60)), (42164.0, 0.0, 0.05, (5, 10, 15)), (10000.0, 0.3, 97.0, (200, 240, 300)),
                                            (7000.0, 0.01, 51.6, (359, 0, 1)), (7000.0, 0.01, 51.6, (10, 170, 300))])
def test_gibbs_returns_the_true_velocity_of_a_known_orbit(a, e, inc, nus):
    states = [conic(a, e, nu, inc) for nu in nus]
    v = iod.gibbs(*[s[0] for s in states])
    assert rel(v, states[1][1]) < 1e-9


def test_gibbs_is_accurate_on_closely_spaced_positions():
    # found by the cross-check: the textbook sums lose 1.5e-5 at 0.02 degrees; the difference form keeps 1e-7
    for step in (0.02, 0.005):
        states = [conic(7000.0, 0.01, nu, 51.6) for nu in (50 - step, 50, 50 + step)]
        assert rel(iod.gibbs(*[s[0] for s in states]), states[1][1]) < 2e-7


def test_gibbs_does_not_depend_on_the_unit_and_scales_with_mu():
    v = iod.gibbs(*G)
    metres = iod.gibbs(*[[c * 1000 for c in r] for r in G], mu=MU * 1e9)
    assert all(abs(a * 1000 - b) < 1e-6 for a, b in zip(v, metres))
    assert all(abs(2 * a - b) < 1e-12 for a, b in zip(v, iod.gibbs(*G, mu=4 * MU)))
    assert iod.gibbs(*G, MU) == v and iod.gibbs(*G, MU, 3.0) == v and iod.MU_EARTH == MU


def _circular(t, a=7000.0, inc=40.0):
    n = math.sqrt(MU / a ** 3)
    return conic(a, 0.0, math.degrees(n * t), inc)


@pytest.mark.parametrize("dt", [1.0, 10.0, 30.0, 60.0])
def test_herrick_gibbs_on_a_circular_orbit_with_known_times(dt):
    s = [_circular(t) for t in (100.0 - dt, 100.0, 100.0 + dt)]
    v = iod.herrick_gibbs(s[0][0], s[1][0], s[2][0], 100.0 - dt, 100.0, 100.0 + dt)
    n = math.sqrt(MU / 7000.0 ** 3)
    assert rel(v, s[1][1]) < 0.02 * (n * dt) ** 4 + 1e-11          # truncation error grows as the fourth power of the angle


def test_herrick_gibbs_with_unequal_intervals_and_time_origin():
    s = [_circular(t) for t in (0.0, 20.0, 65.0)]
    v = iod.herrick_gibbs(s[0][0], s[1][0], s[2][0], 0.0, 20.0, 65.0)
    assert rel(v, s[1][1]) < 1e-6
    shifted = iod.herrick_gibbs(s[0][0], s[1][0], s[2][0], 1e6, 1e6 + 20.0, 1e6 + 65.0)
    assert rel(shifted, v) < 1e-9                                  # only time differences matter


def test_the_two_methods_have_opposite_domains():
    close = [conic(7000.0, 0.02, nu, 30.0) for nu in (20.0, 20.01, 20.02)]
    wide = [conic(7000.0, 0.02, nu, 30.0) for nu in (20.0, 50.0, 80.0)]

    def times(states):
        out = []
        for (r, _) in states:
            nu = math.atan2(math.hypot(r[1], r[2]) * (1 if r[1] >= 0 else -1), r[0])
            ecc = 2 * math.atan(math.sqrt((1 - 0.02) / (1 + 0.02)) * math.tan(nu / 2))
            out.append((ecc - 0.02 * math.sin(ecc)) / math.sqrt(MU / 7000.0 ** 3))
        return out

    hg_close = iod.herrick_gibbs(*[s[0] for s in close], *times(close))
    hg_wide = iod.herrick_gibbs(*[s[0] for s in wide], *times(wide))
    assert rel(hg_close, close[1][1]) < 1e-9 and rel(hg_wide, wide[1][1]) > 1e-3
    assert rel(iod.gibbs(*[s[0] for s in wide]), wide[1][1]) < 1e-12
    assert iod.separation_deg(*[s[0] for s in wide]) == pytest.approx((30.0, 30.0), abs=1e-9)
