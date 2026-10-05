"""Tests of the Kepler-equation auditor with synthetic implementations (no third-party library needed).
Verifies: R13 (README).

The auditor must: validate each implementation on Vallado Example 2-1 before comparing it; measure the circular error
against a 40-digit truth; count a non-finite answer as a refusal; record hostile-input behaviour as a category; and
never compare an implementation that failed validation. The defects below are the ones found in real libraries."""
import math
import sys

import pytest

import kepler_audit as ka
from corpus_fingerprint import fingerprint

CMD = [sys.executable, "-c"]
SAFE = ("import math\n"
        "def m_to_e(M, e):\n"
        "    if not 0 <= e < 1 or not math.isfinite(M):\n        raise ValueError('domain')\n"
        "    M = M % (2 * math.pi); lo, hi = 0.0, 2 * math.pi; E = math.pi\n"
        "    for _ in range(200):\n"
        "        f = E - e * math.sin(E) - M\n"
        "        if f < 0: lo = E\n        else: hi = E\n"
        "        n = E - f / (1 - e * math.cos(E))\n"
        "        if not lo < n < hi: n = 0.5 * (lo + hi)\n"
        "        if abs(n - E) < 1e-15: return n\n"
        "        E = n\n"
        "    return E\n")
# Basilisk 2.12 pattern: Newton from E0 = M, returns the unconverged value after the iteration cap
NAIVE = ("import math\ndef m_to_e(M, e):\n    E = M\n    for _ in range(200):\n"
         "        d = (E - e * math.sin(E) - M) / (1 - e * math.cos(E)); E -= d\n"
         "        if abs(d) < 1e-15: break\n    return E\n")
NAN_HIGH_E = SAFE + "_s = m_to_e\ndef m_to_e(M, e):\n    return float('nan') if e > 0.99 else _s(M, e)\n"
IDENTITY = "def m_to_e(M, e):\n    return M\n"
SMALL = [c for c in ka.corpus(n=8)]


def impl(driver, lineage):
    return {"command": CMD, "driver": driver, "lineage": lineage}


def test_vallado_probe_constant_is_consistent_with_the_forward_map():
    E = math.radians(ka.VALLADO_E_DEG)
    M = math.degrees(E - ka.VALLADO_ECC * math.sin(E))
    assert abs(M - ka.VALLADO_M_DEG) < 1e-9


def test_corpus_truth_solves_the_equation_and_is_pinned():
    assert all(abs(c["truth"] - c["e"] * math.sin(c["truth"]) - c["M"]) < 1e-14 for c in ka.corpus())
    assert fingerprint(ka.corpus()) == "913b8b833ea44ace4fb199e30aea2f8bb4121cb2b087b969a22020e6c7a1e6b7"


def test_safe_solver_is_validated_and_accurate():
    r = ka.audit({"safe": impl(SAFE, "A")}, cases=SMALL)
    assert r["validated"] == ["safe"]
    assert max(b["max_err_rad"] for b in r["vs_truth"]["safe"].values()) < 1e-11
    assert r["hostile"]["safe"]["M_nan"] == "error:ValueError" and r["hostile"]["safe"]["M_huge"] == "value"


def test_naive_newton_divergence_near_e_one_is_measured_not_hidden():
    r = ka.audit({"safe": impl(SAFE, "A"), "naive": impl(NAIVE, "B")})  # full grid: holds M = 0.228, e = 0.9999
    worst = max(b["max_err_rad"] for b in r["vs_truth"]["naive"].values())
    assert worst > 1e-3                     # the divergent value at e = 0.9999 is reported as an error
    assert r["pairs"]["naive|safe"]["max_rad"] > 1e-3


def test_nan_answers_are_refusals():
    r = ka.audit({"nan": impl(NAN_HIGH_E, "A")}, cases=SMALL)
    refused = {e: b["refused"] for e, b in r["vs_truth"]["nan"].items()}
    assert refused["0.999"] == refused["0.9999"] == 13 and refused["0.5"] == 0


def test_implementation_failing_validation_is_never_compared():
    r = ka.audit({"safe": impl(SAFE, "A"), "identity": impl(IDENTITY, "B")}, cases=SMALL)
    assert r["validated"] == ["safe"] and r["pairs"] == {} and "identity" not in r["vs_truth"]
    assert r["validation"]["identity"]["valid"] is False


def test_hostile_set_is_the_specified_one_and_classified_in_order():
    assert [(n, repr(m), repr(e)) for n, m, e in ka.HOSTILE] == [
        ("M_nan", "nan", "0.5"), ("e_nan", "1.0", "nan"), ("e_one", "1.0", "1.0"), ("e_hyperbolic", "1.0", "1.5"),
        ("e_negative", "1.0", "-0.1"), ("M_inf", "inf", "0.5"), ("M_huge", "1000000000000.0", "0.5"),
        ("M_negative", "-1.0", "0.5")]
    r = ka.audit({"safe": impl(SAFE, "A")}, cases=SMALL)
    assert r["hostile"]["safe"] == {"M_nan": "error:ValueError", "e_nan": "error:ValueError",
                                    "e_one": "error:ValueError", "e_hyperbolic": "error:ValueError",
                                    "e_negative": "error:ValueError", "M_inf": "error:ValueError",
                                    "M_huge": "value", "M_negative": "value"}


def test_category_of_nan_inf_and_value():
    assert ka.category({"v": float("nan")}) == "nan" and ka.category({"v": float("inf")}) == "inf"
    assert ka.category({"v": 1.0}) == "value" and ka.category({"error": "ValueError: x"}) == "error:ValueError"


def test_truth_is_exact_to_double_precision_on_the_hardest_cases():
    from mpmath import findroot, mp, mpf, sin
    hard = [c for c in ka.corpus() if c["e"] == 0.9999][:12]
    mp.dps = 60
    for c in hard:
        ref = float(findroot(lambda E: E - mpf(c["e"]) * sin(E) - mpf(c["M"]), mpf(c["truth"])))
        assert abs(ref - c["truth"]) <= 1e-15 * max(1.0, abs(ref))


def test_driver_noise_before_the_json_line_is_ignored():
    # Basilisk prints 'Iteration error ...' on stdout before the runner's JSON line
    noisy = "print('Iteration error in M2E')\n" + SAFE
    r = ka.audit({"noisy": impl(noisy, "A")}, cases=SMALL)
    assert r["validated"] == ["noisy"]


def test_identical_implementations_have_zero_pairwise_difference_and_counts_are_exact():
    r = ka.audit({"a": impl(SAFE, "A"), "b": impl(SAFE, "A")}, cases=SMALL)
    assert r["pairs"]["a|b"] == {"max_rad": 0.0, "same_lineage": True}
    assert r["cases"] == len(SMALL) and all(b["n"] == 13 and b["refused"] == 0 for b in r["vs_truth"]["a"].values())
    assert all(b["max_err_rad"] < 1e-11 for b in r["vs_truth"]["a"].values())


def test_probe_tolerance_boundary():
    off = "import math\ndef m_to_e(M, e):\n    return math.radians(220.512074767522) + %r\n"
    assert ka.audit({"x": impl(off % 0.9e-9, "A")}, cases=SMALL[:1])["validation"]["x"]["valid"] is True
    assert ka.audit({"x": impl(off % 1.1e-9, "A")}, cases=SMALL[:1])["validation"]["x"]["valid"] is False


@pytest.mark.parametrize("a,b,d", [(0.0, 2 * math.pi, 0.0), (0.1, 2 * math.pi - 0.1, 0.2), (1.0, 1.5, 0.5),
                                   (3.0, 0.2, 2.8), (0.2, 3.0, 2.8), (6.0, 0.5, 0.5 + 2 * math.pi - 6.0)])
def test_circular_difference(a, b, d):
    assert abs(ka.circ(a, b) - d) < 1e-12
