"""The TLE auditor must itself be right: its corpus must carry exactly the defect each kind names (checked here with
the format rule written independently), and synthetic readers (strict, accept-all, checksum-only, misreading) must be
scored exactly as constructed.
Verifies: R11 (README).
"""
import sys

import pytest

from tle_audit import KINDS, SHOULD_ACCEPT, audit, base_tles, checksum, corpus, well_formed

CMD = [sys.executable, "-c"]
STRICT = '''
def _ck(l):
    return sum(int(c) if c.isdigit() else (1 if c == "-" else 0) for c in l[:68]) % 10
def ingest(a, b):
    if len(a) != 69 or len(b) != 69 or a[0] != "1" or b[0] != "2" or a[2:7] != b[2:7]:
        raise ValueError("format")
    if _ck(a) != int(a[68]) or _ck(b) != int(b[68]):
        raise ValueError("checksum")
    return {"satnum": int(a[2:7]), "inc": float(b[8:16])}
'''
ACCEPT_ALL = "def ingest(a, b):\n    return {'satnum': int(a[2:7]), 'inc': float(b[8:16])}\n"
CHECKSUM_ONLY = STRICT.replace('a[0] != "1" or b[0] != "2" or a[2:7] != b[2:7]', "False")
MISREAD = ACCEPT_ALL.replace("float(b[8:16])", "float(b[8:16]) + 0.001")


def impl(code):
    return {"command": CMD, "driver": code, "lineage": "synthetic"}


def test_checksum_rule_on_a_known_line():
    l1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
    assert checksum(l1) == 3 and int(l1[68]) == 3 and checksum("1" + " " * 67) == 1 and checksum("-" * 68) == 8


def test_corpus_carries_exactly_the_named_defects():
    base = base_tles()
    c = corpus()
    assert len(base) == 29 and c == corpus() and len(c) == 29 * 7
    for x in c:
        wf = well_formed(x["l1"], x["l2"])
        assert wf == SHOULD_ACCEPT.get(x["kind"], False), x["id"]
        if x["kind"] == "checksum":
            assert x["l2"][:68] == base[int(x["id"].split(":")[0])][1][:68]
        if x["kind"] == "truncated":
            assert len(x["l2"]) == 68
    assert {x["kind"] for x in c} == set(KINDS)


def test_strict_reader_has_zero_verdict_errors():
    s = audit({"strict": impl(STRICT)})["per_impl"]["strict"]
    assert s["validated"] and all(v == 0 for v in s["verdict_errors"].values())
    assert s["accepted"] == {"valid": 29, "field_digit": 0, "checksum": 0, "line_number": 0, "satnum_mismatch": 0,
                             "truncated": 0, "resummed": 29}


def test_lenient_readers_are_scored_exactly():
    a = audit({"all": impl(ACCEPT_ALL), "ck": impl(CHECKSUM_ONLY), "mis": impl(MISREAD)})["per_impl"]
    assert a["all"]["validated"] and a["all"]["verdict_errors"] == {"valid": 0, "field_digit": 29, "checksum": 29,
                                                                    "line_number": 29, "satnum_mismatch": 29,
                                                                    "truncated": 29, "resummed": 0}
    assert a["ck"]["verdict_errors"]["line_number"] == 29 and a["ck"]["verdict_errors"]["checksum"] == 0
    assert not a["mis"]["validated"] and len(a["mis"]["valid_misread"]) == 29


def test_failures():
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"f": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")})
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]


def test_corpus_and_base_are_pinned():
    import hashlib
    import json
    assert hashlib.sha256(json.dumps(corpus(), sort_keys=True).encode()).hexdigest() == \
        "df1ee7462f751854d9bcff48e8c901ad8fe8857eb8b1d4c00b9a5a8abb978e97"
    b = base_tles()
    assert b[0][0] == "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
    assert b[-1][1] == "2 88888  72.8435 115.9689 0086731  52.6988 110.5714 16.05824518  1058"
    assert all(len(x) == 69 and len(y) == 69 for x, y in b) and len(set(b)) == len(b)


def test_misread_tolerance_and_validation_logic():
    near = ACCEPT_ALL.replace("float(b[8:16])", "float(b[8:16]) + 0.00005")
    off = ACCEPT_ALL.replace("float(b[8:16])", "float(b[8:16]) + 0.0002")
    picky = ACCEPT_ALL.replace("def ingest(a, b):\n", "def ingest(a, b):\n    if a[2:7] == '00005': raise ValueError('x')\n")
    a = audit({"near": impl(near), "off": impl(off), "picky": impl(picky)})["per_impl"]
    assert a["near"]["validated"] and a["near"]["valid_misread"] == []
    assert not a["off"]["validated"] and len(a["off"]["valid_misread"]) == 29
    assert not a["picky"]["validated"] and a["picky"]["accepted"]["valid"] == 28 and a["picky"]["valid_misread"] == []
    assert a["picky"]["verdict_errors"]["valid"] == 1 and a["picky"]["total"]["valid"] == 29
