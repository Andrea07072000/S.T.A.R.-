# -*- coding: utf-8 -*-
"""packet_audit — what do CCSDS Space Packet decoders accept? Differential audit (CCSDS 133.0-B), S.T.A.R., 2026-10-05.

Each implementation runs in its own interpreter through a driver defining decode(buffer) -> dict with apid, seq,
ptype, sec, data (hex), for a buffer that should hold EXACTLY one packet, or raising to reject. Reference: the format
rule — 6-octet primary header, version '000', 11-bit APID, 14-bit sequence count, packet data length field = number of
octets in the data field minus 1 (total length = field + 7). Seeded, sha256-pinnable corpus of valid packets (APIDs
across the range, 1..64 data octets, with and without secondary-header flag) and derived kinds, each with the verdict
the rule implies: valid / idle (APID 2047, well formed: accept) · version (version != 0: reject) · truncated (buffer
shorter than the length field says: reject) · trailing (extra octets after the packet: reject, the buffer is not one
packet) · header_only (6 octets, no data field: reject).
Probe validation: an implementation counts only if it accepts every valid packet with exactly the generator's fields.
"""
from __future__ import annotations

import json
import random
import subprocess
from typing import Dict, List

KINDS = ("valid", "idle", "version", "truncated", "trailing", "header_only")
SHOULD_ACCEPT = {"valid": True, "idle": True}
FIELDS = ("apid", "seq", "ptype", "sec", "data")
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __pa_json\n__pa_out = []\nfor __pa_h in payload['cases']:\n"
          "    try:\n        __pa_x = decode(bytes.fromhex(__pa_h))\n"
          "        __pa_out.append({'ok': {__pa_k: __pa_x[__pa_k] for __pa_k in ('apid','seq','ptype','sec','data')}})\n"
          "    except Exception as __pa_e:\n        __pa_out.append({'error': type(__pa_e).__name__ + ': ' + str(__pa_e)[:80]})\n"
          "print(__pa_json.dumps(__pa_out))\n")


def packet(apid: int, seq: int, ptype: int, sec: int, data: bytes, version: int = 0) -> bytes:
    w1 = (version << 13) | (ptype << 12) | (sec << 11) | apid
    w2 = (3 << 14) | seq
    n = len(data) - 1
    return bytes([w1 >> 8, w1 & 0xFF, w2 >> 8, w2 & 0xFF, n >> 8, n & 0xFF]) + data


def corpus(seed: int = 20261005, n: int = 40) -> List[Dict]:
    rng = random.Random(seed)
    out = []
    for k in range(n):
        apid, seq, ptype, sec = rng.randrange(2047), rng.randrange(16384), rng.randrange(2), rng.randrange(2)
        data = bytes(rng.randrange(256) for _ in range(1 + rng.randrange(64)))
        truth = {"apid": apid, "seq": seq, "ptype": ptype, "sec": sec, "data": data.hex()}
        p = packet(apid, seq, ptype, sec, data)
        out.append({"id": f"{k}:valid", "kind": "valid", "buf": p.hex(), "truth": truth})
        out.append({"id": f"{k}:version", "kind": "version", "buf": packet(apid, seq, ptype, sec, data, 1 + rng.randrange(7)).hex()})
        out.append({"id": f"{k}:truncated", "kind": "truncated", "buf": p[:-1 - rng.randrange(len(data))].hex()})
        out.append({"id": f"{k}:trailing", "kind": "trailing", "buf": (p + bytes(1 + rng.randrange(8))).hex()})
        out.append({"id": f"{k}:header_only", "kind": "header_only", "buf": p[:6].hex()})
        if k % 4 == 0:
            idle = packet(2047, seq, 0, 0, bytes([0xFF]) * (1 + rng.randrange(16)))
            out.append({"id": f"{k}:idle", "kind": "idle", "buf": idle.hex(),
                        "truth": {"apid": 2047, "seq": seq, "ptype": 0, "sec": 0, "data": idle[6:].hex()}})
    return out


def run(command: List[str], driver: str, cases: List[str], env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    res = {n: run(i["command"], i["driver"], [c["buf"] for c in cases], i.get("env")) for n, i in impls.items()}
    per_impl = {}
    for n, rows in res.items():
        acc = {k: 0 for k in KINDS}
        tot = {k: 0 for k in KINDS}
        wrong_fields = []
        for c, x in zip(cases, rows):
            tot[c["kind"]] += 1
            if "ok" in x:
                acc[c["kind"]] += 1
                if "truth" in c and any(x["ok"][f] != c["truth"][f] for f in FIELDS):
                    wrong_fields.append(c["id"])
        validated = acc["valid"] == tot["valid"] and not [w for w in wrong_fields if w.endswith(":valid")]
        errors = {k: (acc[k] if not SHOULD_ACCEPT.get(k) else tot[k] - acc[k]) for k in KINDS}
        per_impl[n] = {"accepted": acc, "total": tot, "validated": validated, "wrong_fields": wrong_fields,
                       "verdict_errors": errors, "lineage": impls[n].get("lineage")}
    return {"cases": len(cases), "kinds": {k: sum(1 for c in cases if c["kind"] == k) for k in KINDS}, "per_impl": per_impl}
