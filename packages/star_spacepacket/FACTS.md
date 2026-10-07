# Published values the tests of star_spacepacket may cite (checked by the reviewer against the computation)

1. CCSDS 133.0-B-2, Space Packet Protocol, section 4.1.3 (packet primary header), most significant bit first: packet version number (3 bits, '000'), packet type (1 bit:
   0 telemetry, 1 telecommand), secondary header flag (1 bit), application process identifier (11 bits; 2047 = all ones is the idle packet), sequence flags (2 bits: 00 continuation,
   01 first, 10 last, 11 unsegmented), packet sequence count or packet name (14 bits), packet data length (16 bits: the number of octets in the packet data field MINUS ONE).
   The primary header has 6 octets; the data field has from 1 to 65536 octets; a packet has from 7 to 65542 octets.
   Written out by hand from that layout:
   - telemetry, secondary header present, APID 0x123, unsegmented, count 42, two data octets: first word 000 0 1 00100100011 = 0x0923, second word 11 00000000101010 = 0xC02A,
     length 1: encode_header(0x123, 42, 1, secondary_header=True) == bytes.fromhex("0923c02a0001");
   - the idle packet with one data octet: encode_header(2047, 0, 0) == bytes.fromhex("07ffc0000000");
   - telecommand, APID 0, continuation, count 0, one data octet: encode_header(0, 0, 0, packet_type=1, sequence_flags=0) == bytes.fromhex("100000000000");
   - every field at its maximum: encode_header(2047, 16383, 65535, 1, True, 3) == bytes.fromhex("1fffffffffff").

Values derivable by hand (write the derivation in a comment):
- constants: TELEMETRY == 0, TELECOMMAND == 1, CONTINUATION == 0, FIRST == 1, LAST == 2, UNSEGMENTED == 3, IDLE_APID == 2047, HEADER_OCTETS == 6, MAX_DATA_OCTETS == 65536;
- encode_header(apid, sequence_count, data_length, packet_type=0, secondary_header=False, sequence_flags=3) returns 6 bytes; the defaults are telemetry, no secondary header, unsegmented:
  encode_header(1, 0, 0) == bytes.fromhex("0001c0000000"); each field alone: APID 0x7FF sets the low 3 bits of octet 0 and all of octet 1; packet_type=1 sets bit 0x10 of octet 0;
  secondary_header=True sets bit 0x08 of octet 0; sequence_flags 1, 2, 3 give 0x40, 0x80, 0xC0 in octet 2; sequence_count 0x3FFF gives 3F FF in octets 2-3; data_length 0x1234 gives 12 34;
- decode_header(octets) returns the named tuple Header(apid, packet_type, secondary_header, sequence_flags, sequence_count, data_length), secondary_header a bool:
  decode_header(bytes.fromhex("0923c02a0001")) == (0x123, 0, True, 3, 42, 1); decode_header(bytes.fromhex("1fffffffffff")) == (2047, 1, True, 3, 16383, 65535);
  decode_header(encode_header(f...)) gives back the fields for every valid combination; bytes, bytearray and memoryview are accepted;
- encode_packet(apid, sequence_count, data, ...) returns the header followed by the data, with data_length = len(data) - 1:
  encode_packet(0x123, 42, b"AB", secondary_header=True) == bytes.fromhex("0923c02a00014142"); encode_packet(2047, 0, b"\x00") has 7 octets; a data field of 65536 octets gives a packet of
  65542 octets whose length field is FF FF;
- decode_packet(octets) returns (Header, data) and requires exactly one whole packet: decode_packet(bytes.fromhex("0923c02a00014142")) == (Header(0x123, 0, True, 3, 42, 1), b"AB");
- split_packets(stream) returns the list of the packets (each as bytes, header included) of a stream laid end to end: an empty stream gives []; two packets give two items whose
  concatenation is the stream; an idle packet in the middle is returned like any other;
- next_count(c) == c + 1 for c from 0 to 16382 and next_count(16383) == 0.

Refusals (ValueError):
- encode_header / encode_packet: apid -1, 2048; sequence_count -1, 16384; data_length -1, 65536; packet_type 2, -1; sequence_flags 4, -1; any of them a float (1.0), a string, None or a
  bool ("must be an integer from 0 to N"); secondary_header that is not a bool (0, 1, None, "yes": "must be True or False");
- encode_packet: data that are not bytes-like (a string, a list of integers, None: "bytes-like"); empty data or more than 65536 octets ("from 1 to 65536 octets");
- decode_header: not bytes-like; not exactly 6 octets (5, 7, 0: "a primary header has 6 octets"); a version other than 0 (first octet 0x20 .. 0xE0: "packet version number must be 0");
- decode_packet: fewer than 6 octets ("at least 7 octets"); a length that disagrees with the header, shorter or longer ("the header declares a packet of N octets");
  exactly 6 octets is refused as well (the header then declares at least 7);
- split_packets: a stream that ends inside a header ("ends inside a header at octet N"), or inside a packet ("ends inside the packet that starts at octet N: K octets missing"); a packet with
  a version other than 0 ("packet version number must be 0, got V at octet N"); nothing is returned in these cases, not even the packets before;
- next_count: -1, 16384, 1.0, True, None.
