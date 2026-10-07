# star_spacepacket — CCSDS Space Packets, built and read strictly

Build, read and split CCSDS Space Packets (CCSDS 133.0-B-2). Every field is checked on the way in and on the way
out: nothing out of range is masked, no truncated packet is returned as if it were whole. Standard library only.

```python
import star_spacepacket as ssp
ssp.encode_packet(0x123, 42, b"AB", secondary_header=True).hex()   # '0923c02a00014142'
ssp.decode_header(bytes.fromhex("0923c02a0001"))
# Header(apid=291, packet_type=0, secondary_header=True, sequence_flags=3, sequence_count=42, data_length=1)
ssp.split_packets(stream)          # list of packets, or ValueError saying at which octet the stream breaks
ssp.next_count(16383)              # 0
```

## Requirements
- R1 `encode_header` and `decode_header` convert between the six fields of the primary header and its 6 octets;
  `encode_packet` and `decode_packet` do the same for a whole packet, the length field being the number of data
  octets minus one; `split_packets` cuts a stream of packets laid end to end; `next_count` advances the 14-bit
  sequence count.
- R2 Layout of CCSDS 133.0-B-2, section 4.1.3: version (3 bits, 0), type (1), secondary header flag (1), APID (11),
  sequence flags (2), sequence count (14), data length (16).
- R3 Measured against two independent libraries, spacepackets and ccsdspy, each in its own interpreter: 701 headers
  encoded, 701 random headers decoded, 81 streams split into packets (one with the largest data field, 65536
  octets): no difference.
- R4 Every function returns its result or raises `ValueError`: a field that is not an integer in its range
  (booleans refused; the secondary header flag must be a bool), a header that is not 6 octets, a version other than
  0, an empty or oversized data field, a packet whose length disagrees with its header, a stream that ends inside a
  packet (the message says at which octet).

## Evidence
- Published: the header layout of CCSDS 133.0-B-2, written out by hand for four headers.
- `crosscheck_spacepacket.py`: spacepackets and ccsdspy.

## What is NOT claimed
The primary header and the packet boundary only: no secondary header format (time codes, PUS), no packet error
control, no segmentation or reassembly of user data across packets, no check that sequence counts are consecutive,
no transfer frames (see star_telemetry for extracting packets from frames). Idle packets (APID 2047) are returned
like any other packet. A stream with one damaged length field cannot be resynchronised here: it is refused.
Not affiliated with or endorsed by CCSDS; the standard is cited as the source of the layout.
