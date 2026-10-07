# star-telemetry

CCSDS AOS v2 / TM v1 transfer-frame deframer and Space Packet reassembler, with CUC time decoding via star-timescales.

## Requirements
- R1 `CcsdsTransferFrameEngine(frame_length, has_fecf).parse_frame(bytes) -> (header, data_field)`: TFVN, SCID, VCID,
  VC frame count, replay flag, first header pointer, FECF (CRC-16, poly 0x1021, init 0xFFFF) validity.
- R2 `process_raw_stream(bytes)` reassembles Space Packets across frames per virtual channel, including spanning packets.
  A packet is delivered in the frame that completes it. After a lost frame, the rest of the interrupted packet is
  discarded up to the next first header pointer. A pending packet whose size disagrees with its declared length is
  dropped, never cut to size.
- R3 A frame of the wrong length is rejected with `ValueError`; a corrupted frame is reported (`fecf_valid = False`),
  never silently accepted.
- Dependency: star-timescales >= 0.2.0 (CUC time codes), declared in pyproject.

## How it is verified
NASA F Prime native C++ test-harness frames (reproduced byte-for-byte), ccsdspy oracle on 1,030 packets, XC-005
(spacepackets, ccsdspy), 300 fault-injected frames, equivalence with the C port on 3 targets, `star verify`.

## Corrected in 0.2.7 (2026-10-07)
Three defects of packet reassembly, found by our own guard tests (`test_guards.py`) and present up to 0.2.6:
1. a packet ending exactly at the end of a frame that carries no packet start (first header pointer 2047) was lost;
2. after a lost frame, continuation data were kept and could then be delivered as a packet that was never sent;
3. an unfinished packet followed by a frame whose first header pointer is 0 stayed in the buffer and could be joined
   to octets of a later frame.
If you reassembled packets across frames with 0.2.6 or earlier, update. Frame header decoding was not affected.

## Not supported / not claimed
TC frames, USLP, frame synchronisation/ASM search, Reed-Solomon, the F Prime flight AosFramer component as oracle
(test harness only), any flight qualification.
