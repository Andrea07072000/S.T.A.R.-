"""The SGP4 auditor must itself be right. Fixtures: Vallado SGP4-VER.TLE + tcppver.out (AIAA 2006-6753 companion data)
as shipped with python-sgp4 2.27 (MIT), copied 2026-10-04 (sha256 d246d1d9.., 7a46d8cd..). Drivers here REPLAY the
reference (exact), add a known error, or refuse: the auditor must report 0, the injected error, and the refusal.
Verifies: R5 (README).
"""
import json
import sys
from pathlib import Path

import pytest

from sgp4_audit import audit, load_reference

F = Path(__file__).resolve().parent / "fixtures"
CASES = load_reference(F / "SGP4-VER.TLE", F / "tcppver.out")
REF = {c["case"]: c["ref"] for c in CASES}
CMD = [sys.executable, "-c"]


def replay(offset_km=0.0, refuse=()):
    return ("import json\nREF = " + json.dumps({str(k): v for k, v in REF.items()}) + "\n"
            "KEYS = " + json.dumps([[c["line1"], len(c["epochs"])] for c in CASES]) + "\n"
            "def propagate(l1, l2, ts):\n    n = str(KEYS.index([l1, len(ts)]))\n"
            f"    if int(l1[2:7]) in {tuple(refuse)!r}: raise NotImplementedError('refused')\n"
            f"    return [[p[0] + {offset_km}, p[1], p[2]] for p in REF[n]]\n")


def test_reference_loaded():
    assert len(CASES) == 33 and sum(len(c["epochs"]) for c in CASES) == 667
    assert all(len(c["epochs"]) == len(c["ref"]) for c in CASES)


def test_exact_replay_scores_zero():
    a = audit(CMD, replay(), CASES)
    assert a["max_err_km"] == 0.0 and a["audited"] == 33 and a["refused"] == []


def test_injected_offset_is_measured():
    a = audit(CMD, replay(offset_km=0.25), CASES)
    assert abs(a["max_err_km"] - 0.25) < 1e-12 and abs(a["median_err_km"] - 0.25) < 1e-12


def test_refusals_are_listed_not_scored():
    a = audit(CMD, replay(refuse=(5, 20413)), CASES)
    assert {r["satnum"] for r in a["refused"]} == {5, 20413} and a["audited"] == 30   # 20413 appears twice


def test_failed_run_raises():
    with pytest.raises(RuntimeError):
        audit(CMD, "raise SystemExit(3)\n", CASES)


TWO = CASES[:2]


def driver(body):
    return "def propagate(l1, l2, ts):\n" + body


def test_aggregates_distinguish_max_median_worst_and_missing():
    # case 0: errors 1 km and None; case 1: errors 3 km -> worst is case 1, missing counted per case
    d = driver("    import json\n    n = len(ts)\n"
               f"    ref = {json.dumps([c['ref'] for c in TWO])}\n"
               "    k = 0 if l1 == " + repr(TWO[0]["line1"]) + " else 1\n"
               "    off = 1.0 if k == 0 else 3.0\n"
               "    out = [[p[0] + off, p[1], p[2]] for p in ref[k]]\n"
               "    if k == 0: out[0] = None\n"
               "    return out\n")
    a = audit(CMD, d, TWO)
    assert a["worst_sat"] == f"1:{TWO[1]['satnum']}" and abs(a["max_err_km"] - 3.0) < 1e-9
    assert a["per_sat"][f"0:{TWO[0]['satnum']}"]["missing"] == 1
    assert a["per_sat"][f"1:{TWO[1]['satnum']}"]["missing"] == 0
    n0, n1 = len(TWO[0]["epochs"]), len(TWO[1]["epochs"])
    assert a["per_sat"][f"0:{TWO[0]['satnum']}"]["n"] == n0 - 1
    errs = sorted([1.0] * (n0 - 1) + [3.0] * n1)
    import statistics
    assert abs(a["median_err_km"] - statistics.median(errs)) < 1e-9


def test_only_the_last_stdout_line_is_the_result():
    d = "print('noise from the implementation')\n" + driver("    raise NotImplementedError('x')\n")
    a = audit(CMD, d, TWO)
    assert len(a["refused"]) == 2 and a["audited"] == 0 and a["max_err_km"] is None and a["worst_sat"] is None


def test_failure_message_carries_exactly_the_last_300_chars_of_stderr():
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit(CMD, f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n", TWO)
    tail = str(e.value).split("implementation run failed: ", 1)[1]
    assert tail == msg[-300:]
