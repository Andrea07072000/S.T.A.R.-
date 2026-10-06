"""star_kepler against a published example, a closed-form truth, an independent numerical integrator and invariants.
Verifies: R1, R2, R3 (README).

References: Vallado, Fundamentals of Astrodynamics and Applications, Example 2-4 (Kepler's problem, 40 min), values
cross-checked with NAIF prop2b on 2026-10-06. The numerical lineage is a fixed-step RK4 integration of the two-body
equation written here: a different method (integration vs. solving Kepler's equation), used for hyperbolic orbits too."""
import math

import pytest

from star_kepler import MU_EARTH, propagate, stumpff

MU = MU_EARTH


def rk4(r, v, tof, mu, steps):
    def acc(p):
        d = math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) ** 3
        return [-mu * x / d for x in p]
    h = tof / steps
    r, v = list(r), list(v)
    for _ in range(steps):
        k1r, k1v = v, acc(r)
        k2r = [a + 0.5 * h * b for a, b in zip(v, k1v)]; k2v = acc([a + 0.5 * h * b for a, b in zip(r, k1r)])
        k3r = [a + 0.5 * h * b for a, b in zip(v, k2v)]; k3v = acc([a + 0.5 * h * b for a, b in zip(r, k2r)])
        k4r = [a + h * b for a, b in zip(v, k3v)]; k4v = acc([a + h * b for a, b in zip(r, k3r)])
        r = [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(r, k1r, k2r, k3r, k4r)]
        v = [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(v, k1v, k2v, k3v, k4v)]
    return r, v


def invariants(r, v, mu=MU):
    energy = 0.5 * sum(x * x for x in v) - mu / math.dist(r, (0, 0, 0))
    h = (r[1] * v[2] - r[2] * v[1], r[2] * v[0] - r[0] * v[2], r[0] * v[1] - r[1] * v[0])
    return energy, h


def test_vallado_example_2_4():
    r, v = propagate((1131.340, -2282.343, 6672.423), (-5.64305, 4.30333, 2.42879), 2400.0)
    assert math.dist(r, (-4219.7527, 4363.0292, -3958.7666)) < 1e-3       # printed to 4 decimals
    assert math.dist(v, (3.689866, -1.916735, -6.112511)) < 1e-5          # printed to 6 decimals


CASES = [  # (r0, v0, tof, steps): LEO circular equatorial, inclined elliptic, GTO-like, hyperbolic flyby
    ((7000.0, 0.0, 0.0), (0.0, math.sqrt(MU / 7000.0), 0.0), 3000.0, 6000),
    ((6800.0, 500.0, 1200.0), (-1.0, 7.2, 2.5), 5000.0, 10000),
    ((6600.0, 0.0, 0.0), (0.0, 10.2, 0.6), 7200.0, 30000),
    ((8000.0, 0.0, 2000.0), (2.0, 12.5, 1.0), 4000.0, 8000),
]


@pytest.mark.parametrize("r0,v0,tof,steps", CASES)
def test_against_independent_numerical_integration(r0, v0, tof, steps):
    r, v = propagate(r0, v0, tof)
    rn, vn = rk4(r0, v0, tof, MU, steps)
    assert math.dist(r, rn) < 1e-5 * math.dist(rn, (0, 0, 0))
    assert math.dist(v, vn) < 1e-5 * math.dist(vn, (0, 0, 0))


@pytest.mark.parametrize("r0,v0,tof,steps", CASES)
def test_energy_and_angular_momentum_are_conserved(r0, v0, tof, steps):
    e0, h0 = invariants(r0, v0)
    e1, h1 = invariants(*propagate(r0, v0, tof))
    assert abs(e1 - e0) < 1e-9 * max(1.0, abs(e0)) and math.dist(h0, h1) < 1e-9 * math.dist(h0, (0, 0, 0))


def test_hyperbolic_case_is_really_hyperbolic_and_handled():
    r0, v0 = CASES[3][0], CASES[3][1]
    assert invariants(r0, v0)[0] > 0
    r, v = propagate(r0, v0, 86400.0)
    assert math.dist(r, (0, 0, 0)) > 5e5 and invariants(r, v)[0] > 0


@pytest.mark.parametrize("r0,v0,tof,steps", CASES)
def test_forward_then_backward_returns_to_the_start(r0, v0, tof, steps):
    r, v = propagate(r0, v0, tof)
    rb, vb = propagate(r, v, -tof)
    assert math.dist(rb, r0) < 1e-7 and math.dist(vb, v0) < 1e-10


def test_whole_periods_return_the_same_state_even_after_a_thousand_revolutions():
    r0, v0 = CASES[1][0], CASES[1][1]
    a = 1.0 / (2.0 / math.dist(r0, (0, 0, 0)) - sum(x * x for x in v0) / MU)
    period = 2 * math.pi * math.sqrt(a ** 3 / MU)
    r, v = propagate(r0, v0, 1000 * period)
    assert math.dist(r, r0) < 1e-4 and math.dist(v, v0) < 1e-7
    assert propagate(r0, v0, 0.0) == (r0, v0)


def test_circular_equatorial_orbit_has_no_singularity():
    r, v = propagate((7000.0, 0.0, 0.0), (0.0, math.sqrt(MU / 7000.0), 0.0), 0.25 * 2 * math.pi * math.sqrt(7000.0 ** 3 / MU))
    assert math.dist(r, (0.0, 7000.0, 0.0)) < 1e-8 and abs(v[0] + math.sqrt(MU / 7000.0)) < 1e-11


def test_stumpff_series_matches_the_closed_forms_at_the_switch_and_at_zero():
    assert stumpff(0.0) == (0.5, 1.0 / 6.0)
    for z in (1e-6 * 1.0001, -1e-6 * 1.0001, 0.5, -0.5, 9.0):
        s = math.sqrt(abs(z))
        c = (1 - math.cos(s)) / z if z > 0 else (math.cosh(s) - 1) / -z
        assert abs(stumpff(z)[0] - c) < 1e-9
    assert abs(stumpff(1e-7)[0] - stumpff(1.5e-6)[0]) < 1e-6 and abs(stumpff(1e-7)[1] - stumpff(1.5e-6)[1]) < 1e-6


@pytest.mark.parametrize("z", [5e-7, -5e-7, 9e-7, -9e-7, 1e-9])
def test_stumpff_series_coefficients(z):
    c, s = stumpff(z)                      # longer independent Taylor series: 1/2 - z/24 + z^2/720 - z^3/40320 ...
    assert abs(c - (0.5 - z / 24 + z * z / 720 - z ** 3 / 40320)) < 1e-15
    assert abs(s - (1 / 6 - z / 120 + z * z / 5040 - z ** 3 / 362880)) < 1e-15
    assert abs(c - 0.5) > 1e-12 or abs(z) < 1e-8      # the linear term is really there


def test_period_removal_uses_the_true_period():
    r0, v0 = (6800.0, 500.0, 1200.0), (-1.0, 7.2, 2.5)
    a = 1.0 / (2.0 / math.dist(r0, (0, 0, 0)) - sum(x * x for x in v0) / MU)
    period = 2 * math.pi * math.sqrt(a ** 3 / MU)
    one = propagate(r0, v0, 1234.5)
    again = propagate(r0, v0, 1234.5 + 7 * period)
    assert math.dist(one[0], again[0]) < 1e-6 and math.dist(one[1], again[1]) < 1e-9
    half = propagate(r0, v0, 0.5 * period)
    assert math.dist(half[0], r0) > 1000.0            # half a period is NOT the starting point
