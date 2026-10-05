"""Error contract of lambert(), from a probe of R3 with hostile inputs (2026-10-05).
Verifies: R2, R3 (README).

Found by the probe: a 0-degree transfer raised ZeroDivisionError (R3 promises ValueError for 0 or 180 deg), NaN/inf
positions raised ZeroDivisionError, a NaN/inf time of flight was reported as "did not converge", and mu <= 0 gave a
misleading domain error. All are invalid input and now raise ValueError; RuntimeError stays for real non-convergence."""
import math

import pytest

from star_lambert import lambert

R1, R2 = (7000.0, 0.0, 0.0), (0.0, 7000.0, 0.0)


@pytest.mark.parametrize("r2", [(8000.0, 0.0, 0.0), (7000.0, 0.0, 0.0), (-7000.0, 0.0, 0.0), (-9000.0, 0.0, 0.0)])
def test_zero_and_180_degree_transfers_are_degenerate(r2):
    with pytest.raises(ValueError):
        lambert(R1, r2, 3000.0)


@pytest.mark.parametrize("kw", [dict(tof=math.nan), dict(tof=math.inf), dict(tof=0.0), dict(tof=-1.0),
                                dict(mu=0.0), dict(mu=-1.0), dict(mu=math.nan),
                                dict(r1=(math.nan, 0.0, 0.0)), dict(r1=(math.inf, 0.0, 0.0)), dict(r2=(0.0, -math.inf, 0.0)),
                                dict(r1=(0.0, 0.0, 0.0))])
def test_invalid_input_is_a_value_error(kw):
    args = dict(r1=R1, r2=R2, tof=3000.0)
    args.update(kw)
    with pytest.raises(ValueError):
        lambert(**args)


def test_iteration_budget_too_small_is_a_runtime_error_not_a_value():
    with pytest.raises(RuntimeError):
        lambert(R1, R2, 3000.0, max_iter=1)


def test_valid_quarter_transfer_still_solves():
    v1, v2 = lambert(R1, R2, 3000.0)
    assert all(map(math.isfinite, (*v1, *v2)))
