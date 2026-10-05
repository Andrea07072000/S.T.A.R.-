/* Arm Cortex-R52 (ARMv8-R AArch32, the real-time core family of space/avionics and automotive safety SoCs) bare-metal
 * firmware as modelled by Renode's platforms/cpus/cortex-r52.repl: same check as main.c, unchanged star_aos.c, output on
 * the PL011 UART at 0x9C090000 (DR +0x00, FR +0x18 bit5 = TX FIFO full). Code/data/stack in DRAM at 0x0.
 * Simulated in Renode (no hardware, no timing claim). */
#include <stdint.h>
#include <stddef.h>
#include "star_aos.h"
#include "frames.h"

#define PL011_DR (*(volatile uint32_t *)0x9C090000u)
#define PL011_FR (*(volatile uint32_t *)0x9C090018u)
#define PL011_CR (*(volatile uint32_t *)0x9C090030u)   /* bit0 UARTEN, bit8 TXE: the model refuses DR writes until set */

static void putc_(char c) {
    while (PL011_FR & (1u << 5)) { }
    PL011_DR = (uint32_t)(unsigned char)c;
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
    PL011_CR = (1u << 0) | (1u << 8);
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
