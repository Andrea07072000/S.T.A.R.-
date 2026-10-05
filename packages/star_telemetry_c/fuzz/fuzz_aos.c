/* libFuzzer harness for star_aos_parse (S.T.A.R. C3: test like an attacker, for the good of the code).
 * Any byte string, any length, with and without FECF: the parser must never crash, read out of bounds or hit undefined
 * behaviour (AddressSanitizer + UndefinedBehaviorSanitizer abort the run if it does), and its outputs must stay
 * self-consistent: data_offset + data_len (+2 with FECF) == length, fecf_valid only when the CRCs are equal. */
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include "star_aos.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    for (int fecf = 0; fecf <= 1; fecf++) {
        star_aos_header_t h;
        int rc = star_aos_parse(data, size, fecf, &h);
        if (rc == STAR_AOS_OK) {
            size_t total = h.data_offset + h.data_len + h.ocf_len + (fecf ? 2u : 0u);
            if (total != size) abort();
            /* AOS: 8-octet header. TM: 6, or 6 + secondary header of 1..64 octets (2026-10-04, TM v1 support) */
            if (h.tfvn == 0) {
                size_t expect = (data[4] & 0x80u) ? 7u + (size_t)(data[6] & 0x3Fu) : 6u;
                if (h.data_offset != expect) abort();
                if (h.ocf_len != ((data[1] & 0x01u) ? 4u : 0u)) abort();
            } else if (h.data_offset != 8u || h.ocf_len != 0u) {
                abort();
            }
            if (fecf && h.fecf_valid != (h.fecf_computed == h.fecf_received)) abort();
            if (!fecf && !h.fecf_valid) abort();
            if (h.fhp > 0x07FFu) abort();
        } else if (rc != STAR_AOS_ERR_SHORT) {
            abort();                       /* data is never NULL here: only "too short" is a legal error */
        }
    }
    (void)star_aos_parse(NULL, size, 0, NULL); /* NULL inputs must be refused, not dereferenced */
    return 0;
}
