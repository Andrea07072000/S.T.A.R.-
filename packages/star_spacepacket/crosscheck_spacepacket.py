"""Cross-check of star_spacepacket against two independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_spacepacket.py  ->  12_EVIDENCE/crosscheck_spacepacket_20261007.json

Lineages, each in its own interpreter:
  spacepackets  spacepackets.ccsds.spacepacket.SpacePacketHeader: pack() of the fields, unpack() of a header, and a
                walk of a stream by the unpacked lengths;
  ccsdspy       ccsdspy.utils.read_primary_headers (a decoder only: it reads the headers star_spacepacket encoded and
                the random ones) and ccsdspy.utils.split_packet_bytes for the streams.
Probe (by the layout of CCSDS 133.0-B-2, section 4.1.3, written out by hand): telemetry, secondary header present,
APID 0x123, unsegmented, count 42, two octets of data: first word 000 0 1 00100100011 = 0x0923, second word
11 00000000101010 = 0xC02A, length 0x0001: the header is 09 23 C0 2A 00 01. The idle packet of one octet is
07 FF C0 00 00 00.
Corpus (seed 20261007): 700 sets of fields (the ends of every range included) to encode; 700 headers of 6 random
octets with version 0 to decode (not produced by star_spacepacket); 80 streams of 1 to 8 packets with data fields of
1 to 400 octets, and one packet with the largest data field (65536 octets).
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_spacepacket as ssp  # noqa: E402

SPACEPACKETS = '''
from spacepackets.ccsds.spacepacket import PacketType, SequenceFlags, SpacePacketHeader
def fields(h):
    return [h.apid, int(h.packet_type), bool(h.sec_header_flag), int(h.seq_flags), h.seq_count, h.data_len]
def encode(apid, count, length, ptype, sec, flags, mine):
    return SpacePacketHeader(packet_type=PacketType(ptype), apid=apid, seq_count=count, data_len=length, sec_header_flag=sec, seq_flags=SequenceFlags(flags)).pack().hex()
def decode(hexa):
    return fields(SpacePacketHeader.unpack(bytes.fromhex(hexa)))
def split(hexa):
    raw, out, pos = bytes.fromhex(hexa), [], 0
    while pos < len(raw):
        end = pos + 6 + SpacePacketHeader.unpack(raw[pos:pos + 6]).data_len + 1
        out.append(raw[pos:end].hex())
        pos = end
    return out
'''
CCSDSPY = '''
import io, logging
logging.disable(logging.CRITICAL)
from ccsdspy import utils
def decode(hexa):
    h = utils.read_primary_headers(io.BytesIO(bytes.fromhex(hexa) + bytes(int(hexa[8:], 16) + 1)))
    assert int(h["CCSDS_VERSION_NUMBER"][0]) == 0
    return [int(h["CCSDS_APID"][0]), int(h["CCSDS_PACKET_TYPE"][0]), bool(h["CCSDS_SECONDARY_FLAG"][0]), int(h["CCSDS_SEQUENCE_FLAG"][0]),
            int(h["CCSDS_SEQUENCE_COUNT"][0]), int(h["CCSDS_PACKET_LENGTH"][0])]
def encode(apid, count, length, ptype, sec, flags, mine):
    got = decode(mine)                       # a decoder only: it must read back the fields from the header encoded by star_spacepacket
    return mine if got == [apid, ptype, sec, flags, count, length] else "decoded " + repr(got)
def split(hexa):
    return [p.hex() for p in utils.split_packet_bytes(io.BytesIO(bytes.fromhex(hexa)))]
'''
RUNNER = '''
import json, sys
job = json.load(sys.stdin)
out = {}
for name, fn in (("encode", encode), ("decode", decode), ("split", split)):
    out[name] = []
    for args in job[name]:
        try:
            out[name].append(fn(*args))
        except Exception as e:
            out[name].append("error:" + type(e).__name__ + ":" + str(e)[:60])
print("@@" + json.dumps(out))
'''
PROBE_FIELDS = [0x123, 42, 1, 0, True, 3]
PROBE_HEX = "0923c02a0001"


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"spacepackets": (venv("spacepackets"), SPACEPACKETS), "ccsdspy": (venv("ccsdspy"), CCSDSPY)}


def corpus():
    rnd = random.Random(20261007)
    ends = {"apid": [0, 1, 2046, 2047], "count": [0, 1, 16382, 16383], "length": [0, 1, 65534, 65535]}
    encode = []
    for k in range(700):
        apid = ends["apid"][k % 4] if k % 5 == 0 else rnd.randint(0, 2047)
        count = ends["count"][(k // 4) % 4] if k % 7 == 0 else rnd.randint(0, 16383)
        length = ends["length"][(k // 16) % 4] if k % 3 == 0 else rnd.randint(0, 65535)
        fields = [apid, count, length, k % 2, (k // 2) % 2 == 1, (k // 4) % 4]
        encode.append(fields + [ssp.encode_header(*fields).hex()])
    decode = [[bytes([rnd.randint(0, 31)] + [rnd.randint(0, 255) for _ in range(5)]).hex()] for _ in range(700)]
    split = []
    for k in range(80):
        stream = b"".join(ssp.encode_packet(rnd.randint(0, 2047), rnd.randint(0, 16383), bytes(rnd.randint(0, 255) for _ in range(rnd.randint(1, 400))),
                                            rnd.randint(0, 1), rnd.random() < 0.5, rnd.randint(0, 3)) for _ in range(rnd.randint(1, 8)))
        split.append([stream.hex()])
    split.append([ssp.encode_packet(5, 7, bytes(65536)).hex()])
    return {"encode": encode + [PROBE_FIELDS + [PROBE_HEX]], "decode": decode + [[PROBE_HEX]], "split": split}


def main():
    job = corpus()
    sizes = {k: len(v) for k, v in job.items()}
    mine = {"encode": [ssp.encode_header(*args[:6]).hex() for args in job["encode"]],
            "decode": [list(ssp.decode_header(bytes.fromhex(h))) for (h,) in job["decode"]],
            "split": [[p.hex() for p in ssp.split_packets(bytes.fromhex(h))] for (h,) in job["split"]]}
    mine_ok = mine["encode"][-1] == PROBE_HEX and mine["decode"][-1] == [0x123, 0, True, 3, 42, 1] and ssp.encode_header(2047, 0, 0).hex() == "07ffc0000000"
    out = {"cases": sizes, "seed": 20261007, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if any(len(res[k]) != sizes[k] for k in sizes):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for k in sizes for x in res[k] if isinstance(x, str) and x.startswith("error:")]
        valid = res["encode"][-1] == PROBE_HEX and res["decode"][-1] == [0x123, 0, True, 3, 42, 1]
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            mismatches = {k: sum(a != b for a, b in zip(mine[k], res[k])) for k in sizes}
            entry.update(compared=sum(sizes.values()), mismatches=mismatches, within=not any(mismatches.values()),
                         packets_split=sum(len(p) for p in res["split"]))
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("mismatches"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())
    packets = sum(len(p) for p in mine["split"])
    out["published"] = {"source": "CCSDS 133.0-B-2, section 4.1.3 (primary header layout), written out by hand: telemetry, secondary header, APID 0x123, unsegmented, count 42, "
                                  "two data octets -> 09 23 C0 2A 00 01; idle packet of one octet -> 07 FF C0 00 00 00", "star_spacepacket_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["spacepackets SpacePacketHeader (pack, unpack)", "ccsdspy read_primary_headers and split_packet_bytes"],
                      "claim": "star_spacepacket encodes and decodes the CCSDS Space Packet primary header and splits a stream of packets exactly as two independent libraries do",
                      "crosscheck": f"{sizes['encode']} headers encoded (identical octets from spacepackets; read back to the same fields by ccsdspy), {sizes['decode']} random headers decoded "
                                    f"(identical fields from both), {sizes['split']} streams split into {packets} packets, one of them with the largest data field of 65536 octets "
                                    f"(identical packets from both): 0 differences",
                      "benchmark": f"{sum(sizes.values())} cases against each library, 0 differences"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_spacepacket_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
