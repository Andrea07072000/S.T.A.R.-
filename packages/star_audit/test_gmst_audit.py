"""The GMST auditor must itself be right: synthetic implementations built on the IAU 1982 formula, with KNOWN offsets,
refusals and wrap-around cases, must be validated / excluded / compared exactly as constructed.
Verifies: R9 (README).
"""
import sys

import pytest

from gmst_audit import (VALIDATION_TOL_ARCSEC, VALLADO_GMST_DEG, VALLADO_JD_UT1, arcsec_diff, audit,
                        default_epochs)

CMD = [sys.executable, "-c"]
BASE = ("def _g82(jd):\n    t = (jd - 2451545.0) / 36525.0\n"
        "    s = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t ** 3\n"
        "    return ((s % 86400.0) / 240.0) % 360.0\n")


def impl(extra, lineage="L"):
    return {"command": CMD, "driver": BASE + extra, "lineage": lineage}


def test_constants_wrap_and_epochs():
    assert (VALLADO_JD_UT1, VALLADO_GMST_DEG, VALIDATION_TOL_ARCSEC) == (2448855.009722222, 152.57878781, 0.1)
    assert arcsec_diff(359.9999, 0.0001) == pytest.approx(0.72, abs=1e-9) and arcsec_diff(10.0, 10.0) == 0.0
    assert arcsec_diff(0.0, 1.0) == pytest.approx(3600.0) and arcsec_diff(1.0, 0.0) == pytest.approx(3600.0)
    e = default_epochs()
    assert len(e) == 201 and e[0] == 2433282.5 and e[-1] == 2469807.5 and len(default_epochs(11)) == 11


def test_validation_threshold_and_envelopes():
    off = lambda a: f"def gmst_deg(jd):\n    return _g82(jd) + {a} / 3600.0\n"
    late = "def gmst_deg(jd):\n    return _g82(jd) + (0.05 / 3600.0 if jd > 2451545.0 else 0.0)\n"
    a = audit({"exact": impl(off(0.0), "A"), "near": impl(off(0.09), "B"), "far": impl(off(0.11), "C"),
               "late": impl(late, "A")}, default_epochs(21))
    v = a["validation"]
    assert v["exact"]["valid"] and v["exact"]["vallado_err_arcsec"] < 1e-4
    assert v["near"]["valid"] and not v["far"]["valid"] and a["validated"] == ["exact", "late", "near"]
    p = a["pairs"]["exact|late"]
    assert p["same_lineage"] and p["max_arcsec_by_half_century"]["1950-2000"] < 1e-6
    assert abs(p["max_arcsec_by_half_century"]["2000-2050"] - 0.05) < 1e-6
    assert abs(a["pairs"]["exact|near"]["max_arcsec"] - 0.09) < 1e-6 and a["pairs"]["exact|near"]["n"] == 21


def test_wrap_around_values_compare_as_close():
    near_zero = "def gmst_deg(jd):\n    return 360.0 - 1e-7\n"
    zero = "def gmst_deg(jd):\n    return 0.0\n"
    a = audit({"a": impl(near_zero), "b": impl(zero)}, default_epochs(3))
    assert a["validated"] == []                                     # neither reproduces Vallado
    from gmst_audit import run
    rows = run(CMD, BASE + near_zero, [2451545.0])
    assert 0.0 <= rows[0]["v"] < 360.0 and arcsec_diff(rows[0]["v"], 0.0) < 0.001


def test_refusal_excludes_failure_raises_and_names_are_safe():
    refuse = impl("def gmst_deg(jd):\n    if jd < 2440000: raise ValueError('old')\n    return _g82(jd)\n")
    a = audit({"r": refuse, "x": impl("def gmst_deg(jd):\n    return _g82(jd)\n")}, default_epochs(11))
    assert a["validation"]["r"]["refused"] >= 1 and not a["validation"]["r"]["valid"] and a["pairs"] == {}
    d = impl("jd = 'kept'\nprint('banner')\ndef gmst_deg(x):\n    assert jd == 'kept'\n    return _g82(x)\n")
    assert audit({"d": d}, default_epochs(3))["validation"]["d"]["valid"]
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"f": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")}, default_epochs(3))
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]
