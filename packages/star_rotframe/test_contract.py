"""Contract tests for star_rotframe: hostile inputs, range boundaries, and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math
import pytest

import star_rotframe as sr

BAD_NUM = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1 + 2j]
BAD_VEC = [(1, 2), (1, 2, 3, 4), "abc", None]


def test_pinned_constants():
    assert sr.__version__ == "0.1.0"
    assert sr.__all__ == ["to_rotating", "to_inertial", "EARTH_RATE"]
    assert sr.EARTH_RATE == 7.292115e-5
    assert sr.BIG == 1e15
    assert sr.MAX_ANGLE == 1e9
    assert sr.MAX_RATE == 1000.0


@pytest.mark.parametrize("f", [sr.to_rotating, sr.to_inertial], ids=lambda f: f.__name__)
def test_r_and_v_container_contract(f):
    for bad in BAD_VEC:
        with pytest.raises(ValueError, match="must be a list or tuple of 3 numbers"):
            f(bad, (1, 2, 3), 0.0, 0.0)
        with pytest.raises(ValueError, match="must be a list or tuple of 3 numbers"):
            f((1, 2, 3), bad, 0.0, 0.0)


@pytest.mark.parametrize("f", [sr.to_rotating, sr.to_inertial], ids=lambda f: f.__name__)
def test_component_hostiles_for_r_and_v(f):
    base_r = [1.0, 2.0, 3.0]
    base_v = [4.0, 5.0, 6.0]
    bads = BAD_NUM + [1.0000001e15, -1.0000001e15]
    for bad in bads:
        for i in range(3):
            r = base_r[:]
            r[i] = bad
            with pytest.raises(ValueError, match="a component of r"):
                f(r, base_v, 0.0, 0.0)

            v = base_v[:]
            v[i] = bad
            with pytest.raises(ValueError, match="a component of v"):
                f(base_r, v, 0.0, 0.0)


@pytest.mark.parametrize("f", [sr.to_rotating, sr.to_inertial], ids=lambda f: f.__name__)
def test_angle_and_rate_hostiles_and_limits(f):
    for bad in BAD_NUM + [1.0000001e9, -1.0000001e9]:
        with pytest.raises(ValueError, match="angle"):
            f((1, 2, 3), (4, 5, 6), bad, 0.0)

    for bad in BAD_NUM + [1000.0000001, -1000.0000001]:
        with pytest.raises(ValueError, match="rate"):
            f((1, 2, 3), (4, 5, 6), 0.0, bad)

    # accepted boundaries and just-inside
    for a in (1e9, -1e9, 1e9 - 1e-9, -1e9 + 1e-9):
        out = f((1, 2, 3), (4, 5, 6), a, 0.0)
        assert all(type(x) is float for x in (*out[0], *out[1]))
    for w in (1000.0, -1000.0, 999.999999999, -999.999999999):
        out = f((1, 2, 3), (4, 5, 6), 0.0, w)
        assert all(type(x) is float and math.isfinite(x) for x in (*out[0], *out[1]))


@pytest.mark.parametrize("f", [sr.to_rotating, sr.to_inertial], ids=lambda f: f.__name__)
def test_big_component_boundaries(f):
    ok = f((1e15, -1e15, 0), (0, 0, 0), 0.0, 0.0)
    assert ok[0][0] == 1e15 and ok[0][1] == -1e15
    with pytest.raises(ValueError, match="a component of r"):
        f((1e15 + 1e8, 0, 0), (0, 0, 0), 0.0, 0.0)
