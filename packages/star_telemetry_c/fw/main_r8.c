/* Arm Cortex-R8 (ARMv7-R, the real-time processing unit of Xilinx Zynq UltraScale+ class SoCs used in space payloads)
 * bare-metal firmware as modelled by Renode's platforms/cpus/cortex-r8.repl: same check as main.c, unchanged star_aos.c,
 * output on the Cadence UART at 0xFF010000 (CR +0x00 bit4 = TXEN, SR +0x2C bit4 = TX FIFO full, FIFO +0x30).
 * Code/data/stack in RAM at 0x0. Simulated in Renode (no hardware, no timing claim). */
#include <stdint.h>
#include <stddef.h>
#include "star_aos.h"
#include "frames.h"

/* Cadence UART base: 0xFF010000 on the Cortex-R8 model, 0xE0000000 on Zynq-7000 (-DSTAR_CDNS_BASE=0xE0000000u) */
#ifndef STAR_CDNS_BASE
#define STAR_CDNS_BASE 0xFF010000u
#endif
#define CDNS_CR   (*(volatile uint32_t *)(STAR_CDNS_BASE + 0x00u))
#define CDNS_SR   (*(volatile uint32_t *)(STAR_CDNS_BASE + 0x2Cu))
#define CDNS_FIFO (*(volatile uint32_t *)(STAR_CDNS_BASE + 0x30u))

static void putc_(char c) {
    while (CDNS_SR & (1u << 4)) { }
    CDNS_FIFO = (uint32_t)(unsigned char)c;
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
    CDNS_CR = (1u << 4);     /* TXEN */
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

extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;
void c_start(void) {
    uint32_t *s = &_sidata, *d = &_sdata;
    while (d < &_edata) *d++ = *s++;
    for (d = &_sbss; d < &_ebss; ) *d++ = 0;
    main();
    for (;;) { }
}
