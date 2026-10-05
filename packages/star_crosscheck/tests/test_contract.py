"""Contract of crosscheck(), from a probe with hostile configurations (2026-10-05).
Verifies: R1, R2, R3, R4, R5 (README).

Found by the probe, each one a FALSE AGREE (the worst output a cross-check can give): an infinite tolerance agreed on
1 vs 1e9; 'ERFA'/'erfa' and 'SOFA'/'SOFA ' were counted as two independent lineages; an empty lineage counted as a
witness; a misspelt diff_mode silently fell back to max_abs; an infinite reference tolerance hid a wrong published
value. Also: str/bool results were accepted as numbers and an empty vector crashed crosscheck()."""
import math

import pytest

from star_crosscheck import AGREE, DEGRADED, DISAGREE, INSUFFICIENT, Engine, bundle_sha256, crosscheck


def E(name, lineage, value):
    return Engine(name=name, lineage=lineage, func=lambda inputs, v=value: v)


def run(engines, tol=1e-9, **kw):
    return crosscheck("q", {"x": 1}, engines, tol, "m", **kw)


@pytest.mark.parametrize("kw", [dict(tol=math.inf), dict(tol=math.nan), dict(tol=-1.0), dict(tol=True),
                                dict(diff_mode="nrom"), dict(reference={"value": 5.0, "tolerance": math.inf}),
                                dict(reference={"value": 5.0, "tolerance": -1.0})])
def test_invalid_configuration_is_refused(kw):
    tol = kw.pop("tol", 1e-9)
    with pytest.raises(ValueError):
        run([E("a", "A", 1.0), E("b", "B", 1.0)], tol=tol, **kw)


def test_empty_lineage_is_refused():
    with pytest.raises(ValueError):
        run([E("a", "", 1.0), E("b", "B", 1.0)])


@pytest.mark.parametrize("l1,l2", [("ERFA", "erfa"), ("SOFA", "SOFA "), ("Vallado  2013", "vallado 2013")])
def test_spelling_variants_are_one_lineage(l1, l2):
    b = run([E("a", l1, 1.0), E("b", l2, 1.0)])
    assert b["verdict"] == INSUFFICIENT and len(b["independent_lineages"]) == 1


@pytest.mark.parametrize("bad", ["1.0", True, None, [], [1.0, math.nan], math.inf, math.nan])
def test_non_numeric_or_empty_result_is_a_failed_engine_never_agreement(bad):
    b = run([E("a", "A", 1.0), E("b", "B", 1.0), E("c", "C", bad)])
    assert b["verdict"] == DEGRADED
    assert [r["state"] for r in b["engines"]] == ["OK", "OK", "FAILED"]


def test_norm_mode_really_uses_the_norm():
    # max_abs = 1.0 <= 1.2 but norm = 1.414 > 1.2: the requested mode decides
    assert run([E("a", "A", [1.0, 0.0]), E("b", "B", [0.0, 1.0])], tol=1.2, diff_mode="norm")["verdict"] == DISAGREE
    assert run([E("a", "A", [1.0, 0.0]), E("b", "B", [0.0, 1.0])], tol=1.2, diff_mode="max_abs")["verdict"] == AGREE


def test_reference_disagreement_and_bundle_hash():
    b = run([E("a", "A", 1.0), E("b", "B", 1.0)], reference={"value": 2.0, "source": "printed", "tolerance": 0.5})
    assert b["verdict"] == DISAGREE and b["reference"]["within_tol"] is False
    assert b["sha256"] == bundle_sha256(b)
    b["engines"][0]["value"] = [1.5]
    assert bundle_sha256(b) != b["sha256"]          # tamper-evident
