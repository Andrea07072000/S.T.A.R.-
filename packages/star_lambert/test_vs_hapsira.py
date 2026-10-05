"""Differential test against an independent lineage: 24 seeded 3-D geometries (both directions, 20..340 deg) solved by
hapsira 0.18.0 (Izzo 2015) and frozen in fixtures/hapsira_reference.json (generator: fixtures/make_hapsira_reference.py).
Two different algorithms must agree to well below a metre per second; the earlier tests used one published example only
and left the direction logic (cross-product z sign, 2*pi - dnu) and the Stumpff series largely unchecked.
Verifies: R1 (README)."""
import json
import math
from pathlib import Path

import pytest

from star_lambert import MU_EARTH, _stumpff_c, _stumpff_s, _universal_functions, lambert

REF = json.loads((Path(__file__).parent / "fixtures" / "hapsira_reference.json").read_text(encoding="utf-8"))


def test_mu_matches_the_reference_constant():
    assert MU_EARTH == REF["mu"] == 398600.4418


@pytest.mark.parametrize("k", range(len(REF["cases"])))
def test_agrees_with_hapsira_izzo(k):
    c = REF["cases"][k]
    v1, v2 = lambert(c["r1"], c["r2"], c["tof"], prograde=c["prograde"])
    assert math.dist(v1, c["v1"]) < 1e-6 and math.dist(v2, c["v2"]) < 1e-6, (k, v1, c["v1"])


def test_reference_covers_both_directions_and_long_way():
    assert {c["prograde"] for c in REF["cases"]} == {True, False}
    # at least one long-way (> 180 deg in the requested direction) transfer
    def angle(c):
        r1, r2 = c["r1"], c["r2"]
        cosv = sum(a * b for a, b in zip(r1, r2)) / (math.dist(r1, [0, 0, 0]) * math.dist(r2, [0, 0, 0]))
        nu = math.acos(max(-1.0, min(1.0, cosv)))
        cz = r1[0] * r2[1] - r1[1] * r2[0]
        return nu if (cz >= 0) == c["prograde"] else 2 * math.pi - nu
    assert any(angle(c) > math.pi for c in REF["cases"]) and any(angle(c) < math.pi for c in REF["cases"])


def test_stumpff_series_slope_inside_the_series_band():
    z = 9e-9   # inside |z| < 1e-8: the series branch; first-order term z/24 (C) and z/120 (S) is ~1e-10, visible
    assert abs(_stumpff_c(z) - (0.5 - z / 24)) < 1e-17 and abs(_stumpff_c(-z) - (0.5 + z / 24)) < 1e-17
    assert abs(_stumpff_s(z) - (1 / 6 - z / 120)) < 1e-17 and abs(_stumpff_s(-z) - (1 / 6 + z / 120)) < 1e-17


def test_derivative_at_zero_uses_the_series_and_matches_numerical():
    c = REF["cases"][0]
    r1n, r2n = math.dist(c["r1"], [0, 0, 0]), math.dist(c["r2"], [0, 0, 0])
    A = 0.8 * math.sqrt(r1n * r2n)
    y, F, dF = _universal_functions(r1n, r2n, A, MU_EARTH, c["tof"])
    h = 1e-3
    num = (F(h) - F(-h)) / (2 * h)
    assert abs(dF(0.0) - num) < 1e-6 * abs(num)
    assert abs(dF(5e-9) - num) < 1e-6 * abs(num)        # still the series branch
