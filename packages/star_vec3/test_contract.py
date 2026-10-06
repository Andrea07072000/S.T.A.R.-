"""Contract/refusals for every public star_vec3 function and argument.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_vec3 as sv

HOSTILE_VEC_CONTAINERS = ["abc", {1, 2, 3}, {"x": 1}, (x for x in [1, 2, 3]), None, 7]
HOSTILE_COMPONENTS = [True, "1", None, float("nan"), float("inf"), float("-inf"), 1 + 2j, 1.0000001e100]
BAD_LENGTHS = [(1, 2), (1, 2, 3, 4)]


def test_pinned_constants_and_exports():
    assert sv.__version__ == "0.1.0"
    assert sv.__all__ == ["dot", "cross", "norm", "distance", "triple", "unit", "angle_deg", "project", "reject"]
    assert sv.BIG == 1e100


@pytest.mark.parametrize("v", HOSTILE_VEC_CONTAINERS + BAD_LENGTHS)
def test_all_vector_taking_functions_refuse_bad_shapes(v):
    funcs = [
        (sv.dot, (v, (1, 0, 0))),
        (sv.cross, (v, (1, 0, 0))),
        (sv.norm, (v,)),
        (sv.distance, (v, (1, 0, 0))),
        (sv.triple, (v, (1, 0, 0), (0, 1, 0))),
        (sv.unit, (v,)),
        (sv.angle_deg, (v, (1, 0, 0))),
        (sv.project, (v, (1, 0, 0))),
        (sv.reject, (v, (1, 0, 0))),
    ]
    for f, args in funcs:
        with pytest.raises(ValueError):
            f(*args)


@pytest.mark.parametrize("bad", HOSTILE_COMPONENTS)
def test_component_hostiles_refused_in_every_position(bad):
    good = (1.0, 2.0, 3.0)
    for idx in range(3):
        v = list(good)
        v[idx] = bad
        v = tuple(v)
        with pytest.raises(ValueError):
            sv.norm(v)
        with pytest.raises(ValueError):
            sv.dot(v, good)
        with pytest.raises(ValueError):
            sv.dot(good, v)
        with pytest.raises(ValueError):
            sv.triple(good, v, good)


def test_limits_inside_and_outside():
    assert sv.norm((1e100, 0, 0)) == 1e100
    with pytest.raises(ValueError):
        sv.norm((1.0000001e100, 0, 0))
    assert sv.norm((-1e100, 0, 0)) == 1e100
    with pytest.raises(ValueError):
        sv.norm((-1.0000001e100, 0, 0))


def test_zero_direction_refusals_and_special_acceptance():
    z = (0, 0, 0)
    with pytest.raises(ValueError, match="zero vector"):
        sv.unit(z)
    with pytest.raises(ValueError, match="zero vector"):
        sv.angle_deg(z, (1, 0, 0))
    with pytest.raises(ValueError, match="zero vector"):
        sv.angle_deg((1, 0, 0), z)
    with pytest.raises(ValueError, match="zero vector"):
        sv.project((1, 2, 3), z)
    with pytest.raises(ValueError, match="zero vector"):
        sv.reject((1, 2, 3), z)
    assert sv.project(z, (1, 2, 3)) == (0.0, 0.0, 0.0)
    assert sv.reject(z, (1, 2, 3)) == (0.0, 0.0, 0.0)


def test_public_returns_are_floats_or_tuples_of_three_floats():
    assert isinstance(sv.dot((1, 0, 0), (0, 1, 0)), float)
    assert isinstance(sv.norm((1, 0, 0)), float)
    assert isinstance(sv.distance((1, 0, 0), (0, 1, 0)), float)
    assert isinstance(sv.triple((1, 0, 0), (0, 1, 0), (0, 0, 1)), float)
    for out in (sv.cross((1, 0, 0), (0, 1, 0)), sv.unit((0, 0, -7)), sv.project((1, 2, 3), (1, 0, 0)), sv.reject((1, 2, 3), (1, 0, 0))):
        assert isinstance(out, tuple) and len(out) == 3 and all(isinstance(x, float) and math.isfinite(x) for x in out)
