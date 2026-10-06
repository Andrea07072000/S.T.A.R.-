"""star_interp against published and hand-derivable interpolation facts.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (one finite-difference bound tighter than FACTS.md allowed)."""
import math
import random

import pytest

import star_interp as si


def test_published_meeus_example_3a():
    x = 8.0 + 4.35 / 24.0  # n = 0.18125
    y = si.lagrange([7, 8, 9], [0.884226, 0.877366, 0.870531], x)
    assert abs(y - 0.876125) <= 5e-7


def test_quadratic_and_cubic_reproduction_and_node_derivatives():
    # y=x^2 at nodes 0,1,2: exact polynomial reproduction
    xs2, ys2 = [0.0, 1.0, 2.0], [0.0, 1.0, 4.0]
    assert si.lagrange(xs2, ys2, 1.5) == pytest.approx(2.25, abs=1e-13)
    assert si.lagrange_derivative(xs2, ys2, 1.5) == pytest.approx(3.0, abs=1e-13)
    assert si.lagrange_derivative(xs2, ys2, 1.0) == pytest.approx(2.0, abs=1e-13)
    assert si.lagrange_derivative(xs2, ys2, 0.0) == pytest.approx(0.0, abs=1e-13)
    assert si.lagrange_derivative(xs2, ys2, 2.0) == pytest.approx(4.0, abs=1e-13)

    # y=x^3+x+1 at nodes 0,1,2,3 => values 1,3,11,31
    xs3, ys3 = [0.0, 1.0, 2.0, 3.0], [1.0, 3.0, 11.0, 31.0]
    assert si.lagrange(xs3, ys3, 1.5) == pytest.approx(5.875, abs=1e-13)
    assert si.lagrange_derivative(xs3, ys3, 1.5) == pytest.approx(7.75, abs=1e-13)
    assert si.lagrange_derivative(xs3, ys3, 2.0) == pytest.approx(13.0, abs=1e-13)


def test_line_constant_node_exactness_weights_and_invariants():
    assert si.lagrange([0, 1], [3, 5], 0.25) == pytest.approx(3.5, abs=1e-14)
    for x in (0.0, 0.25, 0.9, 1.0):
        assert si.lagrange_derivative([0, 1], [3, 5], x) == pytest.approx(2.0, abs=1e-14)

    assert si.lagrange([0, 10], [5, 5], 3) == pytest.approx(5.0, abs=1e-14)
    assert si.lagrange_derivative([0, 10], [5, 5], 3) == pytest.approx(0.0, abs=1e-14)

    xs, ys = [2.0, -1.0, 4.0], [7.0, 9.0, -3.0]
    assert si.lagrange(xs, ys, -1.0) == 9.0
    assert si.lagrange(xs, ys, 2.0) == 7.0
    assert si.lagrange(xs, ys, 4.0) == -3.0

    assert si.lagrange_weights([0, 1, 2]) == pytest.approx([0.5, -1.0, 0.5], abs=1e-15)
    assert si.lagrange_weights([0, 1, 2, 3]) == pytest.approx([-1 / 6, 1 / 2, -1 / 2, 1 / 6], abs=1e-15)
    assert si.lagrange_weights([1, 3]) == pytest.approx([-0.5, 0.5], abs=1e-15)

    x = 1.37
    xs1, ys1 = [0.0, 1.0, 2.0, 3.0], [1.0, 2.0, 5.0, 10.0]
    perm = [2, 0, 3, 1]
    xs2, ys2 = [xs1[i] for i in perm], [ys1[i] for i in perm]
    assert si.lagrange(xs2, ys2, x) == pytest.approx(si.lagrange(xs1, ys1, x), rel=1e-13)

    a, b = 2.5, -0.75
    y1, y2 = [0.0, 1.0, 4.0], [1.0, 0.0, 1.0]
    y = [a * u + b * v for u, v in zip(y1, y2)]
    assert si.lagrange([0, 1, 2], y, 1.2) == pytest.approx(
        a * si.lagrange([0, 1, 2], y1, 1.2) + b * si.lagrange([0, 1, 2], y2, 1.2), rel=1e-12
    )

    xs = [0.0, 1.0, 2.0]
    ys = [1.0, 3.0, 7.0]
    x0 = 1.4
    s, k = 10.0, 3.0
    assert si.lagrange([u + s for u in xs], ys, x0 + s) == pytest.approx(si.lagrange(xs, ys, x0), abs=1e-14)
    assert si.lagrange([k * u for u in xs], ys, k * x0) == pytest.approx(si.lagrange(xs, ys, x0), abs=1e-14)
    assert si.lagrange_derivative([k * u for u in xs], ys, k * x0) == pytest.approx(
        si.lagrange_derivative(xs, ys, x0) / k, rel=1e-13
    )


def test_derivative_matches_finite_difference_and_continuity_and_sin_table():
    xs = [0.0, 0.7, 1.1, 2.0, 2.6]
    ys = [math.sin(t) + 0.1 * t for t in xs]
    span = max(xs) - min(xs)
    h = 1e-5 * span
    x = 1.3
    d = si.lagrange_derivative(xs, ys, x)
    d_fd = (si.lagrange(xs, ys, x + h) - si.lagrange(xs, ys, x - h)) / (2 * h)
    assert d == pytest.approx(d_fd, rel=1e-6)

    node = 1.1
    e = 1e-9
    dl = si.lagrange_derivative(xs, ys, node - e)
    dr = si.lagrange_derivative(xs, ys, node + e)
    dn = si.lagrange_derivative(xs, ys, node)
    assert dl == pytest.approx(dn, rel=1e-6, abs=1e-10)       # beside the node the derivative differs from the one at the node by the offset times the curvature: 2e-7 here
    assert dr == pytest.approx(dn, rel=1e-6, abs=1e-10)

    xs = [0.1 * i for i in range(11)]
    ys = [math.sin(t) for t in xs]
    rnd = random.Random(7)
    for _ in range(20):
        x = rnd.uniform(0.2, 0.8)
        assert si.lagrange(xs, ys, x) == pytest.approx(math.sin(x), abs=1e-12)
        assert si.lagrange_derivative(xs, ys, x) == pytest.approx(math.cos(x), abs=1e-10)
