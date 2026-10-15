"""star_crc - cyclic redundancy checks of space data links, bit by bit (S.T.A.R., 2026-10-07).
Standard library only.

  crc16_ccsds(data)    CRC-16 with polynomial 0x1021, register preset to all ones: the Frame Error Control Field of
                       CCSDS TM, AOS and TC transfer frames (catalogue name CRC-16/IBM-3740, "CCITT-FALSE")
  crc16_xmodem(data)   the same polynomial with the register preset to zero (CRC-16/XMODEM)
  crc32(data)          CRC-32/ISO-HDLC, the CRC of Ethernet, zip and PNG
  crc32c(data)         CRC-32C (Castagnoli, CRC-32/ISCSI)
  crc(data, width, poly, init, reflect_in, reflect_out, xor_out)   any CRC of the Rocksoft model, width 8 to 64
The message is processed one bit at a time through the shift register that defines a CRC: no table, nothing to get
out of step. Each function returns an int in [0, 2^width).
Refusals (ValueError): data that is not bytes or bytearray (a str is refused: encode it first) or is longer than
65536 bytes; width not an integer from 8 to 64; a polynomial that is not an odd integer in [1, 2^width) (every CRC
polynomial has the term 1); init or xor_out outside [0, 2^width); reflect flags that are not bools.
"""
from __future__ import annotations

import numbers

__all__ = ["crc", "crc16_ccsds", "crc16_xmodem", "crc32", "crc32c"]
__version__ = "0.1.0"

MAX_BYTES = 65536


def _reflect(value: int, bits: int) -> int:
    out = 0
    for _ in range(bits):
        out = (out << 1) | (value & 1)
        value >>= 1
    return out


def _word(v, what: str, lowest: int, highest: int) -> int:
    if isinstance(v, bool) or not isinstance(v, numbers.Integral) or not lowest <= v <= highest:
        raise ValueError(f"{what} must be an integer from {lowest} to {highest}")
    return int(v)


def crc(data, width: int, poly: int, init: int, reflect_in: bool, reflect_out: bool, xor_out: int) -> int:
    if not isinstance(data, (bytes, bytearray)) or len(data) > MAX_BYTES:
        raise ValueError("data must be bytes or bytearray of at most 65536 bytes")
    w = _word(width, "width", 8, 64)
    mask = (1 << w) - 1
    g = _word(poly, "poly", 1, mask)
    if g % 2 == 0:
        raise ValueError("poly must be odd: a CRC polynomial has the term 1")
    register, final = _word(init, "init", 0, mask), _word(xor_out, "xor_out", 0, mask)
    if not isinstance(reflect_in, bool) or not isinstance(reflect_out, bool):
        raise ValueError("reflect_in and reflect_out must be True or False")
    top = 1 << (w - 1)
    for byte in data:
        register ^= (_reflect(byte, 8) if reflect_in else byte) << (w - 8)
        for _ in range(8):
            register = ((register << 1) ^ g) & mask if register & top else (register << 1) & mask
    return (_reflect(register, w) if reflect_out else register) ^ final


def crc16_ccsds(data) -> int:
    return crc(data, 16, 0x1021, 0xFFFF, False, False, 0x0000)


def crc16_xmodem(data) -> int:
    return crc(data, 16, 0x1021, 0x0000, False, False, 0x0000)


def crc32(data) -> int:
    return crc(data, 32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF)


def crc32c(data) -> int:
    return crc(data, 32, 0x1EDC6F41, 0xFFFFFFFF, True, True, 0xFFFFFFFF)
