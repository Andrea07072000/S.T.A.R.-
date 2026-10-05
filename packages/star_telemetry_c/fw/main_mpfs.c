/* Microchip PolarFire SoC (RV64: E51 monitor hart + 4 U54 harts; the architecture of the radiation-tolerant RT PolarFire
 * SoC) bare-metal firmware as modelled by Renode's mpfs-icicle-kit: same check as main.c, unchanged star_aos.c, run by
 * hart 0 only (start_mpfs.S parks the others), output on MMUART0, an NS16550 with 32-bit register stride at 0x20000000
 * (THR +0x00, LSR +0x14 bit5 = THR empty). Code/data/stack in DDR at 0x80000000. Simulated (no hardware/radiation claim). */
#include <stdint.h>
#include <stddef.h>
#include "star_aos.h"
#include "frames.h"

#define MMUART_THR (*(volatile uint32_t *)0x20000000u)
#define MMUART_LSR (*(volatile uint32_t *)0x20000014u)

static void putc_(char c) {
    while (!(MMUART_LSR & (1u << 5))) { }
    MMUART_THR = (uint32_t)(unsigned char)c;
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
