# Published values the tests of star_crc may cite (checked by the reviewer against the computation)

1. Catalogue of parametrised CRC algorithms (Greg Cook, "reveng" catalogue), check values for the nine ASCII bytes b"123456789":
   CRC-16/IBM-3740 (the CCSDS frame CRC, "CCITT-FALSE": width 16, poly 0x1021, init 0xFFFF, no reflection, xorout 0): 0x29B1 -> crc16_ccsds
   CRC-16/XMODEM (width 16, poly 0x1021, init 0, no reflection, xorout 0): 0x31C3 -> crc16_xmodem
   CRC-32/ISO-HDLC (width 32, poly 0x04C11DB7, init 0xFFFFFFFF, reflected in and out, xorout 0xFFFFFFFF): 0xCBF43926 -> crc32
   CRC-32/ISCSI, CRC-32C (width 32, poly 0x1EDC6F41, init 0xFFFFFFFF, reflected in and out, xorout 0xFFFFFFFF): 0xE3069283 -> crc32c
   and through the generic crc(data, width, poly, init, reflect_in, reflect_out, xor_out):
   CRC-16/ARC crc(m, 16, 0x8005, 0, True, True, 0) == 0xBB3D; CRC-16/KERMIT crc(m, 16, 0x1021, 0, True, True, 0) == 0x2189;
   CRC-8/SMBUS crc(m, 8, 0x07, 0, False, False, 0) == 0xF4; CRC-64/ECMA-182 crc(m, 64, 0x42F0E1EBA9EA3693, 0, False, False, 0) == 0x6C40DF5F0B497347;
   CRC-64/XZ crc(m, 64, 0x42F0E1EBA9EA3693, 0xFFFFFFFFFFFFFFFF, True, True, 0xFFFFFFFFFFFFFFFF) == 0x995DC9BBDF1939FA.
2. CCSDS 132.0-B (TM Space Data Link Protocol), Frame Error Control Field: generator polynomial x^16 + x^12 + x^5 + 1 (0x1021), shift register preset to all ones,
   the 16 check bits appended most significant first. A frame followed by its own check bits gives a zero register: crc16_ccsds(m + crc16_ccsds(m).to_bytes(2, "big")) == 0.
3. Widely published CRC-32 values: crc32(b"The quick brown fox jumps over the lazy dog") == 0x414FA339; crc32(b"a") == 0xE8B7BE43.

Values derivable by hand (write the derivation in a comment). Every result is an int:
- the empty message returns the preset register, final XOR applied: crc16_ccsds(b"") == 0xFFFF; crc16_xmodem(b"") == 0; crc32(b"") == 0 and crc32c(b"") == 0
  (0xFFFFFFFF reflected is itself, XOR 0xFFFFFFFF gives 0);
- a zero preset ignores leading zero bytes: crc16_xmodem(b"\x00") == 0 and crc16_xmodem(bytes(50)) == 0, crc16_xmodem(b"\x00" + m) == crc16_xmodem(m);
  with the CCSDS preset they are NOT ignored: crc16_ccsds(b"\x00") == 0xE1F0 != crc16_ccsds(b"");
- one bit: crc16_xmodem(b"\x01") == 0x1021 (the bit is shifted 16 times, x^16 mod G is the polynomial without its top term); crc(b"\x01", 8, 0x07, 0, False, False, 0) == 0x07;
- the named functions are the generic one with their parameters: crc16_ccsds(m) == crc(m, 16, 0x1021, 0xFFFF, False, False, 0), and so on for the other three;
- the final XOR is applied last: crc(m, 16, 0x1021, 0xFFFF, False, False, 0xFFFF) == crc16_ccsds(m) ^ 0xFFFF (this variant is CRC-16/GENIBUS, check value 0xD64E);
- reflect_out alone reverses the 16 bits of the result: crc(m, 16, 0x1021, 0, False, True, 0) == int(format(crc16_xmodem(m), "016b")[::-1], 2);
- linearity with a zero preset: crc16_xmodem(a) ^ crc16_xmodem(b) == crc16_xmodem(bytes(x ^ y for x, y in zip(a, b))) for a and b of equal length;
- every single-bit error is detected: flipping any one bit of b"123456789" changes crc16_ccsds, crc32 and crc32c;
- check bits appended: crc16_xmodem(m + crc16_xmodem(m).to_bytes(2, "big")) == 0 for every m; for the reflected 32-bit CRCs the check is appended least significant byte
  first and the result is a constant: crc32(m + crc32(m).to_bytes(4, "little")) == 0x2144DF1C and crc32c(m + crc32c(m).to_bytes(4, "little")) == 0x48674BC7 for every m;
- bytes and bytearray give the same result; the result is in range(2 ** width).

Limits (state them): MAX_BYTES == 65536; width 8 to 64. Refusals (ValueError):
- data: a str ("abc"), None, a list of ints, a memoryview, an int; 65537 bytes (65536 accepted: crc16_xmodem(bytes(65536)) == 0) ("data must be bytes or bytearray");
- crc: width 7, 65, 8.0, True, None ("width"); poly 0, an even poly (6), poly 2 ** width (0x107 for width 8), a float ("poly"; an even one says "odd");
  init or xor_out equal to -1 or 2 ** width ("init", "xor_out"); reflect_in or reflect_out that is 0, 1 or None instead of a bool ("reflect_in and reflect_out").
