/* LEON3 (SPARC V8, the ESA/Gaisler space processor) firmware: same check as main.c (STM32F4), unchanged star_aos.c,
 * built with Gaisler BCC2 (-qbsp=leon3 provides reset/trap table), output written directly to the GRLIB APBUART at
 * 0x80000100 (data +0x0, status +0x4 bit2 = TX FIFO empty, control +0x8 bit1 = TX enable). Big-endian target:
 * the frame parser reads bytes, so endianness must not change any field. Simulated in Renode (no hardware). */
#include <stdint.h>
#include <stddef.h>
#include "star_aos.h"
#include "frames.h"

/* APBUART base: 0x80000100 on LEON3 and GR712RC; 0x80300000 on GR716 (-DSTAR_APBUART_BASE=0x80300000u) */
#ifndef STAR_APBUART_BASE
#define STAR_APBUART_BASE 0x80000100u
#endif
#define APBUART_DATA (*(volatile uint32_t *)(STAR_APBUART_BASE + 0x0u))
#define APBUART_STAT (*(volatile uint32_t *)(STAR_APBUART_BASE + 0x4u))
#define APBUART_CTRL (*(volatile uint32_t *)(STAR_APBUART_BASE + 0x8u))

static void putc_(char c) {
    while (!(APBUART_STAT & (1u << 2))) { }
    APBUART_DATA = (uint32_t)(unsigned char)c;
}
static void puts_(const char *s) { while (*s) putc_(*s++); }
static void putu(uint32_t v) {
    char b[11]; int i = 10; b[i] = 0;
    if (v == 0) b[--i] = '0';
    while (v) { b[--i] = (char)('0' + v % 10u); v /= 10u; }
    puts_(&b[i]);
}
static void field(const char *k, uint32_t v, int last) {
    putc_('"'); puts_(k); puts_("\":"); putu(v); if (!last) putc_(',');
}

static unsigned char corrupted[256];

int main(void) {
    APBUART_CTRL |= (1u << 1);
    const int len[5] = {256, 256, 256, 256, 254}, fecf[5] = {1, 1, 1, 1, 0};
    size_t off = 0;
    for (int i = 0; i < 6; i++) {
        const unsigned char *f;
        int L, F;
        if (i < 5) { f = fprime_native_frames_bin + off; L = len[i]; F = fecf[i]; off += (size_t)L; }
        else {
            for (int k = 0; k < 256; k++) corrupted[k] = fprime_native_frames_bin[k];
            corrupted[100] ^= 0x01; f = corrupted; L = 256; F = 1;
        }
        star_aos_header_t h;
        int rc = star_aos_parse(f, (size_t)L, F, &h);
        putc_('{'); field("index", (uint32_t)i, 0);
        if (rc) { field("error", (uint32_t)(-rc), 1); puts_("}\r\n"); continue; }
        field("tfvn", h.tfvn, 0); field("scid", h.scid, 0); field("vcid", h.vcid, 0); field("vcfc", h.vcfc, 0);
        field("replay", h.replay, 0); field("fhp", h.fhp, 0); field("fecf_valid", h.fecf_valid, 0);
        field("fecf_received", h.fecf_received, 0); field("fecf_computed", h.fecf_computed, 0);
        field("data_len", (uint32_t)h.data_len, 1);
        puts_("}\r\n");
    }
    puts_("DONE\r\n");
    for (;;) { }
    return 0;
}
