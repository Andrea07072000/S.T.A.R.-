"""Hostile-implementation contract, second round (2026-10-06): what a driver PRINTS is checked before it is counted.
Verifies: R11, R16 (README).

Found by the probe: the TLE auditor VALIDATED a reader that (a) returned a NaN inclination, (b) returned a wrong
catalogue number, (c) answered only 1 case out of 203 (zip() stopped at the shorter list). An empty or non-JSON output
surfaced as IndexError / JSONDecodeError / TypeError, and a CCSDS decoder returning a list crashed the audit with
AttributeError. Every auditor now takes its rows through audit_guard.driver_rows."""
import sys

import pytest

import ccsds_audit
import leapsec_audit
import packet_audit
import tle_audit
from audit_guard import driver_rows

CMD = [sys.executable, "-c"]
TLE_GOOD = "def ingest(a, b):\n    return {'satnum': int(a[2:7]), 'inc': float(b[8:16])}\n"


@pytest.mark.parametrize("stdout", ["", "   \n", "not json", "[1, 2", "{}", "5", "null", '"text"', '[{"a": 1}]\nbye'])
def test_driver_rows_refuses_an_output_without_a_result_list(stdout):
    with pytest.raises(RuntimeError, match=r"printed no result list \(2 cases\)"):
        driver_rows(stdout, 2)


@pytest.mark.parametrize("stdout", ["[]", '[{"a": 1}]', '[{"a": 1}, {"b": 2}, {"c": 3}]', '[{"a": 1}, 5]', '[{"a": 1}, null]',
                                    '[{"a": 1}, [1]]'])
def test_driver_rows_refuses_anything_but_one_object_per_case(stdout):
    with pytest.raises(RuntimeError, match=r"did not return one dict per case \(\d rows, 2 cases\)"):
        driver_rows(stdout, 2)


def test_driver_rows_returns_the_rows_of_the_last_line():
    assert driver_rows('warning: x\n[{"a": 1}, {"error": "e"}]\n', 2) == [{"a": 1}, {"error": "e"}]
    assert driver_rows("[]", 0) == [] and driver_rows("[[1.0, 2.0]]", 1, row=list) == [[1.0, 2.0]]
    with pytest.raises(RuntimeError, match="one list per case"):
        driver_rows('[{"a": 1}]', 1, row=list)


def tle(driver):
    return tle_audit.audit({"x": {"command": CMD, "driver": driver}})["per_impl"]["x"]


def test_tle_reader_is_validated_only_when_it_reads_what_is_printed():
    good = tle(TLE_GOOD)
    assert good["validated"] is True and good["valid_misread"] == [] and good["accepted"]["valid"] == good["total"]["valid"] == 29
    for bad in ("def ingest(a, b):\n    return {'satnum': int(a[2:7]), 'inc': float('nan')}\n",
                "def ingest(a, b):\n    return {'satnum': int(a[2:7]), 'inc': float('inf')}\n",
                "def ingest(a, b):\n    return {'satnum': int(a[2:7]) + 1, 'inc': float(b[8:16])}\n",
                "def ingest(a, b):\n    return {'satnum': int(a[2:7]), 'inc': float(b[8:16]) + 0.00011}\n"):
        r = tle(bad)
        assert r["validated"] is False and len(r["valid_misread"]) == 29, bad
    assert tle("def ingest(a, b):\n    return {'satnum': int(a[2:7]), 'inc': float(b[8:16]) + 0.00009}\n")["validated"] is True


def test_read_ok_checks_types_and_both_fields():
    case = {"l1": "1 25544U", "l2": "2 25544  51.6416"}
    assert tle_audit._read_ok({"satnum": 25544, "inc": 51.6416}, case) and tle_audit._read_ok({"satnum": 25544, "inc": 51.64169}, case)
    for got in ({"satnum": 25544}, {"inc": 51.6416}, {"satnum": True, "inc": 51.6416}, {"satnum": 25544, "inc": True},
                {"satnum": "25544", "inc": 51.6416}, {"satnum": 25544.0, "inc": 51.6416}, {"satnum": 25544, "inc": "51.6416"},
                {"satnum": 25545, "inc": 51.6416}, {"satnum": 25544, "inc": 51.6418}, {"satnum": 25544, "inc": float("nan")},
                None, [25544, 51.6416]):
        assert not tle_audit._read_ok(got, case), got


TRUNCATE = "payload['{key}'] = payload['{key}'][:1]\n"


@pytest.mark.parametrize("module, key, body", [
    (tle_audit, "cases", TLE_GOOD), (packet_audit, "cases", "def decode(b):\n    raise ValueError('x')\n"),
    (ccsds_audit, "frames", "def decode(b):\n    raise ValueError('x')\n")])
def test_an_implementation_that_answers_fewer_cases_is_a_failed_run(module, key, body):
    with pytest.raises(RuntimeError, match=r"\(1 rows, \d+ cases\)"):
        module.audit({"x": {"command": CMD, "driver": TRUNCATE.format(key=key) + body}})


def test_an_implementation_that_prints_nothing_or_junk_is_a_failed_run():
    with pytest.raises(RuntimeError, match="printed no result list"):
        tle_audit.audit({"x": {"command": CMD, "driver": TLE_GOOD + "print = lambda *a: None\n"}})
    with pytest.raises(RuntimeError, match="one dict per case"):
        packet_audit.audit({"x": {"command": CMD, "driver": "import json\nprint(json.dumps([1] * 5))\nraise SystemExit(0)\n"}})
    short = "import json, sys\n_r = sys.stdin.read\nsys.stdin.read = lambda: json.dumps(json.loads(_r())[:1])\ndef to_tai(s):\n    return s\n"
    with pytest.raises(RuntimeError, match=r"\(1 rows, 7 cases\)"):
        leapsec_audit.audit(sys.executable, short)


@pytest.mark.parametrize("ret", ["[1, 2]", "None", "'frame'", "5"])
def test_a_ccsds_decoder_returning_no_object_is_not_an_accepted_frame(ret):
    p = ccsds_audit.audit({"x": {"command": CMD, "driver": f"def decode(b):\n    return {ret}\n"}})["per_impl"]["x"]
    assert p["validated"] is False and p["valid_exact"] == 0 and p["corrupt_rejected"] == 260 and len(p["valid_rejected"]) == 40
    assert ccsds_audit._accepted({"r": {}}) and ccsds_audit._accepted({"r": {"crc_ok": True}})
    assert not ccsds_audit._accepted({"r": {"crc_ok": False}}) and not ccsds_audit._accepted({"error": "x"})
