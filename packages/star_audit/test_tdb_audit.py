"""The TDB auditor must itself be right: synthetic implementations built on the published low-precision formula, with
KNOWN offsets, refusals and failures, must be validated / excluded / compared exactly as constructed.
Verifies: R8 (README).
"""
import math
import sys

import pytest

from tdb_audit import VALIDATION_TOL_S, audit, default_epochs, low_precision

CMD = [sys.executable, "-c"]
BASE = ("import math\ndef _lp(jd):\n    g = math.radians(357.53 + 0.9856003 * (jd - 2451545.0))\n"
        "    return 0.001657 * math.sin(g) + 0.000014 * math.sin(2.0 * g)\n")


def impl(extra, lineage="L"):
    return {"command": CMD, "driver": BASE + extra, "lineage": lineage}


def test_published_formula_and_epochs():
    assert low_precision(2451545.0) == pytest.approx(0.001657 * math.sin(math.radians(357.53))
                                                     + 0.000014 * math.sin(math.radians(2 * 357.53)), abs=1e-18)
    e = default_epochs()
    assert len(e) == 401 and e[0] == 2415020.5 and e[-1] == 2488069.5 and 2451545.0 in e and e == sorted(e)
    assert VALIDATION_TOL_S == 50e-6


def test_validation_threshold_and_pair_envelopes():
    a = audit({"exact": impl("def tdb_minus_tt(jd):\n    return _lp(jd)\n", "A"),
               "near": impl("def tdb_minus_tt(jd):\n    return _lp(jd) + 49e-6\n", "B"),
               "far": impl("def tdb_minus_tt(jd):\n    return _lp(jd) + 51e-6\n", "C"),
               "late": impl("def tdb_minus_tt(jd):\n    return _lp(jd) + (10e-6 if jd > 2451545.0 else 0.0)\n", "A")},
              default_epochs(41))
    v = a["validation"]
    assert v["exact"]["max_dev_from_published_s"] == 0.0 and v["exact"]["valid"]
    assert v["near"]["valid"] and abs(v["near"]["max_dev_from_published_s"] - 49e-6) < 1e-12
    assert not v["far"]["valid"] and "far" not in a["validated"] and a["validated"] == ["exact", "late", "near"]
    p = a["pairs"]["exact|late"]
    assert p["same_lineage"] and p["max_s_by_century"]["19xx"] == 0.0 and abs(p["max_s_by_century"]["20xx"] - 10e-6) < 1e-12
    assert abs(a["pairs"]["exact|near"]["max_s"] - 49e-6) < 1e-12 and not a["pairs"]["exact|near"]["same_lineage"]
    assert a["epochs"] == 41 and a["pairs"]["exact|near"]["n"] == 41   # J2000 is a grid point


def test_refusal_excludes_and_failure_raises():
    refuse = impl("def tdb_minus_tt(jd):\n    if jd < 2420000: raise ValueError('out of range')\n    return _lp(jd)\n")
    a = audit({"r": refuse, "x": impl("def tdb_minus_tt(jd):\n    return _lp(jd)\n")}, default_epochs(21))
    assert a["validation"]["r"]["refused"] >= 1 and not a["validation"]["r"]["valid"] and a["pairs"] == {}
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"f": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")}, default_epochs(5))
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]


def test_runner_names_do_not_shadow_driver_globals_and_noise_is_ignored():
    d = impl("jd = 'kept'\nprint('banner')\ndef tdb_minus_tt(x):\n    assert jd == 'kept'\n    return _lp(x)\n")
    assert audit({"d": d}, default_epochs(5))["validation"]["d"]["valid"]
