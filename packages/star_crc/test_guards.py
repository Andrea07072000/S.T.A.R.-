"""Guard tests of star_crc written by the reviewer: a second, differently built reference (long division of bit
lists written here), the reflection helper, and every limit at its exact value."""
import pytest

import star_crc as sc

ONES64 = 0xFFFFFFFFFFFFFFFF
VARIANTS = [(16, 0x1021, 0xFFFF, False, False, 0), (16, 0x1021, 0, False, False, 0), (32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF),
            (32, 0x1EDC6F41, 0xFFFFFFFF, True, True, 0xFFFFFFFF), (16, 0x8005, 0, True, True, 0), (16, 0x1021, 0, True, True, 0), (8, 0x07, 0, False, False, 0),
            (8, 0x31, 0xFF, True, True, 0), (16, 0x1021, 0xFFFF, True, True, 0xFFFF), (16, 0x8005, 0xFFFF, True, False, 0x1234), (24, 0x864CFB, 0xB704CE, False, False, 0),
            (12, 0x80F, 0, False, True, 0), (9, 0x119, 0x1FF, False, False, 0x155), (40, 0x0004820009, 0, False, False, 0xFFFFFFFFFF),
            (64, 0x42F0E1EBA9EA3693, 0, False, False, 0), (64, 0x42F0E1EBA9EA3693, ONES64, True, True, ONES64), (63, 0x1B, 1, True, False, 5)]
MESSAGES = [b"", b"\x00", b"\x01", b"\x80", b"\xff", b"123456789", bytes(range(256)), b"\x00\x00\x00\x01", b"\xff" * 9, b"S.T.A.R.", bytes([0x5A, 0xA5] * 20)]


def long_division(message: bytes, width, poly, init, reflect_in, reflect_out, xor_out) -> int:
    """The Rocksoft model as a division of bit lists: no shift register, no masks."""
    bits = []
    for byte in message:
        one = [(byte >> (7 - k)) & 1 for k in range(8)]
        bits += one[::-1] if reflect_in else one
    bits += [0] * width
    for k in range(width):                                   # the preset is an XOR on the first bits of the augmented message
        if k < len(bits):
            bits[k] ^= (init >> (width - 1 - k)) & 1
    generator = [1] + [(poly >> (width - 1 - k)) & 1 for k in range(width)]
    for k in range(len(bits) - width):
        if bits[k]:
            for j, g in enumerate(generator):
                bits[k + j] ^= g
    rest = bits[len(bits) - width:]
    if reflect_out:
        rest = rest[::-1]
    return int("".join(str(b) for b in rest), 2) ^ xor_out


def test_the_reference_division_reproduces_the_catalogue():
    m = b"123456789"
    assert long_division(m, 16, 0x1021, 0xFFFF, False, False, 0) == 0x29B1 and long_division(m, 16, 0x1021, 0, False, False, 0) == 0x31C3
    assert long_division(m, 32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF) == 0xCBF43926 and long_division(m, 16, 0x8005, 0, True, True, 0) == 0xBB3D
    assert long_division(m, 8, 0x07, 0, False, False, 0) == 0xF4 and long_division(m, 64, 0x42F0E1EBA9EA3693, ONES64, True, True, ONES64) == 0x995DC9BBDF1939FA


@pytest.mark.parametrize("variant", VARIANTS)
def test_shift_register_equals_long_division(variant):
    for m in MESSAGES:
        if m == b"" and variant[2] != 0:
            continue                                         # the division needs at least `width` message bits to carry the preset: checked below
        got = sc.crc(m, *variant)
        assert got == long_division(m, *variant), (m, variant)
        assert type(got) is int and 0 <= got < 2 ** variant[0]
        assert sc.crc(bytearray(m), *variant) == got


def test_empty_message_is_the_preset_through_the_output_stage():
    assert sc.crc(b"", 16, 0x1021, 0x1234, False, False, 0) == 0x1234
    assert sc.crc(b"", 16, 0x1021, 0x1234, False, False, 0x00FF) == 0x12CB
    assert sc.crc(b"", 16, 0x1021, 0x1234, False, True, 0) == 0x2C48          # 0001 0010 0011 0100 reversed is 0010 1100 0100 1000
    assert sc.crc(b"", 16, 0x1021, 0x1234, True, False, 0) == 0x1234          # reflect_in touches message bytes only
    assert sc.crc(b"", 8, 0x07, 0x01, False, True, 0) == 0x80 and sc.crc(b"", 12, 0x80F, 0x001, False, True, 0) == 0x800
    assert sc.crc(b"", 64, 0x1B, 1, False, True, 0) == 1 << 63 and sc.crc(b"", 64, 0x1B, ONES64, False, False, ONES64) == 0


def test_reflection_helper():
    assert sc._reflect(0b00000001, 8) == 0b10000000 and sc._reflect(0b11010000, 8) == 0b00001011 and sc._reflect(0, 8) == 0 and sc._reflect(0xFF, 8) == 0xFF
    assert sc._reflect(0x1234, 16) == 0x2C48 and sc._reflect(1, 64) == 1 << 63 and sc._reflect(0b101, 3) == 0b101 and sc._reflect(0b110, 3) == 0b011
    for value in (0x00, 0x01, 0x5A, 0x80, 0xC3, 0xFF):
        assert sc._reflect(sc._reflect(value, 8), 8) == value
    assert sc.crc(b"\x80", 8, 0x07, 0, True, False, 0) == sc.crc(b"\x01", 8, 0x07, 0, False, False, 0) == 0x07   # reflect_in reverses each byte
    assert sc.crc(b"\x01", 8, 0x07, 0, True, False, 0) == sc.crc(b"\x80", 8, 0x07, 0, False, False, 0) == 0x89
    assert sc.crc(b"\x01\x80", 16, 0x1021, 0, True, False, 0) == sc.crc(b"\x80\x01", 16, 0x1021, 0, False, False, 0)


def test_limits_at_their_exact_values():
    assert sc.MAX_BYTES == 65536
    assert sc.crc16_xmodem(bytes(65536)) == 0
    with pytest.raises(ValueError, match="data must be bytes"):
        sc.crc16_xmodem(bytes(65537))
    assert sc.crc(b"\x01", 8, 0x01, 0, False, False, 0) == 0x01 and sc.crc(b"\x01", 8, 0xFF, 0, False, False, 0) == 0xFF     # the smallest and largest polynomials
    assert sc.crc(b"\x01", 64, ONES64, 0, False, False, 0) == ONES64 and sc.crc(b"", 8, 0x07, 0xFF, False, False, 0xFF) == 0
    assert sc.crc(b"", 8, 0x07, 0xFF, False, False, 0) == 0xFF and sc.crc(b"", 8, 0x07, 0, False, False, 0xFF) == 0xFF
    for width, word in ((7, "width"), (65, "width"), (0, "width"), (-8, "width")):
        with pytest.raises(ValueError, match=word):
            sc.crc(b"a", width, 0x07, 0, False, False, 0)
    for poly, word in ((0, "poly"), (0x100, "poly"), (0x101, "poly"), (-1, "poly"), (2, "odd"), (0xFE, "odd")):
        with pytest.raises(ValueError, match=word):
            sc.crc(b"a", 8, poly, 0, False, False, 0)
    for bad in (-1, 0x100):
        with pytest.raises(ValueError, match="init"):
            sc.crc(b"a", 8, 0x07, bad, False, False, 0)
        with pytest.raises(ValueError, match="xor_out"):
            sc.crc(b"a", 8, 0x07, 0, False, False, bad)
    for bad in (True, 8.0, "8", None, float("nan"), float("inf")):
        for position in (1, 2, 3, 6):
            args = [b"a", 8, 0x07, 0, False, False, 0]
            args[position] = bad
            with pytest.raises(ValueError, match="must be an integer"):
                sc.crc(*args)
    for bad in (0, 1, None, "True", 1.0):
        with pytest.raises(ValueError, match="reflect_in and reflect_out"):
            sc.crc(b"a", 8, 0x07, 0, bad, False, 0)
        with pytest.raises(ValueError, match="reflect_in and reflect_out"):
            sc.crc(b"a", 8, 0x07, 0, False, bad, 0)
    for bad in ("abc", None, [1, 2], memoryview(b"ab"), 5, (1, 2), float("nan")):
        for f in (sc.crc16_ccsds, sc.crc16_xmodem, sc.crc32, sc.crc32c, lambda d: sc.crc(d, 8, 0x07, 0, False, False, 0)):
            with pytest.raises(ValueError, match="data must be bytes"):
                f(bad)
