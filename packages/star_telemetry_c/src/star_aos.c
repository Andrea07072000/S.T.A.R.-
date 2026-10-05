/* star_aos.c - see star_aos.h. CRC: CCSDS 131.0-B / 132.0-B FECF, polynomial 0x1021, initial value 0xFFFF. */
#include "star_aos.h"

uint16_t star_crc16_ccitt(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)((uint16_t)data[i] << 8);
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}

int star_aos_parse(const uint8_t *f, size_t len, int has_fecf, star_aos_header_t *o) {
    if (!f || !o) return STAR_AOS_ERR_NULL;
    size_t fecf_len = has_fecf ? 2u : 0u;
    if (len < 8u + fecf_len) return STAR_AOS_ERR_SHORT;
    o->fecf_valid = 1; o->fecf_received = 0; o->fecf_computed = 0;
    if (has_fecf) {
        o->fecf_computed = star_crc16_ccitt(f, len - 2u);
        o->fecf_received = (uint16_t)((f[len - 2u] << 8) | f[len - 1u]);
        o->fecf_valid = (uint8_t)(o->fecf_computed == o->fecf_received);
    }
    uint16_t w1 = (uint16_t)((f[0] << 8) | f[1]);
    o->tfvn = (uint8_t)((w1 >> 14) & 0x03u);
    size_t hdr, ocf_len = 0u;
    if (o->tfvn == 0) {                       /* TM v1 (CCSDS 132.0-B) */
        /* octet 2 = master channel count, octet 3 = VC count; bit 0 of w1 = OCF flag (no replay flag in TM).
         * Fixed 2026-10-04: octet 2 was read as the VC count and the OCF flag as 'replay' (same defect as the Python
         * reference it was ported from; found by cross-checking with spacepackets). */
        uint16_t status = (uint16_t)((f[4] << 8) | f[5]);
        o->scid = (uint16_t)((w1 >> 4) & 0x03FFu);
        o->vcid = (uint8_t)((w1 >> 1) & 0x07u);
        o->replay = 0u;
        ocf_len = (w1 & 0x01u) ? 4u : 0u;
        o->vcfc = f[3];
        o->fhp = (uint16_t)(status & 0x07FFu);
        hdr = 6u;
        if (status & 0x8000u) {               /* secondary header: ID octet low 6 bits = total length - 1 */
            if (len < 7u) return STAR_AOS_ERR_SHORT;
            hdr += (size_t)(f[6] & 0x3Fu) + 1u;
        }
        if (len < hdr + ocf_len + fecf_len) return STAR_AOS_ERR_SHORT;
    } else {                                  /* AOS v2 (CCSDS 732.0-B) */
        o->scid = (uint16_t)((w1 >> 6) & 0x00FFu);
        o->vcid = (uint8_t)(w1 & 0x3Fu);
        o->vcfc = ((uint32_t)f[2] << 16) | ((uint32_t)f[3] << 8) | f[4];
        o->replay = (uint8_t)((f[5] >> 7) & 1u);
        o->fhp = (uint16_t)(((f[6] << 8) | f[7]) & 0x07FFu);
        hdr = 8u;
    }
    o->data_offset = hdr;
    o->data_len = len - hdr - ocf_len - fecf_len;
    o->ocf_len = ocf_len;
    return STAR_AOS_OK;
}
