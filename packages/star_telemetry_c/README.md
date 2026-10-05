# star_aos — CCSDS AOS/TM transfer-frame check in C99 (S.T.A.R.)

Embedded-oriented decoder of CCSDS AOS v2 (CCSDS 732.0-B) and TM v1 (CCSDS 132.0-B) transfer-frame primary headers with
FECF CRC-16/CCITT verification. No heap, no stdio in the core (`src/star_aos.c`, `src/star_aos.h`), fixed-width types,
byte-wise access (endianness-independent).

## Requirements
- R1 `star_aos_parse(frame, len, has_fecf, &hdr)`: TFVN, SCID, VCID, VC frame count, replay (AOS), FHP; TM: VC count
  from octet 3, OCF flag (4 octets before the FECF), secondary header skipped (length from its ID octet).
- R2 FECF: CRC-16/CCITT-FALSE over the frame without the FECF; `fecf_valid` only when computed == received.
- R3 Exact layout: `data_offset + data_len + ocf_len (+2 with FECF) == len`; TM data offset 6 or 7 + (ID & 0x3F).
- R4 Errors: NULL inputs -> `STAR_AOS_ERR_NULL`; frames too short for the declared layout -> `STAR_AOS_ERR_SHORT`;
  never a read outside `[frame, frame + len)`.
- R5 Portability: identical results on every target listed below (byte-wise parsing, no undefined behaviour).

## How it is verified
- Host/ISA bench `test_c_vs_python.py`: 305 AOS frames (5 NASA F Prime native + 300 bit-flipped) field-by-field equal to
  the Python reference on 18 ISAs under qemu-user (LE/BE, 32/64-bit).
- Bare-metal firmware on 12 Renode platforms: STM32F4, STM32F103, STM32F746, LEON3, GR712RC, GR716, Mi-V, PolarFire
  SoC, FE310, Cortex-R52, Cortex-R8, Zynq-7000. One run: 30 passed (`12_EVIDENCE/hw/hw_targets_30_run_20261005.txt`).
- Independent lineage: `star_audit/ccsds_audit` — 40/40 valid TM frames field-exact and 260/260 corrupted frames
  rejected, 0 disagreements with spacepackets.
- libFuzzer + ASan + UBSan with exact invariants (`fuzz/`): 12.0 M inputs clean after the TM fix.
- Mutation (`c_mutation.py`, double oracle AOS + TM): 146/162 = 0.9012.

## Not claimed
No timing (DWT is not modelled), no radiation behaviour, no flight heritage; simulated and emulated targets only.
Defects found by this verification and fixed: TM VC count read from the master-channel octet, OCF read as "replay",
OCF and secondary header left in the data (2026-10-04).
