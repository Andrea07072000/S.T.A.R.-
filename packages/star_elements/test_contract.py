"""Non-finite input contract, from a probe of R3/R4 with hostile inputs (2026-10-05).
Verifies: R3, R4 (README).

Found by the probe: rv_to_coe with a NaN or inf component returned NaN/inf elements, coe_to_rv returned NaN/inf vectors,
the anomaly conversions returned NaN for a NaN angle, and mean_to_eccentric reported a NaN mean anomaly as "did not
converge". R3 says no arbitrary value is ever returned for an undefined element: all of these now raise ValueError."""
import math

import pytest

import star_elements as E

R, V = (7000.0, 0.0, 10.0), (0.0, 7.5, 1.0)
NAN, INF = math.nan, math.inf


@pytest.mark.parametrize("r,v", [((NAN, 0.0, 0.0), V), ((INF, 0.0, 0.0), V), (R, (0.0, -INF, 1.0)), (R, (0.0, 7.5, NAN))])
def test_rv_to_coe_rejects_non_finite(r, v):
    with pytest.raises(ValueError):
        E.rv_to_coe(r, v)


@pytest.mark.parametrize("k", range(6))
@pytest.mark.parametrize("bad", [NAN, INF])
def test_coe_to_rv_rejects_non_finite(k, bad):
    coe = [52000.0, 0.1, 0.5, 0.1, 0.2, 0.3]
    coe[k] = bad
    with pytest.raises(ValueError):
        E.coe_to_rv(*coe, 398600.4418)


@pytest.mark.parametrize("f", [E.mean_to_eccentric, E.eccentric_to_true, E.true_to_eccentric, E.eccentric_to_mean])
@pytest.mark.parametrize("bad", [NAN, INF, -INF])
def test_anomaly_conversions_reject_non_finite_angle(f, bad):
    with pytest.raises(ValueError):
        f(bad, 0.2)


def test_finite_inputs_still_work():
    h, e, i, raan, argp, nu = E.rv_to_coe(R, V)
    r, v = E.coe_to_rv(h, e, i, raan, argp, nu)
    assert all(abs(a - b) < 1e-6 for a, b in zip((*r, *v), (*R, *V)))
