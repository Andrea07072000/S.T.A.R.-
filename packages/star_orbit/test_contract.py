"""Input contract of propagate_orbit, from a probe with hostile inputs (2026-10-05).
Verifies: R1, R2 (README).

Found by the probe: step_sec = 0 or < 0 looped forever (the call never returned), a negative duration silently
returned only the initial state, NaN/inf position or velocity returned a trajectory of NaN, and r = 0 raised
ZeroDivisionError. All now raise ValueError before any work. Each call runs in a daemon thread with a deadline, so a
regression to the infinite loop FAILS this test instead of hanging the suite."""
import math
import threading
from datetime import datetime, timezone

import pytest

from star_orbit import OrbitState, propagate_orbit

EP = datetime(2026, 1, 1, tzinfo=timezone.utc)
GOOD = OrbitState(EP, (7000e3, 0.0, 0.0), (0.0, 7546.0, 0.0))


def call_with_deadline(seconds=10.0, **kw):
    out = {}

    def run():
        try:
            out["value"] = propagate_orbit(**kw)
        except BaseException as e:  # noqa: BLE001 - recorded and re-raised in the test thread
            out["error"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), f"propagate_orbit did not return within {seconds} s: {kw}"
    if "error" in out:
        raise out["error"]
    return out["value"]


@pytest.mark.parametrize("kw", [
    dict(step_sec=0.0), dict(step_sec=-30.0), dict(step_sec=math.nan), dict(step_sec=math.inf),
    dict(duration_sec=-600.0), dict(duration_sec=math.nan), dict(duration_sec=math.inf),
    dict(initial_state=OrbitState(EP, (math.nan, 0.0, 0.0), (0.0, 7546.0, 0.0))),
    dict(initial_state=OrbitState(EP, (7000e3, 0.0, 0.0), (0.0, math.inf, 0.0))),
    dict(initial_state=OrbitState(EP, (0.0, 0.0, 0.0), (0.0, 7546.0, 0.0))),
])
def test_invalid_input_is_a_value_error_and_returns_promptly(kw):
    args = dict(initial_state=GOOD, duration_sec=600.0, step_sec=30.0)
    args.update(kw)
    with pytest.raises(ValueError):
        call_with_deadline(**args)


def test_zero_duration_returns_the_initial_state_only():
    h = call_with_deadline(initial_state=GOOD, duration_sec=0.0, step_sec=30.0)
    assert h == [GOOD]


@pytest.mark.parametrize("force", ["include_drag", "include_srp"])
def test_unavailable_force_is_refused_not_dropped(monkeypatch, force):
    # simulate an environment without star_weather (the module binds None when the import fails)
    import star_orbit.core as core
    monkeypatch.setattr(core, "compute_drag_acceleration", None)
    monkeypatch.setattr(core, "compute_srp_acceleration", None)
    with pytest.raises(RuntimeError):
        call_with_deadline(initial_state=GOOD, duration_sec=60.0, step_sec=30.0, **{force: True})


def test_valid_propagation_is_finite_and_has_expected_length():
    h = call_with_deadline(initial_state=GOOD, duration_sec=600.0, step_sec=30.0)
    assert len(h) == 21 and all(math.isfinite(x) for s in h for x in (*s.r, *s.v))
