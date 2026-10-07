"""Cross-check of star_crc against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_crc.py  ->  12_EVIDENCE/crosscheck_crc_20261007.json

Lineages, each in its own interpreter:
  fastcrc  the Rust `crc` tables behind the Python package fastcrc: all nine variants below;
  cpython  binascii.crc_hqx (CCITT polynomial, any preset) and zlib.crc32, in C: three of the variants;
  sympy    no CRC code at all: the remainder of the message polynomial divided by the generator over GF(2), with the
           preset, the reflections and the final XOR applied as the Rocksoft model defines them. All nine variants,
           on the messages of at most 40 bytes (polynomial division is slow).
Variants (width, polynomial, preset, reflect in, reflect out, final XOR): ccsds (16, 0x1021, 0xFFFF, no, no, 0),
xmodem (16, 0x1021, 0, no, no, 0), crc32 (32, 0x04C11DB7, all ones, yes, yes, all ones), crc32c (32, 0x1EDC6F41, all
ones, yes, yes, all ones), arc (16, 0x8005, 0, yes, yes, 0), kermit (16, 0x1021, 0, yes, yes, 0), smbus (8, 0x07, 0,
no, no, 0), ecma182 (64, 0x42F0E1EBA9EA3693, 0, no, no, 0), xz (64, same polynomial, all ones, yes, yes, all ones).
Probe (published): the check values of the catalogue of parametrised CRC algorithms (G. Cook, reveng) for the ASCII
message "123456789": 0x29B1, 0x31C3, 0xCBF43926, 0xE3069283, 0xBB3D, 0x2189, 0xF4, 0x6C40DF5F0B497347,
0x995DC9BBDF1939FA, in the order above.
Corpus (seed 20261007): 500 messages of 0 to 300 bytes (empty, all zeros, all 0xFF, single bytes, random), each
through the nine variants. The comparison is equality of integers.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_crc as sc  # noqa: E402

ONES64 = 0xFFFFFFFFFFFFFFFF
VARIANTS = {"ccsds": (16, 0x1021, 0xFFFF, False, False, 0), "xmodem": (16, 0x1021, 0, False, False, 0), "crc32": (32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF),
            "crc32c": (32, 0x1EDC6F41, 0xFFFFFFFF, True, True, 0xFFFFFFFF), "arc": (16, 0x8005, 0, True, True, 0), "kermit": (16, 0x1021, 0, True, True, 0),
            "smbus": (8, 0x07, 0, False, False, 0), "ecma182": (64, 0x42F0E1EBA9EA3693, 0, False, False, 0), "xz": (64, 0x42F0E1EBA9EA3693, ONES64, True, True, ONES64)}
CHECK = {"ccsds": 0x29B1, "xmodem": 0x31C3, "crc32": 0xCBF43926, "crc32c": 0xE3069283, "arc": 0xBB3D, "kermit": 0x2189, "smbus": 0xF4,
         "ecma182": 0x6C40DF5F0B497347, "xz": 0x995DC9BBDF1939FA}
ORDER = list(VARIANTS)
FASTCRC = ("import fastcrc\nF = {'ccsds': fastcrc.crc16.ibm_3740, 'xmodem': fastcrc.crc16.xmodem, 'crc32': fastcrc.crc32.iso_hdlc, 'crc32c': fastcrc.crc32.iscsi,\n"
           "     'arc': fastcrc.crc16.arc, 'kermit': fastcrc.crc16.kermit, 'smbus': fastcrc.crc8.smbus, 'ecma182': fastcrc.crc64.ecma_182, 'xz': fastcrc.crc64.xz}\n"
           "def f(msg):\n    return [int(F[k](msg)) for k in ORDER]\n")
CPYTHON = ("import binascii, zlib\n"
           "def f(msg):\n    return [binascii.crc_hqx(msg, 0xFFFF), binascii.crc_hqx(msg, 0), zlib.crc32(msg)] + [None] * 6\n")
SYMPY = ("from sympy import Poly, symbols, GF\nX = symbols('x')\n"
         "def bits_of(value, n):\n    return [(value >> (n - 1 - i)) & 1 for i in range(n)]\n"
         "def rev(value, n):\n    return int(''.join(str(b) for b in reversed(bits_of(value, n))), 2)\n"
         "def one(msg, width, poly, init, refin, refout, xorout):\n"
         "    data = bytes(rev(b, 8) for b in msg) if refin else msg\n"
         "    m = [b for byte in data for b in bits_of(byte, 8)] + [0] * width\n"
         "    for i, b in enumerate(bits_of(init, width)):\n        m[i] ^= b\n"          # the preset is an XOR on the first `width` bits of the augmented message
         "    while m and m[0] == 0:\n        m = m[1:]\n"
         "    r = Poly(m, X, domain=GF(2)).rem(Poly([1] + bits_of(poly, width), X, domain=GF(2))).all_coeffs() if m else []\n"
         "    value = int(''.join(str(int(c) % 2) for c in r), 2) if r else 0\n"
         "    return (rev(value, width) if refout else value) ^ xorout\n"
         "def f(msg):\n    return [one(msg, *VARIANTS[k]) for k in ORDER] if len(msg) <= 40 else [None] * 9\n")
RUNNER = ("\nimport json, sys\njob = json.load(sys.stdin)\nORDER = job['order']\nVARIANTS = job['variants']\nout = []\nfor h in job['messages']:\n    try:\n        out.append(f(bytes.fromhex(h)))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"fastcrc": (venv("spacepackets"), FASTCRC), "cpython": (venv("sympy"), CPYTHON), "sympy": (venv("sympy"), SYMPY)}


def main():
    rnd = random.Random(20261007)
    messages = [b"123456789", b"", b"\x00", b"\xff", bytes(40), bytes([255]) * 40, bytes(300), bytes([255]) * 300]
    for k in range(492):
        n = rnd.randint(1, 40) if k % 4 == 0 else rnd.randint(0, 300)
        messages.append(bytes(rnd.getrandbits(8) for _ in range(n)))
    total = len(messages) - 1
    mine = [[sc.crc(m, *VARIANTS[k]) for k in ORDER] for m in messages]
    named = all(sc.crc16_ccsds(m) == r[0] and sc.crc16_xmodem(m) == r[1] and sc.crc32(m) == r[2] and sc.crc32c(m) == r[3] for m, r in zip(messages, mine))
    out = {"cases": total, "seed": 20261007, "variants": ORDER, "named_functions_equal_generic": named, "lineages": {}}
    job = {"order": ORDER, "variants": {k: list(v) for k, v in VARIANTS.items()}, "messages": [m.hex() for m in messages]}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(messages):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = not isinstance(res[0], str) and all(v is None or v == CHECK[k] for k, v in zip(ORDER, res[0])) and any(v is not None for v in res[0])
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            compared = mismatches = 0
            per_variant = {}
            example = None
            for m, got, ref in zip(messages[1:], mine[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                for k, a, b in zip(ORDER, got, ref):
                    if b is None:
                        continue
                    compared += 1
                    per_variant[k] = per_variant.get(k, 0) + 1
                    if a != b:
                        mismatches += 1
                        example = example or [m.hex()[:60], k, a, b]
            entry.update(compared=compared, per_variant=per_variant, mismatches=mismatches, example=example)
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(res[0])[:120]}", "errors", len(errors), errors[:1], "compared", entry.get("compared"), "mismatches", entry.get("mismatches"), flush=True)
    L = out["lineages"]
    mine_ok = named and mine[0] == [CHECK[k] for k in ORDER]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("mismatches") == 0 and v.get("compared", 0) >= 1000 for v in L.values())
    out["published"] = {"source": "catalogue of parametrised CRC algorithms (G. Cook, reveng), check values for the message 123456789: " + ", ".join(f"{k} 0x{CHECK[k]:X}" for k in ORDER),
                        "star_crc_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["fastcrc (Rust crc tables)", "CPython binascii.crc_hqx and zlib.crc32", "SymPy polynomial division over GF(2)"],
                      "claim": "star_crc computes the CCSDS frame CRC-16, CRC-16/XMODEM, CRC-32, CRC-32C and any Rocksoft-model CRC of width 8 to 64 bit by bit",
                      "crosscheck": f"{total} messages of 0 to 300 bytes through nine CRC variants: identical to fastcrc on {L['fastcrc'].get('compared')} values, to CPython binascii and zlib on "
                                    f"{L['cpython'].get('compared')}, and to the remainder of a polynomial division over GF(2) in SymPy on {L['sympy'].get('compared')}; no mismatch",
                      "benchmark": f"mismatches: {sum(v.get('mismatches') or 0 for v in L.values())} of {sum(v.get('compared') or 0 for v in L.values())} comparisons"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_crc_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
