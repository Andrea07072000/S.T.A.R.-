"""Tests of the Lambert-solver auditor with synthetic implementations (no third-party library needed).
Verifies: R14 (README).

The auditor must: validate each solver on Curtis Example 5.2 before comparing it; measure the error against the v1 of a
known orbit (truth built without any Lambert solver); count a non-finite answer as a refusal; record hostile-input
behaviour; never compare a solver that failed validation. The SHORTWAY defect below is the one measured in real
libraries (a direction flag that silently means "short way"): up to tens of km/s on transfers beyond 180 degrees."""
import math
import sys

import pytest

import lambert_audit as la
from corpus_fingerprint import fingerprint

CMD = [sys.executable, "-c"]
SAFE = '''
import math
def _stumpff(z):
    if z > 1e-8:
        s = math.sqrt(z); return (s - math.sin(s)) / s ** 3, (1 - math.cos(s)) / z
    if z < -1e-8:
        s = math.sqrt(-z); return (math.sinh(s) - s) / s ** 3, (math.cosh(s) - 1) / -z
    return 1 / 6 - z / 120, 0.5 - z / 24
def lambert(r1, r2, tof, mu, shortway_only=False):
    if not all(map(math.isfinite, (tof, mu, *r1, *r2))) or tof <= 0 or mu <= 0:
        raise ValueError("invalid input")
    a, b = math.sqrt(sum(x * x for x in r1)), math.sqrt(sum(x * x for x in r2))
    if a == 0 or b == 0:
        raise ValueError("zero vector")
    c = max(-1.0, min(1.0, sum(x * y for x, y in zip(r1, r2)) / (a * b)))
    dnu = math.acos(c)
    if not shortway_only and r1[0] * r2[1] - r1[1] * r2[0] < 0:
        dnu = 2 * math.pi - dnu
    if 1 - math.cos(dnu) < 1e-15 or abs(math.sin(dnu)) < 1e-12:
        raise ValueError("degenerate geometry")
    A = math.sin(dnu) * math.sqrt(a * b / (1 - math.cos(dnu)))
    def y(z):
        S, C = _stumpff(z); return a + b + A * (z * S - 1) / math.sqrt(C)
    def F(z):
        yy = y(z)
        if yy < 0: return -1.0
        S, C = _stumpff(z); return (yy / C) ** 1.5 * S + A * math.sqrt(yy) - math.sqrt(mu) * tof
    z = -100.0
    while F(z) < 0:
        z += 0.1
        if z > 4 * math.pi ** 2: raise RuntimeError("no bracket")
    lo, hi = z - 0.1, z
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if F(mid) < 0: lo = mid
        else: hi = mid
    yy = y(hi); f, g = 1 - yy / a, A * math.sqrt(yy / mu)
    return [(q - f * p) / g for p, q in zip(r1, r2)]
'''
SHORTWAY = SAFE + "_safe = lambert\ndef lambert(r1, r2, tof, mu):\n    return _safe(r1, r2, tof, mu, shortway_only=True)\n"
NAN_HIGH_E = SAFE + ("_safe2 = lambert\ndef lambert(r1, r2, tof, mu):\n    v = _safe2(r1, r2, tof, mu)\n"
                     "    return [float('nan')] * 3 if abs(tof - round(tof)) > -1 and mu == 398600.4418 and "
                     "math.dist(r1, [0, 0, 0]) > 30000 else v\n")
IDENTITY = "def lambert(r1, r2, tof, mu):\n    return r1\n"
CASES = la.corpus()


def impl(driver, lineage):
    return {"command": CMD, "driver": driver, "lineage": lineage}


def test_truth_needs_no_solver_and_is_pinned():
    c = la.case(26600.0, 0.5, math.radians(45), math.radians(40), math.radians(25), math.radians(30), math.radians(250))
    p = 26600.0 * (1 - 0.25)
    assert abs(math.dist(c["r1"], [0, 0, 0]) - p / (1 + 0.5 * math.cos(math.radians(30)))) < 1e-9
    assert abs(math.dist(c["r2"], [0, 0, 0]) - p / (1 + 0.5 * math.cos(math.radians(280)))) < 1e-9
    energy = 0.5 * sum(x * x for x in c["v1"]) - la.MU / math.dist(c["r1"], [0, 0, 0])
    assert abs(energy + la.MU / (2 * 26600.0)) < 1e-9          # vis-viva: the v1 belongs to that orbit
    period = 2 * math.pi * math.sqrt(26600.0 ** 3 / la.MU)
    def mean(nu_deg, e=0.5):       # independent route: cos E = (e + cos nu) / (1 + e cos nu), sign of sin nu
        nu = math.radians(nu_deg)
        E = math.acos((e + math.cos(nu)) / (1 + e * math.cos(nu)))
        E = E if math.sin(nu) >= 0 else 2 * math.pi - E
        return E - e * math.sin(E)
    assert abs(c["tof"] / period - (mean(280.0) - mean(30.0)) / (2 * math.pi)) < 1e-12
    assert len(CASES) == 315
    assert fingerprint(CASES) == "83a4ebc7fa490229462c8e933455a8fb6b599316a3ab0481dfc5eeee29bfb8be"


def test_safe_solver_is_validated_and_matches_the_truth_everywhere():
    r = la.audit({"safe": impl(SAFE, "A")})
    assert r["validated"] == ["safe"] and r["validation"]["safe"]["curtis_err_kms"] < 1e-4
    assert all(b["n"] == 63 and b["refused"] == 0 and b["max_err_kms"] < 1e-6 for b in r["vs_truth"]["safe"].values())
    assert r["hostile"]["safe"] == {"tof_nan": "error:ValueError", "tof_zero": "error:ValueError",
                                    "tof_negative": "error:ValueError", "r1_zero": "error:ValueError",
                                    "r1_nan": "error:ValueError", "transfer_180": "error:ValueError",
                                    "transfer_0": "error:ValueError"}


def test_short_way_flag_defect_passes_the_probe_but_is_measured_on_long_transfers():
    r = la.audit({"safe": impl(SAFE, "A"), "short": impl(SHORTWAY, "B")})
    assert r["validated"] == ["safe", "short"]                 # Curtis 5.2 is a short-way case: the probe cannot see it
    assert max(b["max_err_kms"] for b in r["vs_truth"]["short"].values()) > 10.0
    assert r["pairs"]["safe|short"]["max_kms"] > 10.0 and r["pairs"]["safe|short"]["same_lineage"] is False


def test_nan_answers_are_refusals_not_agreement():
    r = la.audit({"nan": impl(NAN_HIGH_E, "A")})
    refused = sum(b["refused"] for b in r["vs_truth"]["nan"].values())
    assert refused == sum(1 for c in CASES if math.dist(c["r1"], [0, 0, 0]) > 30000) > 0
    assert all(b["max_err_kms"] < 1e-6 for b in r["vs_truth"]["nan"].values())


def test_solver_failing_the_probe_is_never_compared():
    r = la.audit({"safe": impl(SAFE, "A"), "identity": impl(IDENTITY, "B")}, cases=CASES[:5])
    assert r["validated"] == ["safe"] and r["pairs"] == {} and "identity" not in r["vs_truth"]


def test_identical_solvers_have_zero_difference_and_same_lineage_is_reported():
    r = la.audit({"a": impl(SAFE, "A"), "b": impl(SAFE, "A")}, cases=CASES[:21])
    assert r["pairs"]["a|b"] == {"max_kms": 0.0, "same_lineage": True} and r["cases"] == 21


def test_probe_tolerance_boundary_and_stdout_noise():
    off = "print('solver banner')\ndef lambert(r1, r2, tof, mu):\n    return [-5.9925 + %r, 1.9254, 3.2456]\n"
    assert la.audit({"x": impl(off % 0.9e-4, "A")}, cases=CASES[:1])["validation"]["x"]["valid"] is True
    assert la.audit({"x": impl(off % 1.1e-4, "A")}, cases=CASES[:1])["validation"]["x"]["valid"] is False


def test_hostile_set_and_categories():
    assert [h[0] for h in la.HOSTILE] == ["tof_nan", "tof_zero", "tof_negative", "r1_zero", "r1_nan", "transfer_180",
                                          "transfer_0"]
    a, b = "[7000.0, 0.0, 0.0]", "[0.0, 7000.0, 0.0]"          # the whole hostile set is part of the specification
    assert [repr(h[1:]) for h in la.HOSTILE] == [
        f"({a}, {b}, nan)", f"({a}, {b}, 0.0)", f"({a}, {b}, -100.0)", f"([0.0, 0.0, 0.0], {b}, 3000.0)",
        f"([nan, 0.0, 0.0], {b}, 3000.0)", f"({a}, [-7000.0, 0.0, 0.0], 3000.0)", f"({a}, [8000.0, 0.0, 0.0], 3000.0)"]
    assert (la.MU, la.VALIDATION_TOL_KMS, la.CURTIS["tof"], la.CURTIS["mu"]) == (398600.4418, 1e-4, 3600.0, 398600.0)
    assert (la.A_KM, la.ECC, la.INC_DEG) == ((7000.0, 26600.0, 42164.0), (0.0, 0.1, 0.5, 0.8, 0.95), (5.0, 45.0, 80.0))
    assert la.DNU_DEG == (10.0, 60.0, 120.0, 170.0, 190.0, 250.0, 330.0)
    assert la.category({"v": [1.0, float("nan"), 0.0]}) == "nan" and la.category({"v": [float("inf"), 0.0, 0.0]}) == "inf"
    assert la.category({"v": [1.0, 2.0, 3.0]}) == "value" and la.category({"error": "ValueError: x"}) == "error:ValueError"


@pytest.mark.parametrize("vec", [[1.0, 2.0], [1.0, 2.0, 3.0, 4.0]])
def test_wrong_length_answer_is_a_refusal(vec):
    drv = SAFE + f"_s3 = lambert\ndef lambert(r1, r2, tof, mu):\n    return _s3(r1, r2, tof, mu) if mu == 398600.0 else {vec!r}\n"
    r = la.audit({"x": impl(drv, "A")}, cases=CASES[:6])
    assert r["validated"] == ["x"] and sum(b["refused"] for b in r["vs_truth"]["x"].values()) == 6
