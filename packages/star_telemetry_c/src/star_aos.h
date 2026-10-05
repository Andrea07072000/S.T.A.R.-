/* star_aos.h - CCSDS AOS/TM transfer frame primary header + FECF check (S.T.A.R., Apache-2.0).
 * Embedded-oriented: no heap, no stdio, fixed-width integers, single pass. Mirrors star_telemetry.engine.parse_frame. */
#ifndef STAR_AOS_H
#define STAR_AOS_H
#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint8_t tfvn;       /* 0 = TM v1, 1 = AOS v2 */
    uint16_t scid;
    uint8_t vcid;
    uint32_t vcfc;
    uint8_t replay;
    uint16_t fhp;       /* first header pointer (11 bits) */
    uint8_t fecf_valid; /* 1 if CRC matches or no FECF */
    uint16_t fecf_received;
    uint16_t fecf_computed;
    size_t data_offset;
    size_t data_len;
    size_t ocf_len;      /* 4 when a TM frame carries an Operational Control Field before the FECF, else 0 */
} star_aos_header_t;

enum { STAR_AOS_OK = 0, STAR_AOS_ERR_NULL = -1, STAR_AOS_ERR_SHORT = -2 };

uint16_t star_crc16_ccitt(const uint8_t *data, size_t len);
int star_aos_parse(const uint8_t *frame, size_t len, int has_fecf, star_aos_header_t *out);
#endif
