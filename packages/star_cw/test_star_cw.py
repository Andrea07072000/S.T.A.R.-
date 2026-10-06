"""star_cw: properties of the Clohessy-Wiltshire solution that can be checked by hand, and an independent integration.
Verifies: R1, R2, R3 (README).

Reference: W. H. Clohessy and R. S. Wiltshire, "Terminal Guidance System for Satellite Rendezvous" (1960): the
equations x'' - 2 n y' - 3 n^2 x = 0, y'' + 2 n x' = 0, z'' + n^2 z = 0 and their textbook consequences (a deputy
at rest on the along-track axis stays there; a radial offset drifts 12 pi x0 per revolution; the closed 2-by-1 ellipse).
Independent method here: the three equations are integrated with a fixed-step RK4, without the closed form.
The comparison with SciPy's matrix exponential and with full two-body motion (NAIF prop2b) is in crosscheck_cw.py."""
import math
import random

import pytest

import star_cw as cw

N = 0.0011                       # rad/s, a low Earth orbit
T = 2 * math.pi / N


def close(p, q, tol):
    return len(p) == len(q) and all(abs(a - b) <= tol for a, b in zip(p, q))


def test_a_state_has_six_components_and_time_zero_changes_nothing():
    s = (1.0, -2.0, 3.0, 0.01, -0.02, 0.03)
    out = cw.propagate(s, N, 0.0)
    assert len(out) == 6 and out == s                         # 2026-10-06: the first version returned an EMPTY tuple
    m = cw.stm(N, 0.0)
    assert len(m) == 6 and all(len(r) == 6 for r in m)
    assert all(m[i][j] == (1.0 if i == j else 0.0) for i in range(6) for j in range(6))


def test_textbook_trajectories():
    assert close(cw.propagate((0, 100, 0, 0, 0, 0), N, 0.37 * T), (0, 100, 0, 0, 0, 0), 1e-12)          # along-track hold point
    out = cw.propagate((10, 0, 0, 0, 0, 0), N, T)                                                     # radial offset, at rest
    assert close(out, (10, -12 * math.pi * 10, 0, 0, 0, 0), 1e-9)                                     # drifts 12 pi x0 per revolution
    ellipse = (10, 0, 0, 0, -2 * N * 10, 0)                                                           # closed 2-by-1 ellipse
    assert close(cw.propagate(ellipse, N, T / 4), (0, -20, 0, -N * 10, 0, 0), 1e-9)
    assert close(cw.propagate(ellipse, N, T / 2), (-10, 0, 0, 0, 2 * N * 10, 0), 1e-9)
    assert close(cw.propagate(ellipse, N, T), ellipse, 1e-9) and close(cw.propagate(ellipse, N, 7 * T), ellipse, 1e-7)
    out = cw.propagate((0, 0, 5, 0, 0, 0), N, T / 4)                                                  # cross-track: harmonic oscillator
    assert close(out, (0, 0, 0, 0, 0, -N * 5), 1e-12) and close(cw.propagate((0, 0, 5, 0, 0, 0), N, T / 2), (0, 0, -5, 0, 0, 0), 1e-12)
    out = cw.propagate((0, 0, 0, 0, 0.1, 0), N, T)                                                    # along-track kick: 6 pi v / n behind
    assert close(out[:3], (0, -6 * math.pi * 0.1 / N, 0), 1e-9) and close(out[3:], (0, 0.1, 0), 1e-12)


def test_transition_matrix_composes_and_inverts():
    rnd = random.Random(4)
    for _ in range(50):
        n, t1, t2 = 10 ** rnd.uniform(-4.3, -2.9), rnd.uniform(0, 5000), rnd.uniform(0, 5000)
        s = [rnd.uniform(-10, 10) for _ in range(3)] + [rnd.uniform(-0.01, 0.01) for _ in range(3)]
        direct, chained = cw.propagate(s, n, t1 + t2), cw.propagate(cw.propagate(s, n, t1), n, t2)
        scale = max(map(abs, direct[:3])) + 1.0
        assert close(direct[:3], chained[:3], 1e-11 * scale) and close(direct[3:], chained[3:], 1e-11 * scale * n)
        back = cw.propagate(cw.propagate(s, n, t1), n, -t1)
        assert close(back[:3], s[:3], 1e-10 * scale) and close(back[3:], s[3:], 1e-10 * scale * n)
        m = cw.stm(n, t1)
        assert close(cw.propagate(s, n, t1), [sum(m[i][j] * s[j] for j in range(6)) for i in range(6)], 0.0)


def _rk4(s, n, t, steps=4000):
    def f(y):
        return [y[3], y[4], y[5], 3 * n * n * y[0] + 2 * n * y[4], -2 * n * y[3], -n * n * y[2]]
    h = t / steps
    y = list(s)
    for _ in range(steps):
        k1 = f(y)
        k2 = f([a + 0.5 * h * b for a, b in zip(y, k1)])
        k3 = f([a + 0.5 * h * b for a, b in zip(y, k2)])
        k4 = f([a + h * b for a, b in zip(y, k3)])
        y = [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(y, k1, k2, k3, k4)]
    return y


@pytest.mark.parametrize("seed", range(6))
def test_closed_form_agrees_with_a_numerical_integration_of_the_equations(seed):
    rnd = random.Random(seed)
    s = [rnd.uniform(-50, 50) for _ in range(3)] + [rnd.uniform(-0.05, 0.05) for _ in range(3)]
    t = rnd.uniform(0.1, 1.5) * T
    exact, numeric = cw.propagate(s, N, t), _rk4(s, N, t)
    assert close(exact[:3], numeric[:3], 1e-7) and close(exact[3:], numeric[3:], 1e-10)


def test_small_angles_keep_precision():
    # 1 - cos(nt) computed as 2 sin^2(nt/2): a 1 ms drift after a radial kick must not lose the along-track term
    out = cw.propagate((0, 0, 0, 1.0, 0, 0), N, 1e-3)
    assert out[1] == pytest.approx(-N * 1e-6, rel=1e-9) and out[0] == pytest.approx(1e-3, rel=1e-9)


@pytest.mark.parametrize("frac", [0.1, 0.25, 0.4, 0.6, 0.75, 0.9, 1.3, 2.25])
def test_rendezvous_reaches_the_target_and_stops_there(frac):
    rnd = random.Random(int(frac * 100))
    r0 = [rnd.uniform(-2000, 2000) for _ in range(3)]
    v0 = [rnd.uniform(-1, 1) for _ in range(3)]
    rf = [rnd.uniform(-50, 50) for _ in range(3)]
    t = frac * T
    dv1, dv2 = cw.rendezvous(r0, v0, rf, N, t)
    assert len(dv1) == 3 and len(dv2) == 3
    arrive = cw.propagate(list(r0) + [a + b for a, b in zip(v0, dv1)], N, t)
    assert close(arrive[:3], rf, 1e-6) and close([a + b for a, b in zip(arrive[3:], dv2)], (0, 0, 0), 1e-9)


def test_rendezvous_with_the_chief_from_a_hold_point():
    # from 1 km behind, at rest, to the chief in a quarter revolution: the textbook V-bar approach
    dv1, dv2 = cw.rendezvous((0, -1000, 0), (0, 0, 0), (0, 0, 0), N, T / 4)
    th = math.pi / 2
    det = 8 * (1 - math.cos(th)) - 3 * th * math.sin(th)
    assert dv1[0] == pytest.approx(-N * 2 * (1 - math.cos(th)) * 1000 / det, rel=1e-12)          # from the inverse of the 2x2 block by hand
    assert dv1[1] == pytest.approx(N * math.sin(th) * 1000 / det, rel=1e-12) and dv1[2] == 0.0
    assert cw.rendezvous((0, 0, 0), (0, 0, 0), (0, 0, 0), N, 500.0) == ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
