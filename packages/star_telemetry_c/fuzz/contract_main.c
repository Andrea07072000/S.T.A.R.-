/* contract_main.c - deterministic driver for the fuzz invariants (S.T.A.R., Apache-2.0).
 * Runs LLVMFuzzerTestOneInput (fuzz_aos.c) on every frame of a corpus file AND on every truncation of it, each copied
 * into a heap buffer of exactly that size, so AddressSanitizer reports any read past the end. Then checks the explicit
 * error contract and the published CRC-16/CCITT-FALSE check value. Built with -fsanitize=address,undefined; any
 * violation aborts (exit != 0). Corpus format: repeated [u32 little-endian length][frame bytes].
 * Usage: contract <corpus.bin>   Prints "CONTRACT OK <inputs>" on success. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "star_aos.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

static void run_exact(const uint8_t *src, size_t n) {
    uint8_t *buf = (uint8_t *)malloc(n ? n : 1u);
    if (!buf) abort();
    if (n) memcpy(buf, src, n);
    (void)LLVMFuzzerTestOneInput(buf, n);
    free(buf);
}

int main(int argc, char **argv) {
    static const uint8_t check[] = "123456789";
    star_aos_header_t h;
    uint8_t one = 0;
    unsigned long inputs = 0;
    FILE *f;
    if (argc != 2) return 2;
    /* R2: published check value of CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over "123456789" is 0x29B1 */
    if (star_crc16_ccitt(check, 9) != 0x29B1u) { puts("FAIL crc check value"); return 1; }
    /* R4: NULL frame or NULL output -> STAR_AOS_ERR_NULL; empty or 1-octet frame -> STAR_AOS_ERR_SHORT */
    if (star_aos_parse(NULL, 64, 1, &h) != STAR_AOS_ERR_NULL) { puts("FAIL null frame"); return 1; }
    if (star_aos_parse(&one, 1, 1, NULL) != STAR_AOS_ERR_NULL) { puts("FAIL null out"); return 1; }
    if (star_aos_parse(&one, 0, 0, &h) != STAR_AOS_ERR_SHORT) { puts("FAIL empty"); return 1; }
    if (star_aos_parse(&one, 1, 0, &h) != STAR_AOS_ERR_SHORT) { puts("FAIL one octet"); return 1; }
    f = fopen(argv[1], "rb");
    if (!f) return 2;
    for (;;) {
        uint8_t lb[4];
        size_t len, k;
        uint8_t *frame;
        if (fread(lb, 1, 4, f) != 4) break;
        len = (size_t)lb[0] | ((size_t)lb[1] << 8) | ((size_t)lb[2] << 16) | ((size_t)lb[3] << 24);
        frame = (uint8_t *)malloc(len ? len : 1u);
        if (!frame || fread(frame, 1, len, f) != len) return 2;
        for (k = 0; k <= len; k++) { run_exact(frame, k); inputs++; } /* R3/R4 on the frame and all its truncations */
        free(frame);
    }
    fclose(f);
    printf("CONTRACT OK %lu\n", inputs);
    return 0;
}
