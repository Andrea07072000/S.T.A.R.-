"""The Space Packet auditor must itself be right: its corpus must carry exactly the defect each kind names (checked with
the CCSDS 133.0-B rule written here independently) and synthetic decoders (strict, lenient on length, lenient on version,
misreading) must be scored exactly as constructed.
Verifies: R12 (README).
"""
import sys

import pytest

from corpus_fingerprint import fingerprint
from packet_audit import KINDS, SHOULD_ACCEPT, audit, corpus, packet

CMD = [sys.executable, "-c"]
STRICT = '''
def decode(b):
    if len(b) < 7:
        raise ValueError("short")
    if b[0] >> 5:
        raise ValueError("version")
    if len(b) != ((b[4] << 8) | b[5]) + 7:
        raise ValueError("length")
    return {"apid": ((b[0] & 7) << 8) | b[1], "seq": ((b[2] << 8) | b[3]) & 0x3FFF, "ptype": (b[0] >> 4) & 1,
            "sec": (b[0] >> 3) & 1, "data": bytes(b[6:]).hex()}
'''
NO_VERSION = STRICT.replace('    if b[0] >> 5:\n        raise ValueError("version")\n', "")
NO_LENGTH = STRICT.replace('    if len(b) != ((b[4] << 8) | b[5]) + 7:\n        raise ValueError("length")\n', "")
MISREAD = STRICT.replace('"apid": ((b[0] & 7) << 8) | b[1]', '"apid": b[1]')


def impl(code):
    return {"command": CMD, "driver": code, "lineage": "synthetic"}


def rule_ok(b):
    return len(b) >= 7 and (b[0] >> 5) == 0 and len(b) == ((b[4] << 8) | b[5]) + 7


def test_packet_builder_matches_the_standard_layout():
    p = packet(0x5A3, 0x1234, 1, 1, b"\x01\x02\x03")
    assert p == bytes([0x1D, 0xA3, 0xD2, 0x34, 0x00, 0x02, 1, 2, 3])
    assert packet(0, 0, 0, 0, b"\x00", version=7)[0] >> 5 == 7


def test_corpus_carries_exactly_the_named_defects_and_is_pinned():
    c = corpus()
    assert c == corpus() and {x["kind"] for x in c} == set(KINDS)
    for x in c:
        assert rule_ok(bytes.fromhex(x["buf"])) == SHOULD_ACCEPT.get(x["kind"], False), x["id"]
    assert sum(1 for x in c if x["kind"] == "valid") == 40 and sum(1 for x in c if x["kind"] == "idle") == 10
    assert fingerprint(c) == fingerprint(corpus(20261005, 40)) and fingerprint(c) != fingerprint(corpus(1))
    assert fingerprint(c) == "cb1b960d9413eaf325a44f8c10a825db8516b1539ac785f52cda5edf64ab0864"


def test_strict_decoder_has_zero_verdict_errors():
    s = audit({"strict": impl(STRICT)})["per_impl"]["strict"]
    assert s["validated"] and all(v == 0 for v in s["verdict_errors"].values()) and s["wrong_fields"] == []


def test_lenient_and_misreading_decoders_are_scored_exactly():
    a = audit({"nov": impl(NO_VERSION), "nol": impl(NO_LENGTH), "mis": impl(MISREAD)})["per_impl"]
    assert a["nov"]["validated"] and a["nov"]["verdict_errors"]["version"] == 40
    assert a["nov"]["verdict_errors"]["truncated"] == 0
    long_enough = sum(1 for x in corpus() if x["kind"] == "truncated" and len(bytes.fromhex(x["buf"])) >= 7)
    assert a["nol"]["verdict_errors"]["trailing"] == 40 and a["nol"]["verdict_errors"]["truncated"] == long_enough < 40
    assert a["nol"]["verdict_errors"]["header_only"] == 0                        # still rejected: shorter than 7
    assert not a["mis"]["validated"] and len(a["mis"]["wrong_fields"]) >= 1


def test_failures():
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"f": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")})
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]
