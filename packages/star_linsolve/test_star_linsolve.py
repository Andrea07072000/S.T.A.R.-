"""star_linsolve against published values and hand-derivable linear algebra identities.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_linsolve as sl


def _matmul_vec(a, x):
    return tuple(sum(float(ai) * float(xj) for ai, xj in zip(row, x)) for row in a)


def test_hand_small_orders_and_types():
    assert sl.det([[3]]) == 3.0
    assert sl.solve([[5]], [10]) == (2.0,)
    assert sl.inverse([[4]]) == ((0.25,),)

    assert sl.det([[1, 2], [3, 4]]) == -2.0
    assert sl.inverse([[1, 2], [3, 4]]) == ((-2.0, 1.0), (1.5, -0.5))
    # 1/10 of ((6, -7), (-2, 4))
    assert sl.inverse([[4, 7], [2, 6]]) == ((0.6, -0.7), (-0.2, 0.4))
    # det=5, x=(9-5)/5=0.8, y=(10-3)/5=1.4
    assert sl.solve([[2, 1], [1, 3]], [3, 5]) == (0.8, 1.4)

    m3 = [[1, 2, 3], [4, 5, 6], [7, 8, 10]]
    assert sl.det(m3) == -3.0
    assert sl.solve(m3, [6, 15, 25]) == (1.0, 1.0, 1.0)
    assert sl.inverse(m3) == ((-2 / 3, -4 / 3, 1.0), (-2 / 3, 11 / 3, -2.0), (1.0, -2.0, 1.0))


def test_pivots_singular_near_singular_and_scale():
    assert sl.det([[0, 1], [1, 0]]) == -1.0
    assert sl.det([[0, 2], [3, 0]]) == -6.0
    assert sl.solve([[0, 2], [3, 0]], [4, 9]) == (3.0, 2.0)

    assert sl.det([[1, 2], [2, 4]]) == 0.0
    with pytest.raises(ValueError, match="singular"):
        sl.solve([[1, 2], [2, 4]], [1, 2])
    with pytest.raises(ValueError, match="singular"):
        sl.inverse([[1, 2], [2, 4]])

    e = 2 ** -52
    assert sl.det([[1, 1], [1, 1 + e]]) == e
    assert sl.solve([[1, 1], [1, 1 + e]], [2, 2]) == (2.0, 0.0)
    assert sl.solve([[1, 1], [1, 1 + e]], [2, 2 + 2 * e]) == (0.0, 2.0)
    assert sl.inverse([[1, 1], [1, 1 + e]]) == ((2 ** 52 + 1.0, -(2 ** 52)), (-(2 ** 52), 2 ** 52.0))

    assert sl.det([[1e100, 0], [0, 1e100]]) == 1e200
    assert sl.det([[1e-200, 0], [0, 1e-200]]) == 0.0
    inv = sl.inverse([[1e-200, 0], [0, 1e-200]])
    assert inv[0][0] == pytest.approx(1e200, rel=1e-15)
    assert inv[1][1] == pytest.approx(1e200, rel=1e-15)


def test_published_hilbert_values():
    h = ((1.0, 0.5, 1.0 / 3.0), (0.5, 1.0 / 3.0, 0.25), (1.0 / 3.0, 0.25, 0.2))
    assert sl.det(h) == pytest.approx(1.0 / 2160.0, rel=1e-13)
    invh = sl.inverse(h)
    target = ((9.0, -36.0, 30.0), (-36.0, 192.0, -180.0), (30.0, -180.0, 180.0))
    for r in range(3):
        for c in range(3):
            assert invh[r][c] == pytest.approx(target[r][c], rel=1e-12)

    a = ((60, 30, 20), (30, 20, 15), (20, 15, 12))
    assert sl.det(a) == 100.0
    assert sl.inverse(a) == ((0.15, -0.6, 0.5), (-0.6, 3.2, -3.0), (0.5, -3.0, 3.0))
    assert sl.solve(a, [110, 65, 47]) == (1.0, 1.0, 1.0)
