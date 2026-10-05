"""Reference for the TCA refinement used by the screening: CCSDS 508.0-B-1 example 3.6.2 (official CDM) gives the two
state vectors AT TCA (2010-03-13T22:37:52.618) with MISS_DISTANCE 715 m (the states themselves give 715.75 m).
Starting the refinement 40 s before TCA with two-body motion, it must return TCA within 1 ms and the miss distance of
the published states within 1 m. Propagation here is an independent RK4 two-body integrator (not SGP4)."""
import math

import numpy as np

from screen import refine_tca

MU = 398600.4418
O1 = (np.array([2570.097065, 2244.654904, 6281.497978]), np.array([4.418769571, 4.833547743, -3.526774282]))
O2 = (np.array([2569.540800, 2245.093614, 6281.599946]), np.array([-2.888612500, -6.007247516, 3.328770172]))


def _rk4(r, v, dt, n=400):
    h = dt / n
    acc = lambda x: -MU * x / np.linalg.norm(x) ** 3
    for _ in range(n):
        k1v, k1r = acc(r), v
        k2v, k2r = acc(r + h / 2 * k1r), v + h / 2 * k1v
        k3v, k3r = acc(r + h / 2 * k2r), v + h / 2 * k2v
        k4v, k4r = acc(r + h * k3r), v + h * k3v
        r, v = r + h / 6 * (k1r + 2 * k2r + 2 * k3r + k4r), v + h / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
    return r, v


def test_refinement_recovers_published_tca_and_miss():
    start = -40.0  # coarse sample 40 s before the published TCA
    def state_at(t):
        r1, v1 = _rk4(*O1, start + t)
        r2, v2 = _rk4(*O2, start + t)
        return r1, v1, r2, v2
    tsec, miss_km = refine_tca(state_at, step=60.0)
    assert abs((start + tsec) - 0.0) < 1e-3                  # TCA within 1 ms of the published one
    assert abs(miss_km * 1000 - 715.75) < 1.0                 # miss of the published states (CDM prints 715 m)
    assert abs(miss_km * 1000 - 715) < 1.0                    # and within 1 m of the printed MISS_DISTANCE
