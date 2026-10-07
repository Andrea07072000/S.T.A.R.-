"""star_crc against published catalogue values and hand-derivable CRC properties/invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""

import star_crc as sc


M = b"123456789"


def test_published_catalogue_values_for_named_functions():
    assert sc.crc16_ccsds(M) == 0x29B1
    assert sc.crc16_xmodem(M) == 0x31C3
    assert sc.crc32(M) == 0xCBF43926
    assert sc.crc32c(M) == 0xE3069283


def test_published_catalogue_values_for_generic_crc():
    assert sc.crc(M, 16, 0x8005, 0, True, True, 0) == 0xBB3D      # CRC-16/ARC
    assert sc.crc(M, 16, 0x1021, 0, True, True, 0) == 0x2189      # CRC-16/KERMIT
    assert sc.crc(M, 8, 0x07, 0, False, False, 0) == 0xF4         # CRC-8/SMBUS
    assert sc.crc(M, 64, 0x42F0E1EBA9EA3693, 0, False, False, 0) == 0x6C40DF5F0B497347   # CRC-64/ECMA-182
    assert sc.crc(M, 64, 0x42F0E1EBA9EA3693, 0xFFFFFFFFFFFFFFFF, True, True, 0xFFFFFFFFFFFFFFFF) == 0x995DC9BBDF1939FA  # CRC-64/XZ


def test_other_published_crc32_values():
    assert sc.crc32(b"The quick brown fox jumps over the lazy dog") == 0x414FA339
    assert sc.crc32(b"a") == 0xE8B7BE43


def test_empty_messages_are_preset_then_final_xor():
    # Derivation: no bit processed => register stays at init; function returns register ^ xor_out.
    assert sc.crc16_ccsds(b"") == 0xFFFF
    assert sc.crc16_xmodem(b"") == 0x0000
    assert sc.crc32(b"") == 0x00000000
    assert sc.crc32c(b"") == 0x00000000


def test_leading_zero_bytes_with_zero_and_nonzero_presets():
    # Derivation: with init=0 and non-reflected bit engine, leading all-zero bytes leave register at 0.
    assert sc.crc16_xmodem(b"\x00") == 0
    assert sc.crc16_xmodem(bytes(50)) == 0
    assert sc.crc16_xmodem(b"\x00" + M) == sc.crc16_xmodem(M)
    # With CCSDS nonzero preset, same zero byte transforms register; published hand value below.
    assert sc.crc16_ccsds(b"\x00") == 0xE1F0
    assert sc.crc16_ccsds(b"\x00") != sc.crc16_ccsds(b"")


def test_one_bit_hand_derivable_cases():
    # Derivation: one low bit shifted through 16-bit register with G(x)=x^16+x^12+x^5+1 => remainder 0x1021.
    assert sc.crc16_xmodem(b"\x01") == 0x1021
    # Same idea at width 8 with poly 0x07 => remainder 0x07.
    assert sc.crc(b"\x01", 8, 0x07, 0, False, False, 0) == 0x07


def test_named_functions_equal_generic_parameterizations():
    data = b"\xD3\x5A\x91\x7C"
    assert sc.crc16_ccsds(data) == sc.crc(data, 16, 0x1021, 0xFFFF, False, False, 0)
    assert sc.crc16_xmodem(data) == sc.crc(data, 16, 0x1021, 0x0000, False, False, 0)
    assert sc.crc32(data) == sc.crc(data, 32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF)
    assert sc.crc32c(data) == sc.crc(data, 32, 0x1EDC6F41, 0xFFFFFFFF, True, True, 0xFFFFFFFF)


def test_final_xor_applied_last_and_reflect_out_alone():
    assert sc.crc(M, 16, 0x1021, 0xFFFF, False, False, 0xFFFF) == (sc.crc16_ccsds(M) ^ 0xFFFF)
    assert sc.crc(M, 16, 0x1021, 0xFFFF, False, False, 0xFFFF) == 0xD64E  # CRC-16/GENIBUS check
    # Derivation: reflect_out=True with reflect_in=False reverses final 16-bit register before xor_out.
    x = sc.crc16_xmodem(M)
    assert sc.crc(M, 16, 0x1021, 0, False, True, 0) == int(format(x, "016b")[::-1], 2)


def test_linearity_for_zero_preset_equal_lengths():
    a = b"\xA6\x3D\x91\x4F"
    b = b"\x1C\xE2\x77\x08"
    axb = bytes(x ^ y for x, y in zip(a, b))
    assert sc.crc16_xmodem(a) ^ sc.crc16_xmodem(b) == sc.crc16_xmodem(axb)


def test_append_check_bits_invariants():
    c16 = sc.crc16_ccsds(M).to_bytes(2, "big")
    assert sc.crc16_ccsds(M + c16) == 0
    x16 = sc.crc16_xmodem(M).to_bytes(2, "big")
    assert sc.crc16_xmodem(M + x16) == 0

    c32 = sc.crc32(M).to_bytes(4, "little")
    c32c = sc.crc32c(M).to_bytes(4, "little")
    assert sc.crc32(M + c32) == 0x2144DF1C
    assert sc.crc32c(M + c32c) == 0x48674BC7


def test_single_bit_errors_are_detected():
    base16 = sc.crc16_ccsds(M)
    base32 = sc.crc32(M)
    base32c = sc.crc32c(M)
    for i in range(len(M) * 8):
        msg = bytearray(M)
        msg[i // 8] ^= 1 << (i % 8)
        d = bytes(msg)
        assert sc.crc16_ccsds(d) != base16
        assert sc.crc32(d) != base32
        assert sc.crc32c(d) != base32c


def test_bytearray_and_result_range_for_multiple_widths():
    data_b = b"\x9B\x24\xF1"
    data_a = bytearray(data_b)
    for w, poly in [(8, 0x07), (16, 0x1021), (32, 0x04C11DB7), (64, 0x42F0E1EBA9EA3693)]:
        r1 = sc.crc(data_b, w, poly, 0, False, False, 0)
        r2 = sc.crc(data_a, w, poly, 0, False, False, 0)
        assert r1 == r2
        assert 0 <= r1 < (1 << w)
