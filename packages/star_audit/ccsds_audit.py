# -*- coding: utf-8 -*-
"""ccsds_audit — differential audit of CCSDS TM transfer-frame decoders (CCSDS 132.0-B) on valid and corrupted frames,
S.T.A.R., 2026-10-04.

Corpus (deterministic, seed given): TM frames built from the standard with every header option (OCF on/off, secondary
header of 1..8 octets, VC counts 0..255, FHP values) plus copies with 1..4 bit flips in header, data or FECF. Each
implementation runs in its own interpreter through a driver defining decode(frame_bytes) -> dict with keys
crc_ok, scid, vcid, mc, vc, fhp, ocf (bytes hex or None), data (hex), or raising to reject.
Per frame the audit records: who accepts, who rejects, and field disagreements among accepters. Truth for valid frames
is the generator's own field values (known by construction); for corrupted frames the CRC-16/CCITT recomputation.
"""
from __future__ import annotations

import json
import random
import subprocess
from typing import Dict, List

FIELDS = ("crc_ok", "scid", "vcid", "mc", "vc", "fhp", "ocf", "data")


def crc16(b: bytes) -> int:
    c = 0xFFFF
    for x in b:
        c ^= x << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def tm_frame(scid, vcid, mc, vc, fhp, data, ocf=None, sec=None, length=64):
    """Build a TM frame of `length` octets with FECF; returns (bytes, truth dict)."""
    w1 = (scid << 4) | (vcid << 1) | (1 if ocf is not None else 0)
    status = (0x8000 if sec is not None else 0) | 0x1800 | fhp
    hdr = bytes([w1 >> 8, w1 & 0xFF, mc, vc, status >> 8, status & 0xFF])
    if sec is not None:
        hdr += bytes([len(sec) - 1]) + sec[1:] if len(sec) > 1 else bytes([0])
    room = length - len(hdr) - 2 - (4 if ocf is not None else 0)
    body = data[:room].ljust(room, b"\x55")
    f = hdr + body + (ocf or b"")
    f += bytes([crc16(f) >> 8, crc16(f) & 0xFF])
    return f, {"crc_ok": True, "scid": scid, "vcid": vcid, "mc": mc, "vc": vc, "fhp": fhp,
               "ocf": ocf.hex() if ocf is not None else None, "data": body.hex()}


def corpus(seed: int = 20261004, n_valid: int = 40, n_corrupt: int = 260, length: int = 64) -> List[Dict]:
    rng = random.Random(seed)
    out = []
    for k in range(n_valid):
        sec = None if k % 3 else bytes(rng.randrange(256) for _ in range(1 + k % 8))
        ocf = None if k % 2 else bytes(rng.randrange(256) for _ in range(4))
        f, t = tm_frame(rng.randrange(1024), rng.randrange(8), rng.randrange(256), rng.randrange(256),
                        rng.randrange(2046), bytes(rng.randrange(256) for _ in range(40)), ocf, sec, length)
        out.append({"id": f"v{k}", "frame": f.hex(), "truth": t, "flips": 0})
    for k in range(n_corrupt):
        base = out[k % n_valid]
        b = bytearray(bytes.fromhex(base["frame"]))
        region = k % 3
        lo, hi = {0: (0, 6), 1: (6, length - 2), 2: (length - 2, length)}[region]
        pos = set()
        while len(pos) < 1 + k % 4:
            pos.add((rng.randrange(lo, hi), rng.randrange(8)))
        for i, bit in pos:
            b[i] ^= 1 << bit
        out.append({"id": f"c{k}", "frame": bytes(b).hex(), "truth": None, "flips": len(pos),
                    "crc_ok": crc16(bytes(b[:-2])) == (b[-2] << 8 | b[-1])})
    return out


RUNNER = ("\nimport json as __ca_json\n__ca_out = []\nfor __ca_f in payload['frames']:\n"
          "    try:\n        __ca_out.append({'r': decode(bytes.fromhex(__ca_f))})\n"
          "    except Exception as __ca_e:\n"
          "        __ca_out.append({'error': type(__ca_e).__name__ + ': ' + str(__ca_e)[:80]})\n"
          "print(__ca_json.dumps(__ca_out))\n")
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"


def run(command: List[str], driver: str, frames: List[str], env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "frames": frames}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    res = {n: run(i["command"], i["driver"], [c["frame"] for c in cases], i.get("env")) for n, i in impls.items()}
    per_impl = {}
    for n, rows in res.items():
        s = {"valid_exact": 0, "valid_wrong_fields": [], "valid_rejected": [],
             "corrupt_rejected": 0, "corrupt_accepted_crc_bad": [], "corrupt_crc_collision_accepted": 0}
        for c, x in zip(cases, rows):
            ok = "r" in x and x["r"].get("crc_ok", True)
            if c["truth"] is not None:
                if not ok:
                    s["valid_rejected"].append(c["id"])
                else:
                    bad = [f for f in FIELDS if x["r"].get(f) != c["truth"][f]]
                    if bad:
                        s["valid_wrong_fields"].append({"id": c["id"], "fields": bad})
                    else:
                        s["valid_exact"] += 1
            elif not ok:
                s["corrupt_rejected"] += 1
            elif c["crc_ok"]:
                s["corrupt_crc_collision_accepted"] += 1      # a CRC-16 collision: accepting it is correct behaviour
            else:
                s["corrupt_accepted_crc_bad"].append(c["id"])  # silent acceptance of a frame whose FECF is wrong
        # probe validation: an implementation's rejection counts mean nothing unless it decodes every VALID frame
        # exactly (2026-10-04: a driver AttributeError looked like 40 'rejections')
        s["validated"] = s["valid_exact"] == sum(c["truth"] is not None for c in cases)
        per_impl[n] = s
    disagreements = []
    names = sorted(n for n in res if per_impl[n]["validated"])
    for k, c in enumerate(cases):
        acc = {n: ("r" in res[n][k] and res[n][k]["r"].get("crc_ok", True)) for n in names}
        if len(set(acc.values())) > 1:
            disagreements.append({"id": c["id"], "accepts": acc})
    return {"frames": len(cases), "valid": sum(c["truth"] is not None for c in cases), "per_impl": per_impl,
            "accept_disagreements": disagreements}
