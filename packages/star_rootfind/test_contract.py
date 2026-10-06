"""Contract/refusals for star_rootfind: hostile values, boundary limits, and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""

import pytest

import star_rootfind as sr

HOSTILE = [True, False, "3", None, float("nan"), float("inf"), float("-inf"), 1j, 1.1e300, -1.1e300]


def test_pinned_constants_and_exports():
    assert sr.BIG == 1e300
    assert sr.MAX_PIECES == 100000
    assert sr.__all__ == ["find_root", "find_roots"]


@pytest.mark.parametrize("bad_f", [3, None, "sin"])
def test_f_must_be_callable(bad_f):
    with pytest.raises(ValueError, match="callable"):
        sr.find_root(bad_f, 0, 1)
    with pytest.raises(ValueError, match="callable"):
        sr.find_roots(bad_f, 0, 1, 1)


@pytest.mark.parametrize("bad", HOSTILE)
def test_a_and_b_refuse_hostile_values(bad):
    with pytest.raises(ValueError):
        sr.find_root(lambda x: x, bad, 1.0)
    with pytest.raises(ValueError):
        sr.find_root(lambda x: x, -1.0, bad)
    with pytest.raises(ValueError):
        sr.find_roots(lambda x: x, bad, 1.0, 1)
    with pytest.raises(ValueError):
        sr.find_roots(lambda x: x, -1.0, bad, 1)


def test_a_b_order_refusals_and_boundaries():
    with pytest.raises(ValueError, match="smaller"):
        sr.find_root(lambda x: x, 2, 1)
    with pytest.raises(ValueError, match="smaller"):
        sr.find_root(lambda x: x, 1, 1)
    with pytest.raises(ValueError, match="smaller"):
        sr.find_roots(lambda x: x, 2, 1, 2)
    with pytest.raises(ValueError, match="smaller"):
        sr.find_roots(lambda x: x, 1, 1, 2)

    assert sr.find_root(lambda x: x, -1e300, 1e300) == 0.0


def test_no_sign_change_refusal():
    with pytest.raises(ValueError, match="same sign"):
        sr.find_root(abs, 1, 2)
    with pytest.raises(ValueError, match="same sign"):
        sr.find_root(lambda x: -1.0, 0, 1)


@pytest.mark.parametrize(
    "f",
    [
        lambda x: "bad" if x == 0 else x,
        lambda x: None if x == 0 else x,
        lambda x: True if x == 0 else x,
        lambda x: 1j if x == 0 else x,
        lambda x: float("nan") if x == 0 else x,
        lambda x: float("inf") if x == 0 else x,
    ],
)
def test_f_must_return_finite_real_at_end_or_middle(f):
    with pytest.raises(ValueError, match="finite real"):
        sr.find_root(f, 0, 1)


def test_pole_or_runtime_error_propagation():
    with pytest.raises((ValueError, ZeroDivisionError)):
        sr.find_root(lambda x: 1 / x, -1, 1.5)
    with pytest.raises(ZeroDivisionError):
        sr.find_root(lambda x: 1 / 0, 0, 1)


@pytest.mark.parametrize("pieces", [0, 100001, -1, 2.0, "3", None, True])
def test_pieces_refusals(pieces):
    with pytest.raises(ValueError, match="pieces must be an integer from 1 to 100000"):
        sr.find_roots(lambda x: x, -1, 1, pieces)


def test_pieces_limits_accepted():
    r1 = sr.find_roots(lambda x: x, -1, 1, 1)
    assert len(r1) == 1 and abs(r1[0]) <= 1e-15

    r2 = sr.find_roots(lambda x: x, -1, 1, 100000)
    assert len(r2) == 1 and abs(r2[0]) <= 1e-15
