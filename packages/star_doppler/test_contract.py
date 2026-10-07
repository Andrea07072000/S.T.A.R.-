"""Contract tests for star_doppler: hostile values, range edges, pinned constants and error branches.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_doppler as sd

HOSTILE = [True, False, "x", None, float("nan"), float("inf"), float("-inf"), 1j]


def test_pinned_constants():
    assert sd.C_KM_S == 299792.458
    assert sd.BIG == 1e15
    assert sd.MAX_FREQUENCY == 1e30


@pytest.mark.parametrize("bad", [(1, 2), "abc", None])
@pytest.mark.parametrize("arg_index,name", [(0, "r_observer"), (1, "v_observer"), (2, "r_target"), (3, "v_target")])
def test_range_and_rate_refuses_non_3_vectors(bad, arg_index, name):
    args = [(0, 0, 0), (0, 0, 0), (1, 0, 0), (0, 0, 0)]
    args[arg_index] = bad
    with pytest.raises(ValueError, match=fr"{name} must be a list or tuple of 3 numbers"):
        sd.range_and_rate(*args)


@pytest.mark.parametrize("arg_index,name", [(0, "r_observer"), (1, "v_observer"), (2, "r_target"), (3, "v_target")])
@pytest.mark.parametrize("comp_index", [0, 1, 2])
@pytest.mark.parametrize("bad", HOSTILE + [1e15 + 1.0, -1e15 - 1.0])
def test_range_and_rate_refuses_bad_components(arg_index, name, comp_index, bad):
    args = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    args[arg_index][comp_index] = bad
    with pytest.raises(ValueError, match=fr"a component of {name}"):
        sd.range_and_rate(*args)


def test_range_and_rate_component_limits_and_coincidence():
    assert sd.range_and_rate((-1e15, 0, 0), (0, 0, 0), (1e15, 0, 0), (0, 0, 0))[0] == pytest.approx(2e15, abs=1e-6)
    with pytest.raises(ValueError, match="coincide"):
        sd.range_and_rate((1, 2, 3), (0, 0, 0), (1, 2, 3), (0, 0, 0))


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf"), float("-inf"), True, False, "1", None, 1.0000001e30])     # 1e30 + 1.0 is 1e30 itself in floating point
def test_received_frequency_refuses_bad_frequency(bad):
    with pytest.raises(ValueError, match="frequency"):
        sd.received_frequency(bad, 0.0)


def test_received_frequency_accepts_frequency_limit():
    assert math.isfinite(sd.received_frequency(1e30, 0.0))
    assert sd.received_frequency(1e30, 0.0) == 1e30


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, False, "1", None])
def test_received_frequency_refuses_bad_range_rate_type(bad):
    with pytest.raises(ValueError, match="range_rate"):
        sd.received_frequency(1.0, bad)


@pytest.mark.parametrize("rr", [sd.C_KM_S, -sd.C_KM_S, 3e5])
def test_received_frequency_refuses_speed_of_light_or_faster(rr):
    with pytest.raises(ValueError, match="smaller than the speed of light"):
        sd.received_frequency(1.0, rr)


def test_received_frequency_range_rate_just_inside_and_just_outside():
    assert math.isfinite(sd.received_frequency(1.0, 299792.457))
    with pytest.raises(ValueError, match="smaller than the speed of light"):
        sd.received_frequency(1.0, 299792.458)


@pytest.mark.parametrize("rel", [0, 1, None, "yes"])
def test_received_frequency_relativistic_must_be_bool(rel):
    with pytest.raises(ValueError, match="relativistic must be True or False"):
        sd.received_frequency(1.0, 0.0, rel)
