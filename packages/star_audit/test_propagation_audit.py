"""Tests of the two-body propagator auditor with synthetic implementations (no third-party library needed).
Verifies: R15 (README).

The auditor must: validate each propagator on Vallado Example 2-4 before comparing it; measure position and velocity
error against the closed-form state of a known orbit, also after 10 whole revolutions; count a non-finite or
wrong-length answer as a refusal; run each hostile input alone with a deadline and record a solver that never answers
as "error:Hang" (the first real audit hung for 30 minutes inside one library); never compare a propagator that failed
validation."""
import math
import sys

import pytest

import propagation_audit as pa
from corpus_fingerprint import fingerprint

CMD = [sys.executable, "-c"]
# universal-variable Kepler propagator (Vallado Alg. 8 form) with a bracketed Newton: independent of the truth generator
SAFE = '''
import math
def _stumpff(z):
    if z > 1e-8:
        s = math.sqrt(z); return (1 - math.cos(s)) / z, (s - math.sin(s)) / s ** 3
    if z < -1e-8:
        s = math.sqrt(-z); return (math.cosh(s) - 1) / -z, (math.sinh(s) - s) / s ** 3
    return 0.5 - z / 24, 1 / 6 - z / 120
def propagate(r0, v0, tof, mu, rate=1.0):
    if not all(map(math.isfinite, (tof, mu, *r0, *v0))) or mu <= 0:
        raise ValueError("invalid input")
    R = math.sqrt(sum(x * x for x in r0))
    if R == 0:
        raise ValueError("zero position")
    V2 = sum(x * x for x in v0); rv = sum(x * y for x, y in zip(r0, v0))
    alpha = 2 / R - V2 / mu
    if alpha <= 0:
        raise ValueError("not elliptic")
    dt = tof * rate; sm = math.sqrt(mu)
    def F(x):
        C, S = _stumpff(alpha * x * x)
        return rv / sm * x * x * C + (1 - alpha * R) * x ** 3 * S + R * x - sm * dt
    period_x = 2 * math.pi / math.sqrt(alpha)
    k = math.floor(sm * dt * alpha / period_x)              # whole revolutions already contained in dt
    lo, hi = k * period_x - period_x, (k + 2) * period_x
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if F(mid) < 0: lo = mid
        else: hi = mid
    x = 0.5 * (lo + hi); C, S = _stumpff(alpha * x * x)
    f = 1 - x * x / R * C; g = dt - x ** 3 / sm * S
    r = [f * a + g * b for a, b in zip(r0, v0)]; Rn = math.sqrt(sum(q * q for q in r))
    fd = sm / (Rn * R) * x * (alpha * x * x * S - 1); gd = 1 - x * x / Rn * C
    return r + [fd * a + gd * b for a, b in zip(r0, v0)]
'''
DRIFT = SAFE + "_s = propagate\ndef propagate(r0, v0, tof, mu):\n    return _s(r0, v0, tof, mu, rate=1.0 + 1e-9)\n"
NANNY = SAFE + "_s2 = propagate\ndef propagate(r0, v0, tof, mu):\n    return [float('nan')] * 6 if tof > 5e5 else _s2(r0, v0, tof, mu)\n"
HANGS = SAFE + ("_s3 = propagate\ndef propagate(r0, v0, tof, mu):\n    while tof != tof:\n        pass\n"
                "    return _s3(r0, v0, tof, mu)\n")
IDENTITY = "def propagate(r0, v0, tof, mu):\n    return list(r0) + list(v0)\n"
CASES = pa.corpus()


def impl(driver, lineage):
    return {"command": CMD, "driver": driver, "lineage": lineage}


def test_truth_is_a_known_orbit_and_is_pinned():
    c = pa.case(26600.0, 0.5, math.radians(63.4), math.radians(40), math.radians(25), math.radians(30), math.radians(100), revs=10)
    for s in (c["r0"] + c["v0"], c["truth"]):                           # energy and angular momentum of that orbit
        r, v2 = math.dist(s[:3], [0, 0, 0]), sum(x * x for x in s[3:])
        assert abs(0.5 * v2 - pa.MU / r + pa.MU / (2 * 26600.0)) < 1e-9
        h = [s[1] * s[5] - s[2] * s[4], s[2] * s[3] - s[0] * s[5], s[0] * s[4] - s[1] * s[3]]
        assert abs(math.dist(h, [0, 0, 0]) - math.sqrt(pa.MU * 26600.0 * 0.75)) < 1e-6
    period = 2 * math.pi * math.sqrt(26600.0 ** 3 / pa.MU)
    assert 10 * period < c["tof"] < 11 * period
    assert len(CASES) == 450 and sum(c["revs"] == 10 for c in CASES) == 225
    assert fingerprint(CASES) == "26e925013c27c8989d3096db6f83ae8eff7168198362a98ab02fa1575adae1b3"


def test_constants_are_the_specified_ones():
    assert (pa.MU, pa.VALIDATION_TOL_KM, pa.VALIDATION_TOL_KMS, pa.HOSTILE_DEADLINE_S) == (398600.4418, 1e-3, 1e-5, 120)
    assert (pa.A_KM, pa.ECC, pa.INC_DEG) == ((7000.0, 26600.0, 42164.0), (0.0, 0.1, 0.5, 0.8, 0.95), (5.0, 63.4, 98.0))
    assert (pa.DNU_DEG, pa.REVS) == ((15.0, 100.0, 179.0, 181.0, 300.0), (0, 10))
    assert pa.VALLADO == {"r0": [1131.340, -2282.343, 6672.423], "v0": [-5.64305, 4.30333, 2.42879], "tof": 2400.0,
                          "r": [-4219.7527, 4363.0292, -3958.7666], "v": [3.689866, -1.916735, -6.112511]}
    a, v = "[7000.0, 0.0, 0.0]", "[0.0, 7.5, 0.0]"
    assert [repr(h) for h in pa.HOSTILE] == [
        f"('tof_nan', {a}, {v}, nan, 398600.4418)", f"('r_zero', [0.0, 0.0, 0.0], {v}, 100.0, 398600.4418)",
        f"('r_nan', [nan, 0.0, 0.0], {v}, 100.0, 398600.4418)", f"('mu_negative', {a}, {v}, 100.0, -1.0)",
        f"('tof_huge', {a}, {v}, 1000000000000.0, 398600.4418)", f"('tof_negative', {a}, {v}, -3600.0, 398600.4418)"]


def test_safe_propagator_is_validated_and_accurate_after_ten_revolutions():
    r = pa.audit({"safe": impl(SAFE, "A")})
    v = r["validation"]["safe"]
    assert r["validated"] == ["safe"] and v["vallado_pos_err_km"] < 1e-3 and v["vallado_vel_err_kms"] < 1e-5
    assert len(r["vs_truth"]["safe"]) == 10 and all(b["n"] == 45 and b["refused"] == 0 for b in r["vs_truth"]["safe"].values())
    assert max(b["max_pos_err_km"] for b in r["vs_truth"]["safe"].values()) < 1e-4
    assert max(b["max_vel_err_kms"] for b in r["vs_truth"]["safe"].values()) < 1e-7
    assert r["hostile"]["safe"]["tof_nan"] == r["hostile"]["safe"]["r_zero"] == "error:ValueError"
    assert r["hostile"]["safe"]["tof_huge"] == "value"


def test_a_clock_rate_error_passes_the_probe_and_shows_only_after_many_revolutions():
    r = pa.audit({"safe": impl(SAFE, "A"), "drift": impl(DRIFT, "B")})
    assert r["validated"] == ["drift", "safe"]
    worst = {k: b["max_pos_err_km"] for k, b in r["vs_truth"]["drift"].items()}
    assert max(v for k, v in worst.items() if k.endswith("revs=10")) > 10 * max(v for k, v in worst.items() if k.endswith("revs=0"))
    assert r["pairs"]["drift|safe"]["max_pos_km"] > 1e-3 and r["pairs"]["drift|safe"]["same_lineage"] is False


def test_nan_answers_are_refusals():
    r = pa.audit({"nan": impl(NANNY, "A")})
    refused = sum(b["refused"] for b in r["vs_truth"]["nan"].values())
    assert refused == sum(1 for c in CASES if c["tof"] > 5e5) > 0
    assert all(b["max_pos_err_km"] < 1e-4 for b in r["vs_truth"]["nan"].values())


def test_a_propagator_that_never_answers_is_recorded_as_hang(monkeypatch):
    monkeypatch.setattr(pa, "HOSTILE_DEADLINE_S", 5)
    r = pa.audit({"hang": impl(HANGS, "A")}, cases=CASES[:4])
    assert r["hostile"]["hang"]["tof_nan"] == "error:Hang"
    assert r["hostile"]["hang"]["r_zero"] == "error:ValueError" and r["validated"] == ["hang"]


def test_failed_probe_is_never_compared_and_wrong_length_is_a_refusal():
    r = pa.audit({"safe": impl(SAFE, "A"), "identity": impl(IDENTITY, "B")}, cases=CASES[:5])
    assert r["validated"] == ["safe"] and r["pairs"] == {} and "identity" not in r["vs_truth"]
    short = SAFE + "_s4 = propagate\ndef propagate(r0, v0, tof, mu):\n    s = _s4(r0, v0, tof, mu)\n    return s if tof == 2400.0 else s[:3]\n"
    r = pa.audit({"x": impl(short, "A")}, cases=CASES[:6])
    assert r["validated"] == ["x"] and sum(b["refused"] for b in r["vs_truth"]["x"].values()) == 6


def test_identical_propagators_probe_boundary_and_categories():
    r = pa.audit({"a": impl(SAFE, "A"), "b": impl(SAFE, "A")}, cases=CASES[:20])
    assert r["pairs"]["a|b"] == {"max_pos_km": 0.0, "same_lineage": True} and r["cases"] == 20
    off = "print('banner')\ndef propagate(r0, v0, tof, mu):\n    return [-4219.7527 + %r, 4363.0292, -3958.7666, 3.689866, -1.916735, -6.112511]\n"
    assert pa.audit({"x": impl(off % 0.9e-3, "A")}, cases=CASES[:1])["validation"]["x"]["valid"] is True
    assert pa.audit({"x": impl(off % 1.1e-3, "A")}, cases=CASES[:1])["validation"]["x"]["valid"] is False
    offv = "def propagate(r0, v0, tof, mu):\n    return [-4219.7527, 4363.0292, -3958.7666, 3.689866 + %r, -1.916735, -6.112511]\n"
    assert pa.audit({"x": impl(offv % 0.9e-5, "A")}, cases=CASES[:1])["validation"]["x"]["valid"] is True
    assert pa.audit({"x": impl(offv % 1.1e-5, "A")}, cases=CASES[:1])["validation"]["x"]["valid"] is False
    assert pa.category({"s": [1.0, float("nan")]}) == "nan" and pa.category({"s": [float("inf")]}) == "inf"
    assert pa.category({"s": [1.0] * 6}) == "value" and pa.category({"error": "Hang: no answer"}) == "error:Hang"


def test_a_slow_start_is_not_a_hang_only_the_answer_time_counts(monkeypatch):
    # process start, imports and JIT compilation are not the solver's answer time: the first protocol timed the whole
    # process and, on a loaded machine, labelled a healthy solver "Hang" on a different case at each run
    monkeypatch.setattr(pa, "HOSTILE_DEADLINE_S", 4)
    slow_start = "import time\ntime.sleep(8)\n" + SAFE
    row = pa.run_hostile(CMD, slow_start, [[7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], 100.0, pa.MU])
    assert pa.category(row) == "value" and len(row["s"]) == 6
    assert pa.category(pa.run_hostile(CMD, slow_start, [[7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], float("nan"), pa.MU])) == "error:ValueError"
    assert pa.category(pa.run_hostile(CMD, HANGS, [[7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], float("nan"), pa.MU])) == "error:Hang"
    crash = "def propagate(r0, v0, tof, mu):\n    import os\n    if tof != 600.0: os._exit(3)\n    return [0.0] * 6\n"
    assert pa.category(pa.run_hostile(CMD, crash, [[7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], 100.0, pa.MU])) == "error:Crash"
    assert pa.WARMUP == [[7000.0, 0.0, 100.0], [0.0, 7.4, 1.0], 600.0, 398600.4418] and pa.STARTUP_LIMIT_S == 900
