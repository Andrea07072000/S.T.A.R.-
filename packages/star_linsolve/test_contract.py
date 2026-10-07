"""Contract tests for star_linsolve: refusals, limits, constants, and overflow guards.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_linsolve as sl

HOSTILE = [True, False, "3", None, 1j, float("nan"), float("inf"), float("-inf"), 1.0000001e100, -1.0000001e100]


def test_pinned_constants_and_exports():
    assert sl.MAX_SIZE == 20
    assert sl.BIG == 1e100
    assert sl.__all__ == ["det", "solve", "inverse"]


@pytest.mark.parametrize("a", ["x", None, 7, {1, 2}, []])
def test_a_not_matrix_refused(a):
    for f in (sl.det, sl.inverse):
        with pytest.raises(ValueError):
            f(a)
    with pytest.raises(ValueError):
        sl.solve(a, [1])


def test_a_size_and_shape_limits():
    a21 = tuple(tuple(1.0 if i == j else 0.0 for j in range(21)) for i in range(21))
    with pytest.raises(ValueError, match="1 to 20 rows"):
        sl.det(a21)

    with pytest.raises(ValueError, match="must be square"):
        sl.det([[1, 2], [3]])
    with pytest.raises(ValueError, match="must be square"):
        sl.det([1, 2])


def test_a_entries_hostile_and_limits():
    for bad in HOSTILE:
        with pytest.raises(ValueError):
            sl.det([[bad]])
    assert sl.det([[1e100]]) == 1e100
    assert sl.det([[-1e100]]) == -1e100


def test_b_contract_all_positions_and_message():
    a = [[2.0, 0.0], [0.0, 3.0]]
    with pytest.raises(ValueError, match="b must be a list or tuple of 2 numbers"):
        sl.solve(a, 3)
    with pytest.raises(ValueError, match="b must be a list or tuple of 2 numbers"):
        sl.solve(a, [1.0])
    with pytest.raises(ValueError, match="b must be a list or tuple of 2 numbers"):
        sl.solve(a, [1.0, 2.0, 3.0])

    for bad in HOSTILE:
        with pytest.raises(ValueError, match="b must hold finite real numbers"):
            sl.solve(a, [bad, 1.0])
        with pytest.raises(ValueError, match="b must hold finite real numbers"):
            sl.solve(a, [1.0, bad])


def test_singular_and_overflow_refusals():
    with pytest.raises(ValueError, match="singular"):
        sl.solve([[1, 2], [2, 4]], [1, 2])
    with pytest.raises(ValueError, match="singular"):
        sl.inverse([[1, 2], [2, 4]])

    with pytest.raises(ValueError, match="too large"):
        sl.det([[1e100, 0, 0, 0], [0, 1e100, 0, 0], [0, 0, 1e100, 0], [0, 0, 0, 1e100]])
    with pytest.raises(ValueError, match="too large"):
        sl.solve([[1e-300]], [1e100])
    with pytest.raises(ValueError, match="too large"):
        sl.inverse([[5e-324]])
