/* STM32F746 (Cortex-M7, USART v2 register layout) variant of main.c, generated 2026-10-05 -- same check.
 * Bare-metal firmware for STM32F407 (Cortex-M4): runs the S.T.A.R. AOS/TM frame check (star_aos.c, unchanged) on the
 * 5 NASA F Prime native frames embedded in flash, plus a corrupted copy of frame 0, and prints one line per frame on
 * USART2 in the same field order as host_main.c. No libc, no heap, no OS. Simulated in Renode (no hardware). */
#include <stdint.h>
#include <stddef.h>
#include "star_aos.h"
#include "frames.h"   /* generated: const unsigned char fprime_native_frames_bin[]; unsigned int ..._len */

/* USART1 at 0x40011000, v2 layout: CR1 +0x00 (UE bit0, TE bit3), ISR +0x1C (TXE bit7), TDR +0x28 */
#define USART2_CR1 (*(volatile uint32_t *)0x40011000u)
#define USART2_SR (*(volatile uint32_t *)0x4001101Cu)
#define USART2_DR (*(volatile uint32_t *)0x40011028u)
#define DWT_CTRL (*(volatile uint32_t *)0xE0001000u)
#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004u)
#define DEMCR (*(volatile uint32_t *)0xE000EDFCu)

static void putc_(char c) {
    while (!(USART2_SR & (1u << 7))) { }   /* TXE */
    USART2_DR = (uint32_t)(unsigned char)c;
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
    USART2_CR1 = (1u << 0) | (1u << 3);    /* UE | TE (v2 layout) */
    DEMCR |= (1u << 24);                   /* trace enable for DWT cycle counter */
    DWT_CYCCNT = 0; DWT_CTRL |= 1u;
    const int len[5] = {256, 256, 256, 256, 254}, fecf[5] = {1, 1, 1, 1, 0};
    size_t off = 0;
    for (int i = 0; i < 6; i++) {
        const unsigned char *f;
        int L, F;
        if (i < 5) { f = fprime_native_frames_bin + off; L = len[i]; F = fecf[i]; off += (size_t)L; }
        else {      /* frame 0 with one bit flipped in the data field: must be rejected by the FECF */
            for (int k = 0; k < 256; k++) corrupted[k] = fprime_native_frames_bin[k];
            corrupted[100] ^= 0x01; f = corrupted; L = 256; F = 1;
        }
        star_aos_header_t h;
        uint32_t c0 = DWT_CYCCNT;
        int rc = star_aos_parse(f, (size_t)L, F, &h);
        uint32_t cyc = DWT_CYCCNT - c0;
        putc_('{'); field("index", (uint32_t)i, 0);
        if (rc) { field("error", (uint32_t)(-rc), 1); puts_("}\r\n"); continue; }
        field("tfvn", h.tfvn, 0); field("scid", h.scid, 0); field("vcid", h.vcid, 0); field("vcfc", h.vcfc, 0);
        field("replay", h.replay, 0); field("fhp", h.fhp, 0); field("fecf_valid", h.fecf_valid, 0);
        field("fecf_received", h.fecf_received, 0); field("fecf_computed", h.fecf_computed, 0);
        field("data_len", (uint32_t)h.data_len, 0); field("cycles", cyc, 1);
        puts_("}\r\n");
    }
    puts_("DONE\r\n");
    for (;;) { }
}

/* --- minimal startup: vector table, .data copy, .bss clear --- */
extern uint32_t _estack, _sidata, _sdata, _edata, _sbss, _ebss;
void Reset_Handler(void) {
    uint32_t *s = &_sidata, *d = &_sdata;
    while (d < &_edata) *d++ = *s++;
    for (d = &_sbss; d < &_ebss; ) *d++ = 0;
    main();
    for (;;) { }
}
void Default_Handler(void) { for (;;) { } }
__attribute__((section(".isr_vector"), used))
static void (*const vectors[16])(void) = {
    (void (*)(void))(&_estack), Reset_Handler, Default_Handler, Default_Handler, Default_Handler, Default_Handler,
    Default_Handler, 0, 0, 0, 0, Default_Handler, Default_Handler, 0, Default_Handler, Default_Handler,
};
