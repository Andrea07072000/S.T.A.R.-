"""Invalid-input contract, from a probe of R3 with hostile inputs (2026-10-05).
Verifies: R3 (README).

Found by the probe: vis_viva(7000, 3000) returned a complex number (r > 2a), combined_dv(7.5, nan, 0.1) returned 0.0,
hohmann with mu < 0 returned delta-v values, and NaN/inf propagated as results. All now raise ValueError."""
import math

import pytest

import star_maneuver as M

NAN, INF = math.nan, math.inf


@pytest.mark.parametrize("call", [
    lambda: M.vis_viva(7000.0, 3000.0), lambda: M.vis_viva(NAN, 7000.0), lambda: M.vis_viva(INF, 7000.0),
    lambda: M.vis_viva(7000.0, 7000.0, 0.0), lambda: M.vis_viva(7000.0, 7000.0, -1.0),
    lambda: M.hohmann(NAN, 42164.0), lambda: M.hohmann(7000.0, INF), lambda: M.hohmann(7000.0, 42164.0, -1.0),
    lambda: M.hohmann(7000.0, 42164.0, NAN), lambda: M.bielliptic(7000.0, 42164.0, NAN),
    lambda: M.bielliptic(7000.0, 42164.0, INF), lambda: M.bielliptic(7000.0, 42164.0, 100000.0, 0.0),
    lambda: M.plane_change(NAN, 0.1), lambda: M.plane_change(7.5, NAN), lambda: M.plane_change(7.5, INF),
    lambda: M.combined_dv(7.5, NAN, 0.1), lambda: M.combined_dv(NAN, 3.0, 0.1), lambda: M.combined_dv(7.5, 3.0, INF),
])
def test_invalid_input_is_a_value_error(call):
    with pytest.raises(ValueError):
        call()


def test_r_equal_2a_is_the_boundary_and_gives_zero_speed():
    assert M.vis_viva(14000.0, 7000.0) == 0.0


def test_results_are_real_floats():
    out = M.hohmann(6678.0, 42164.0)
    assert all(type(v) is float and math.isfinite(v) for v in out.values())
    assert type(M.vis_viva(7000.0, 7000.0)) is float
