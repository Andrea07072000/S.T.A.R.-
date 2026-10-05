"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_audit_20261004.json, score 0.328): the sampling grid
is part of the METHOD (changing it silently would make audits incomparable over time) and the external-interpreter
path was exercised only by real audits.
Verifies: R1, R2, R3 (README).
"""
import hashlib
import json
import sys

import pytest

from star_audit import ALTITUDES_M, LATS, LONS, points, run_external


def test_sampling_grid_is_frozen():
    assert ALTITUDES_M == (0.0, 1e3, 1e4, 1e5, 4e5, 1e6, 5e6, 2e7, 3.6e7)
    assert LATS == (-89.0, -60.0, -34.5, -10.0, 0.0, 15.0, 34.0, 51.5, 72.0, 89.0)
    assert LONS == (-170.0, -45.0, 0.0, 46.0, 120.0)
    digest = hashlib.sha256(json.dumps(points()).encode()).hexdigest()[:16]
    assert len(points()) == 450 and digest == "75a9636c5e7bc26e"     # frozen 2026-10-04 (order and values)


EXACT = ("import math\n"
         "A=6378137.0; F=1/298.257223563; E2=F*(2-F)\n"
         "def convert(x,y,z):\n"
         "    p=math.hypot(x,y); lon=math.atan2(y,x); lat=math.atan2(z,p*(1-E2))\n"
         "    for _ in range(60):\n"
         "        n=A/math.sqrt(1-E2*math.sin(lat)**2); h=p/math.cos(lat)-n\n"
         "        lat=math.atan2(z,p*(1-E2*n/(n+h)))\n"
         "    n=A/math.sqrt(1-E2*math.sin(lat)**2)\n"
         "    return math.degrees(lat), math.degrees(lon), p/math.cos(lat)-n\n")


def test_run_external_with_an_exact_library_in_another_interpreter():
    e = run_external(sys.executable, EXACT)
    assert e["worst"]["pos_err_m"] < 1e-6 and e["n_points"] == 450


def test_run_external_failure_raises():
    with pytest.raises(RuntimeError):
        run_external(sys.executable, "def convert(x, y, z):\n    raise ValueError('library broken')\n")
