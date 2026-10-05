"""Hostile-implementation contract of the auditors (2026-10-05).
Verifies: R1 (README).

Found by the probe: an implementation that returns NaN (without raising) for every epoch after 2000 was VALIDATED by the
GMST auditor and reported as agreeing with a correct implementation to "0.0 arcsec" - Python's max(0.0, nan) is 0.0,
so the NaN vanished from the envelope. The same aggregation pattern was in the TDB, frame, elements, SGP4 and geodesy
auditors. A non-finite answer is now a refusal (audit_guard.finite_rows) or an infinite error (geodesy envelope)."""
import math
import sys

import gmst_audit
import tdb_audit
from audit_guard import finite_rows
from star_audit import envelope

CMD = [sys.executable, "-c"]
GMST_GOOD = ("def gmst_deg(jd):\n    T = (jd - 2451545.0) / 36525.0\n"
             "    return (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T"
             " - T ** 3 / 38710000.0) % 360.0\n")
GMST_NAN_AFTER_2000 = GMST_GOOD + "_g = gmst_deg\ndef gmst_deg(jd):\n    return float('nan') if jd > 2451545.0 else _g(jd)\n"


def test_finite_rows_turns_nan_inf_and_bool_into_errors():
    rows = [{"v": 1.0}, {"v": math.nan}, {"r": [1.0, math.inf, 0.0]}, {"v": True}, {"r": [1.0, None]}, {"error": "x"}]
    out = finite_rows(rows, ["v", "r"])
    assert [("error" in r) for r in out] == [False, True, True, True, False, True]


def test_finite_rows_keeps_text_payloads_and_bounds_the_message():
    # codes and names are compared by the auditors themselves: a string is not a non-finite number
    assert finite_rows([{"v": "TM-v1"}], ["v"]) == [{"v": "TM-v1"}]
    err = finite_rows([{"r": [math.nan] * 100}], ["r"])[0]["error"]
    assert err.startswith("non-finite value returned for 'r'") and len(err) == 120


def test_gmst_auditor_does_not_validate_a_nan_implementation():
    r = gmst_audit.audit({"good": {"command": CMD, "driver": GMST_GOOD, "lineage": "A"},
                          "nan": {"command": CMD, "driver": GMST_NAN_AFTER_2000, "lineage": "B"}},
                         epochs=[2440000.5, 2451000.5, 2455000.5, 2460000.5])
    assert r["validated"] == ["good"]
    assert r["validation"]["nan"]["refused"] == 2 and r["validation"]["nan"]["valid"] is False
    assert r["pairs"] == {}                  # no agreement can be reported with an implementation that was refused


def test_tdb_auditor_does_not_validate_a_nan_implementation():
    good = "import math\ndef tdb_minus_tt(jd):\n    g = math.radians(357.53 + 0.9856003 * (jd - 2451545.0))\n" \
           "    return 0.001657 * math.sin(g) + 0.000014 * math.sin(2 * g)\n"
    bad = good + "_t = tdb_minus_tt\ndef tdb_minus_tt(jd):\n    return float('nan') if jd > 2451545.0 else _t(jd)\n"
    r = tdb_audit.audit({"good": {"command": CMD, "driver": good, "lineage": "A"},
                         "nan": {"command": CMD, "driver": bad, "lineage": "B"}}, epochs=[2440000.5, 2460000.5])
    assert "nan" not in r["validated"] and r["pairs"] == {}


def test_geodesy_envelope_reports_a_nan_answer_as_infinite_error():
    truth = [(10.0, 20.0, 0.0), (30.0, 40.0, 0.0)]
    env = envelope(truth, [(10.0, 20.0, 0.0), (math.nan, 40.0, 0.0)])
    band = env["bands"]["0.0"]
    assert band["non_finite"] == 1 and math.isinf(band["pos_err_m"])
