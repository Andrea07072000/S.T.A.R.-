"""The leap-second auditor must itself be right: a correct reference driver scores OK on every probe with a truth, a
driver with a KNOWN defect (ignores the leap second) is caught as WRONG exactly where expected, a refusing driver is
REJECTED, and silent extrapolation beyond the table is distinguished from a warned one.
Verifies: R4 (README).
"""
import sys

from leapsec_audit import PROBES, audit

# reference driver: hand-written IERS table (DeltaAT from 1972-07-01 and 2017-01-01 only needed by the probes)
EXACT = (
    "import warnings\n"
    "TABLE = [('1972-01-01', 10), ('1972-07-01', 11), ('1999-01-01', 32), ('2015-07-01', 36), ('2017-01-01', 37)]\n"
    "def dat(day):\n"
    "    v = None\n"
    "    for d, n in TABLE:\n"
    "        if day >= d: v = n\n"
    "    return v\n"
    "def to_tai(s):\n"
    "    import datetime as D\n"
    "    day, t = s.split('T'); hh, mm, ss = t.split(':'); sec = float(ss)\n"
    "    if day > '2030-01-01': warnings.warn('beyond table')\n"
    "    if sec >= 60.0:                       # inside the leap second: next day 00:00:(old DeltaAT + x)\n"
    "        nd = (D.date.fromisoformat(day) + D.timedelta(days=1)).isoformat()\n"
    "        return '%sT00:00:%06.3f' % (nd, dat(day) + sec - 60.0)\n"
    "    base = D.datetime.fromisoformat(day + 'T' + hh + ':' + mm + ':00') + D.timedelta(seconds=sec + dat(day))\n"
    "    return base.strftime('%Y-%m-%dT%H:%M:') + '%06.3f' % (base.second + base.microsecond / 1e6)\n")
IGNORES_LEAP = EXACT.replace("if sec >= 60.0:", "if False:").replace("+ dat(day))", "+ 37)")
REFUSES = "def to_tai(s):\n    raise ValueError('no')\n"


def test_reference_driver_is_ok_on_every_truth_probe():
    a = audit(sys.executable, EXACT)
    truths = sum(1 for _, t in PROBES if t is not None)
    assert a["summary"].get("OK") == truths and a["summary"].get("PAST_TABLE_WARNED") == 1


def test_known_defect_is_caught_as_wrong():
    a = audit(sys.executable, IGNORES_LEAP)
    assert a["summary"].get("WRONG", 0) >= 4                    # every pre-2017 probe and the inside-leap ones
    inside_1972 = next(r for r in a["rows"] if r["utc"].startswith("1972-06-30T23:59:60"))
    assert inside_1972["verdict"] == "WRONG"                   # 23:59:60 handled as a normal minute -> wrong TAI


def test_refusal_and_silent_extrapolation_are_distinguished():
    assert audit(sys.executable, REFUSES)["summary"] == {"REJECTED": len(PROBES)}
    silent = audit(sys.executable, EXACT.replace("warnings.warn('beyond table')", "pass"))
    assert silent["summary"].get("PAST_TABLE_SILENT") == 1


def test_noise_before_the_result_line_is_ignored():
    a = audit(sys.executable, "print('library banner')\n" + EXACT)
    assert a["summary"].get("WRONG", 0) == 0 and a["summary"].get("REJECTED", 0) == 0


def test_failure_message_carries_exactly_the_last_300_chars_of_stderr():
    import pytest
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit(sys.executable, f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")
    assert str(e.value).split("library run failed: ", 1)[1] == msg[-300:]
