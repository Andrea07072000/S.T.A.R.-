# -*- coding: utf-8 -*-
"""Tests of the verification rules of star_crosscheck. Each test fails if its rule is removed from core.py.
Verifies: R1, R2, R3, R4, R5 (README)."""
import json
import sys

from star_crosscheck import AGREE, DEGRADED, DISAGREE, INSUFFICIENT, Engine, crosscheck


def const(v):
    return lambda inputs: v


def test_agree_needs_two_distinct_lineages():
    b = crosscheck("x", {}, [Engine("a", "L1", const(1.0)), Engine("b", "L2", const(1.0 + 1e-9))], 1e-6, "u")
    assert b["verdict"] == AGREE and b["independent_lineages"] == ["L1", "L2"]


def test_same_lineage_is_one_witness():
    b = crosscheck("x", {}, [Engine("a", "DE440", const(1.0)), Engine("b", "DE440", const(1.0))], 1e-6, "u")
    assert b["verdict"] == INSUFFICIENT


def test_disagreement_detected():
    b = crosscheck("x", {}, [Engine("a", "L1", const(1.0)), Engine("b", "L2", const(1.1))], 1e-3, "u")
    assert b["verdict"] == DISAGREE


def test_failed_engine_never_counts_as_agreement():
    def boom(_):
        raise RuntimeError("no data")
    b = crosscheck("x", {}, [Engine("a", "L1", const(1.0)), Engine("b", "L2", boom)], 1e-3, "u")
    assert b["verdict"] == INSUFFICIENT and b["n_failed"] == 1
    b3 = crosscheck("x", {}, [Engine("a", "L1", const(1.0)), Engine("b", "L2", const(1.0)), Engine("c", "L3", boom)], 1e-3, "u")
    assert b3["verdict"] == DEGRADED


def test_published_reference_can_overturn_agreement():
    eng = [Engine("a", "L1", const(2.0)), Engine("b", "L2", const(2.0))]
    b = crosscheck("x", {}, eng, 1e-3, "u", reference={"value": 3.0, "source": "paper"})
    assert b["verdict"] == DISAGREE and not b["reference"]["within_tol"]


def test_vector_norm_mode():
    b = crosscheck("r", {}, [Engine("a", "L1", const([3.0, 0, 0])), Engine("b", "L2", const([0.0, 4.0, 0]))], 4.9, "km", "norm")
    assert b["verdict"] == DISAGREE and abs(b["pairs"][0]["diff"] - 5.0) < 1e-12


def test_isolated_engine_runs_in_other_python_and_bundle_hash_is_stable():
    code = "VERSION='iso-1'\ndef compute(inputs):\n    return inputs['x'] * 2\n"
    e1 = Engine("iso", "L1", python=sys.executable, code=code)
    e2 = Engine("inproc", "L2", lambda i: i["x"] * 2.0)
    b1 = crosscheck("y", {"x": 21}, [e1, e2], 1e-12, "u")
    b2 = crosscheck("y", {"x": 21}, [e1, e2], 1e-12, "u")
    assert b1["verdict"] == AGREE and b1["engines"][0]["version"] == "iso-1"
    assert b1["sha256"] == b2["sha256"]                 # same inputs and results -> same evidence hash


def test_reference_has_its_own_precision():
    eng = [Engine("a", "L1", const(2.00004)), Engine("b", "L2", const(2.00004))]
    loose = crosscheck("x", {}, eng, 1e-9, "u", reference={"value": 2.0, "source": "printed to 4 dp", "tolerance": 5e-4})
    strict = crosscheck("x", {}, eng, 1e-9, "u", reference={"value": 2.0, "source": "printed to 4 dp"})
    assert loose["verdict"] == "AGREE" and strict["verdict"] == "DISAGREE"


def test_hash_is_independent_of_environment():
    from star_crosscheck import bundle_sha256
    b = crosscheck("x", {}, [Engine("a", "L1", const(1.0)), Engine("b", "L2", const(1.0))], 1e-9, "u")
    other = dict(b, environment={"python": "3.99", "platform": "another-machine"})
    assert bundle_sha256(other) == b["sha256"]
    changed = json.loads(json.dumps(b)); changed["engines"][0]["value"] = [2.0]
    assert bundle_sha256(changed) != b["sha256"]
