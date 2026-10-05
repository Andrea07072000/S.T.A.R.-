# star-telemetry

CCSDS AOS v2 / TM v1 transfer-frame deframer and Space Packet reassembler, with CUC time decoding via star-timescales.

## Requirements
- R1 `CcsdsTransferFrameEngine(frame_length, has_fecf).parse_frame(bytes) -> (header, data_field)`: TFVN, SCID, VCID,
  VC frame count, replay flag, first header pointer, FECF (CRC-16, poly 0x1021, init 0xFFFF) validity.
- R2 `process_raw_stream(bytes)` reassembles Space Packets across frames per virtual channel, including spanning packets.
- R3 A frame of the wrong length is rejected with `ValueError`; a corrupted frame is reported (`fecf_valid = False`),
  never silently accepted.
- Dependency: star-timescales >= 0.2.0 (CUC time codes), declared in pyproject.

## How it is verified
NASA F Prime native C++ test-harness frames (reproduced byte-for-byte), ccsdspy oracle on 1,030 packets, XC-005
(spacepackets, ccsdspy), 300 fault-injected frames, equivalence with the C port on 3 targets, `star verify`.

## Not supported / not claimed
TC frames, USLP, frame synchronisation/ASM search, Reed-Solomon, the F Prime flight AosFramer component as oracle
(test harness only), any flight qualification.
