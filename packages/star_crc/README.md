# star_crc — cyclic redundancy checks, bit by bit

The CRC-16 of CCSDS transfer frames, CRC-16/XMODEM, CRC-32, CRC-32C and any other CRC of the Rocksoft model from 8
to 64 bits, computed through the shift register that defines them. Standard library only.

```python
import star_crc as sc
hex(sc.crc16_ccsds(b"123456789"))                       # '0x29b1'
hex(sc.crc32(b"123456789"))                             # '0xcbf43926'
frame = b"..."                                          # a transfer frame without its error control field
sc.crc16_ccsds(frame + sc.crc16_ccsds(frame).to_bytes(2, "big"))   # 0: a frame with its check bits verifies
hex(sc.crc(b"123456789", 16, 0x8005, 0, True, True, 0)) # '0xbb3d': CRC-16/ARC through the generic function
```

## Requirements
- R1 `crc16_ccsds(data)` is the Frame Error Control Field of CCSDS TM, AOS and TC transfer frames (polynomial
  0x1021, register preset to all ones); `crc16_xmodem`, `crc32` and `crc32c` are the other three named variants.
- R2 `crc(data, width, poly, init, reflect_in, reflect_out, xor_out)` computes any CRC described by those six
  parameters, width 8 to 64. The message goes through the shift register one bit at a time: no table.
- R3 Measured on 499 messages of 0 to 300 bytes through nine variants: identical to fastcrc on 4491 values, to
  CPython `binascii.crc_hqx` and `zlib.crc32` on 1497, and to the remainder of a polynomial division over GF(2) done
  in SymPy (no CRC code involved) on 1611. No mismatch.
- R4 Every function returns an int in [0, 2^width) or raises `ValueError`: data that is not bytes or bytearray or is
  longer than 65536 bytes, a width, polynomial, preset or final XOR out of range, an even polynomial, reflection
  flags that are not bools.

## Evidence
- Published: the check values of the reveng catalogue for "123456789" (nine variants); the CCSDS 132.0-B generator
  and preset; two widely published CRC-32 values. One-bit and empty messages by hand.
- `crosscheck_crc.py`: fastcrc, CPython and SymPy, each in its own interpreter.

## What is NOT claimed
A CRC detects errors with a known probability; it does not authenticate and does not correct. This module computes
check values: it does not frame, randomise or decode telemetry (see `star_telemetry` in this repository). Bit-by-bit
processing in Python is slow (about 0.2 s for 65536 bytes): it is a reference and a verifier, not a link-rate
implementation. Widths below 8 or above 64 and polynomials without the term 1 are refused, not supported.
