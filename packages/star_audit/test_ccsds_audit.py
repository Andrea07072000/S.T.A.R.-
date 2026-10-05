"""The CCSDS auditor must itself be right: a reference decoder written here from CCSDS 132.0-B must validate and reject
exactly the corrupted frames with a bad FECF; decoders with KNOWN defects (accept everything, master count read as VC
count, OCF left in the data, a driver that raises) must be caught exactly where expected.
Verifies: R7 (README).
"""
import sys

from ccsds_audit import FIELDS, audit, corpus, crc16, tm_frame

CMD = [sys.executable, "-c"]
REF = '''
def crc16(b):
    c = 0xFFFF
    for x in b:
        c ^= x << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c
def decode(f):
    if crc16(f[:-2]) != (f[-2] << 8 | f[-1]):
        raise ValueError("FECF")
    w1 = f[0] << 8 | f[1]; st = f[4] << 8 | f[5]
    hdr = 6 + ((f[6] & 0x3F) + 1 if st & 0x8000 else 0)
    ocf = f[-6:-2].hex() if w1 & 1 else None
    end = len(f) - 2 - (4 if w1 & 1 else 0)
    return {"crc_ok": True, "scid": (w1 >> 4) & 0x3FF, "vcid": (w1 >> 1) & 7, "mc": f[2], "vc": f[3],
            "fhp": st & 0x7FF, "ocf": ocf, "data": f[hdr:end].hex()}
'''
ACCEPT_ALL = REF.replace('raise ValueError("FECF")', "pass")
MC_AS_VC = REF.replace('"vc": f[3]', '"vc": f[2]')
OCF_IN_DATA = REF.replace("end = len(f) - 2 - (4 if w1 & 1 else 0)", "end = len(f) - 2")
FLAG_ONLY = REF.replace('raise ValueError("FECF")', "return {'crc_ok': False}")
BROKEN = REF.replace("w1 = f[0] << 8 | f[1]", "w1 = f.missing_attribute")


def impl(d):
    return {"command": CMD, "driver": d}


CASES = corpus(n_valid=12, n_corrupt=60)


def test_generator_frames_carry_a_correct_fecf_and_header():
    f, t = tm_frame(0x2A5, 5, 200, 17, 0x123, b"\x01\x02", ocf=b"\xaa\xbb\xcc\xdd", sec=b"\x00\x11\x22")
    assert crc16(f[:-2]) == (f[-2] << 8 | f[-1]) and crc16(f) == 0 and len(f) == 64
    assert f[2] == 200 and f[3] == 17 and (f[4] << 8 | f[5]) & 0x7FF == 0x123 and f[6] == 2 and f[-6:-2] == b"\xaa\xbb\xcc\xdd"
    assert t["data"] == f[9:-6].hex() and set(t) == set(FIELDS)


def test_corpus_is_deterministic_and_balanced():
    a, b = corpus(n_valid=12, n_corrupt=60), corpus(n_valid=12, n_corrupt=60)
    assert a == b and sum(c["truth"] is not None for c in a) == 12 and {c["flips"] for c in a[12:]} == {1, 2, 3, 4}
    assert any(c["truth"] and c["truth"]["ocf"] for c in a) and any(c["truth"] and not c["truth"]["ocf"] for c in a)


def test_reference_decoder_validates_and_rejects_exactly_the_bad_fecf():
    s = audit({"ref": impl(REF)}, CASES)["per_impl"]["ref"]
    bad_fecf = sum(1 for c in CASES[12:] if not c["crc_ok"])
    assert s["validated"] and s["valid_exact"] == 12 and s["corrupt_rejected"] == bad_fecf
    assert s["corrupt_accepted_crc_bad"] == [] and s["corrupt_crc_collision_accepted"] == 60 - bad_fecf


def test_defects_are_caught_where_expected():
    a = audit({"ref": impl(REF), "all": impl(ACCEPT_ALL), "mc": impl(MC_AS_VC), "ocf": impl(OCF_IN_DATA),
               "flag": impl(FLAG_ONLY), "broken": impl(BROKEN)}, CASES)
    p = a["per_impl"]
    assert len(p["all"]["corrupt_accepted_crc_bad"]) == sum(1 for c in CASES[12:] if not c["crc_ok"])
    assert p["mc"]["valid_exact"] < 12 and all(w["fields"] == ["vc"] for w in p["mc"]["valid_wrong_fields"])
    ocf_cases = sum(1 for c in CASES[:12] if c["truth"]["ocf"])
    assert len(p["ocf"]["valid_wrong_fields"]) == ocf_cases and not p["ocf"]["validated"]
    assert p["flag"]["validated"] and p["flag"]["corrupt_rejected"] == p["ref"]["corrupt_rejected"]   # flag == reject
    assert not p["broken"]["validated"] and len(p["broken"]["valid_rejected"]) == 12
    # only validated implementations take part in the acceptance comparison
    assert all(set(d["accepts"]) == {"all", "flag", "ref"} for d in a["accept_disagreements"])
    assert {d["id"] for d in a["accept_disagreements"]} == {c["id"] for c in CASES[12:] if not c["crc_ok"]}


def test_default_corpus_is_pinned_by_fingerprint():
    # the corpus is part of the published evidence: any change of seed, counts, length, ranges or flips must show
    import hashlib
    import json
    c = corpus()
    assert len(c) == 300 and sum(x["truth"] is not None for x in c) == 40 and all(len(x["frame"]) == 128 for x in c)
    assert hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest() == \
        "b29d86b8b9750b82ae89b80c450e42f24fc9e736412ccc313671f75b0965bd38"


def test_single_octet_secondary_header_and_standard_status_bits():
    f, t = tm_frame(1, 2, 3, 4, 5, b"\x77" * 60, sec=b"\x00")
    st = f[4] << 8 | f[5]
    assert st & 0x8000 and (st & 0x7800) == 0x1800 and f[6] == 0 and t["data"].startswith("77") and len(t["data"]) == 2 * (64 - 7 - 2)
    f2, _ = tm_frame(1, 2, 3, 4, 5, b"")
    assert (f2[4] << 8 | f2[5]) == 0x1805


def test_crc_collision_and_missing_crc_key_are_accepts():
    # a 'corrupted' frame whose FECF was recomputed is a CRC collision from the decoder's point of view
    f, t = tm_frame(9, 1, 2, 3, 4, b"\x10" * 50)
    g = bytearray(f[:-2])
    g[10] ^= 0xFF
    g += bytes([crc16(bytes(g)) >> 8, crc16(bytes(g)) & 0xFF])
    cases = [{"id": "v0", "frame": f.hex(), "truth": t, "flips": 0},
             {"id": "c0", "frame": bytes(g).hex(), "truth": None, "flips": 8, "crc_ok": True}]
    no_key = REF.replace('return {"crc_ok": True, ', "return {")
    s = audit({"ref": impl(REF), "nokey": impl(no_key)}, cases)["per_impl"]
    assert s["ref"]["corrupt_crc_collision_accepted"] == 1 and s["ref"]["corrupt_rejected"] == 0
    assert s["nokey"]["corrupt_crc_collision_accepted"] == 1 and s["nokey"]["valid_wrong_fields"][0]["fields"] == ["crc_ok"]


def test_failed_run_carries_last_300_chars_of_stderr():
    import pytest
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"x": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")}, CASES[:2])
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]
