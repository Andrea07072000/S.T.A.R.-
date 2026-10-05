"""Kepler solver on the hard cases found by the Kepler-equation audit (2026-10-05).
Verifies: R4 (README).

The bracketed Newton must (a) solve every case of the audit grid up to e = 0.9999, (b) within 27 iterations (measured
worst case of this implementation, pinned: a slower variant is a regression), (c) to 1e-11 rad of the anomaly the
forward map started from (measured 6.6e-12), and (d) solve the case plain Newton refused (e = 0.99, M = 6.2776)."""
import math

import pytest

from star_elements import mean_to_eccentric

ECCS = [0.0, 1e-6, 0.1, 0.5, 0.9, 0.99, 0.999, 0.9999]
GRID = [0.0, 1e-8, 1e-4, math.pi, 2 * math.pi - 1e-4] + [2 * math.pi * (k + 0.5) / 36 for k in range(36)]


def circ(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


@pytest.mark.parametrize("e", ECCS)
def test_whole_grid_within_iteration_budget_and_accuracy(e):
    for E in GRID:
        M = E - e * math.sin(E)
        got = mean_to_eccentric(M, e, max_iter=27)
        assert circ(got, E) <= 1e-11, (e, E, got)
        assert 0.0 <= got < 2 * math.pi


def test_case_that_plain_newton_refused():
    M, e = 6.277616774031933, 0.99
    E = mean_to_eccentric(M, e)
    assert abs(E - e * math.sin(E) - M) < 1e-14
    assert abs(E - 6.021385919380443) < 1e-12


def test_budget_too_small_is_refused_not_answered():
    with pytest.raises(RuntimeError):
        mean_to_eccentric(0.228247, 0.9999, max_iter=2)
