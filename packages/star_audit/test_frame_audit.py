"""The frame auditor must itself be right: drivers here are synthetic (rotation-free identities plus known defects), so
validation, pairwise envelopes, refusals and the runner's name hygiene are checked against values known by construction.
Verifies: R6 (README).
"""
import math
import sys

import pytest

from frame_audit import VALLADO_GCRF, VALLADO_TEME, VALLADO_UTC, audit, default_cases

CMD = [sys.executable, "-c"]
# exact: returns Vallado's GCRF for the Vallado case and the input vector otherwise
EXACT = ("V = " + repr(VALLADO_GCRF) + "\nT = " + repr(VALLADO_UTC) + "\n"
         "def teme_to_gcrs(utc, r):\n    return list(V) if utc == T else list(r)\n")


def shifted(dx_km, from_year=0):
    return EXACT + (f"_f = teme_to_gcrs\ndef teme_to_gcrs(utc, r):\n    p = _f(utc, r)\n"
                    f"    if int(utc[:4]) >= {from_year}: p[0] += {dx_km}\n    return p\n")


def impl(driver, lineage="x"):
    return {"command": CMD, "driver": driver, "lineage": lineage}


def test_default_cases_layout():
    c = default_cases()
    assert c[0] == [VALLADO_UTC, VALLADO_TEME] and len(c) == 1 + 15 * 3
    assert c[1][0].startswith("1980") and c[-1][0].startswith("2050")


def test_validation_threshold_is_one_metre():
    a = audit({"good": impl(EXACT), "near": impl(shifted(0.0009)), "far": impl(shifted(0.0011))})
    v = a["validation"]
    assert v["good"] == {"error_m": 0.0, "valid": True}
    assert v["near"]["valid"] and abs(v["near"]["error_m"] - 0.9) < 1e-6
    assert not v["far"]["valid"] and abs(v["far"]["error_m"] - 1.1) < 1e-6


def test_pair_envelope_and_by_year_are_exact():
    a = audit({"a": impl(EXACT, "L1"), "b": impl(shifted(0.005, from_year=2030), "L2"), "c": impl(EXACT, "L1")})
    p = a["pairs"]["a|b"]
    assert abs(p["max_m"] - 5.0) < 1e-6 and p["n"] == 45 and not p["same_lineage"]
    assert p["max_m_by_year"]["2025"] == 0.0 and abs(p["max_m_by_year"]["2030"] - 5.0) < 1e-6
    assert a["pairs"]["a|c"]["max_m"] == 0.0 and a["pairs"]["a|c"]["same_lineage"]
    assert list(a["pairs"]) == ["a|b", "a|c", "b|c"]


def test_refusals_are_listed_and_excluded_from_pairs():
    refuse = EXACT + "_g = teme_to_gcrs\ndef teme_to_gcrs(utc, r):\n    if utc.startswith('1980'): raise ValueError('no EOP')\n    return _g(utc, r)\n"
    a = audit({"a": impl(EXACT), "r": impl(refuse)})
    assert a["refused"]["r"] == ["1980-06-15T12:00:00"] * 3 and a["refused"]["a"] == []
    assert a["pairs"]["a|r"]["n"] == 42


def test_refusal_on_the_validation_case_is_not_valid():
    a = audit({"r": impl("def teme_to_gcrs(utc, r):\n    raise RuntimeError('boom')\n")})
    assert a["validation"]["r"]["valid"] is False and "RuntimeError: boom" in a["validation"]["r"]["why"]
    assert a["pairs"] == {}


def test_driver_globals_are_not_shadowed_by_the_runner():
    # a driver that relies on a global named u (as 'import astropy.units as u' does) must keep it
    d = "u = 1000.0\n" + EXACT + "_h = teme_to_gcrs\ndef teme_to_gcrs(utc, r):\n    assert u == 1000.0\n    return _h(utc, r)\n"
    a = audit({"u": impl(d)})
    assert a["validation"]["u"]["valid"] and a["refused"]["u"] == []


def test_noise_and_failures():
    a = audit({"n": impl("print('banner')\n" + EXACT)})
    assert a["validation"]["n"]["valid"]
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"x": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")})
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]


def test_vallado_reference_is_consistent_with_a_pure_rotation():
    # TEME -> GCRF is a rotation: the published pair must have equal norms (guards against a typo in the constants)
    assert abs(math.dist(VALLADO_TEME, [0, 0, 0]) - math.dist(VALLADO_GCRF, [0, 0, 0])) < 1e-6


def test_default_vectors_are_pinned():
    # LEO (Vallado), a second LEO in another octant, and GEO on the x axis: the envelope depends on the radius
    c = default_cases()
    assert [v for _, v in c[1:4]] == [VALLADO_TEME, [-6045.0, -3490.0, 2500.0], [42164.0, 0.0, 0.0]]
    assert {u[:4] for u, _ in c[1:]} == {str(y) for y in range(1980, 2051, 5)}


def test_validation_threshold_edge():
    a = audit({"edge": impl(shifted(0.0009995))})
    assert a["validation"]["edge"]["valid"] and abs(a["validation"]["edge"]["error_m"] - 0.9995) < 1e-6
