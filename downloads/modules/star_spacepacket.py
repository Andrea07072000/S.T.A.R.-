"""star_spacepacket - CCSDS Space Packets: build, read and split, with nothing accepted silently (S.T.A.R., 2026-10-07).
Standard library only.

  encode_header(apid, sequence_count, data_length, packet_type=0, secondary_header=False, sequence_flags=3)   6 octets
  decode_header(octets)             Header(apid, packet_type, secondary_header, sequence_flags, sequence_count, data_length)
  encode_packet(apid, sequence_count, data, packet_type=0, secondary_header=False, sequence_flags=3)   header + data
  decode_packet(octets)             (Header, data): the octets must be exactly one packet
  split_packets(stream)             the packets of a stream laid end to end, as a list of bytes
  next_count(sequence_count)        the following 14-bit count: 16383 is followed by 0
Primary header of CCSDS 133.0-B-2, section 4.1.3, most significant bit first: version (3 bits, always 0), packet type
(1 bit: 0 telemetry, 1 telecommand), secondary header flag (1), application process identifier (11), sequence flags
(2: 0 continuation, 1 first, 2 last, 3 unsegmented), sequence count or packet name (14), packet data length (16:
the number of octets of the data field MINUS ONE, so a data field has from 1 to 65536 octets).
Refusals (ValueError): a field that is not an integer in its range (booleans refused, except the secondary header
flag which must be a bool); a header that is not exactly 6 octets; a version other than 0; data that are not
bytes-like or not from 1 to 65536 octets; a packet whose length disagrees with its header; a stream that ends inside
a packet. An idle packet (APID 2047) is an ordinary packet here: it is returned, not dropped.
"""
from __future__ import annotations

import numbers
from typing import List, NamedTuple, Tuple

__all__ = ["Header", "encode_header", "decode_header", "encode_packet", "decode_packet", "split_packets", "next_count",
           "TELEMETRY", "TELECOMMAND", "CONTINUATION", "FIRST", "LAST", "UNSEGMENTED", "IDLE_APID"]
__version__ = "0.1.1"

TELEMETRY, TELECOMMAND = 0, 1
CONTINUATION, FIRST, LAST, UNSEGMENTED = 0, 1, 2, 3
IDLE_APID = 2047
HEADER_OCTETS = 6
MAX_DATA_OCTETS = 65536


class Header(NamedTuple):
    apid: int
    packet_type: int
    secondary_header: bool
    sequence_flags: int
    sequence_count: int
    data_length: int                 # as transmitted: octets of the data field minus one


def _field(value, name: str, highest: int) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral) or not 0 <= value <= highest:
        raise ValueError(f"{name} must be an integer from 0 to {highest}, got {value!r}")
    return int(value)


def _octets(value, name: str) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise ValueError(f"{name} must be bytes-like, got {type(value).__name__}")
    return bytes(value)


def encode_header(apid: int, sequence_count: int, data_length: int, packet_type: int = TELEMETRY, secondary_header: bool = False,
                  sequence_flags: int = UNSEGMENTED) -> bytes:
    apid = _field(apid, "apid", 2047)
    sequence_count = _field(sequence_count, "sequence_count", 16383)
    data_length = _field(data_length, "data_length", 65535)
    packet_type = _field(packet_type, "packet_type", 1)
    sequence_flags = _field(sequence_flags, "sequence_flags", 3)
    if not isinstance(secondary_header, bool):
        raise ValueError(f"secondary_header must be True or False, got {secondary_header!r}")
    first = (packet_type << 12) | (int(secondary_header) << 11) | apid
    second = (sequence_flags << 14) | sequence_count
    return bytes((first >> 8, first & 0xFF, second >> 8, second & 0xFF, data_length >> 8, data_length & 0xFF))


def decode_header(octets) -> Header:
    raw = _octets(octets, "octets")
    if len(raw) != HEADER_OCTETS:
        raise ValueError(f"a primary header has {HEADER_OCTETS} octets, got {len(raw)}")
    version = raw[0] >> 5
    if version != 0:
        raise ValueError(f"packet version number must be 0, got {version}")
    return Header(apid=((raw[0] & 0x07) << 8) | raw[1], packet_type=(raw[0] >> 4) & 1, secondary_header=bool((raw[0] >> 3) & 1),
                  sequence_flags=raw[2] >> 6, sequence_count=((raw[2] & 0x3F) << 8) | raw[3], data_length=(raw[4] << 8) | raw[5])


def encode_packet(apid: int, sequence_count: int, data, packet_type: int = TELEMETRY, secondary_header: bool = False,
                  sequence_flags: int = UNSEGMENTED) -> bytes:
    body = _octets(data, "data")
    if not 1 <= len(body) <= MAX_DATA_OCTETS:
        raise ValueError(f"the data field must have from 1 to {MAX_DATA_OCTETS} octets, got {len(body)}")
    return encode_header(apid, sequence_count, len(body) - 1, packet_type, secondary_header, sequence_flags) + body


def decode_packet(octets) -> Tuple[Header, bytes]:
    raw = _octets(octets, "octets")
    if len(raw) < HEADER_OCTETS:
        raise ValueError(f"a packet has at least {HEADER_OCTETS + 1} octets, got {len(raw)}")
    header = decode_header(raw[:HEADER_OCTETS])
    expected = HEADER_OCTETS + header.data_length + 1
    if len(raw) != expected:
        raise ValueError(f"the header declares a packet of {expected} octets, got {len(raw)}")
    return header, raw[HEADER_OCTETS:]


def split_packets(stream) -> List[bytes]:
    raw = _octets(stream, "stream")
    packets = []
    position = 0
    while position < len(raw):
        if len(raw) - position < HEADER_OCTETS:
            raise ValueError(f"the stream ends inside a header at octet {position}")
        try:
            header = decode_header(raw[position:position + HEADER_OCTETS])
        except ValueError as err:
            raise ValueError(f"{err} at octet {position}") from None
        end = position + HEADER_OCTETS + header.data_length + 1
        if end > len(raw):
            raise ValueError(f"the stream ends inside the packet that starts at octet {position}: {end - len(raw)} octets missing")
        packets.append(raw[position:end])
        position = end
    return packets


def next_count(sequence_count: int) -> int:
    return (_field(sequence_count, "sequence_count", 16383) + 1) % 16384
