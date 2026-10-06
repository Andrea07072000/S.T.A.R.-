#include <stdint.h>

#define USART2_SR (*(volatile uint32_t *)0x40004400u)
#define USART2_DR (*(volatile uint32_t *)0x40004404u)
#define USART2_CR1 (*(volatile uint32_t *)0x4000440Cu)

#define SYST_CSR (*(volatile uint32_t *)0xE000E010u)
#define SYST_RVR (*(volatile uint32_t *)0xE000E014u)
#define SYST_CVR (*(volatile uint32_t *)0xE000E018u)

static volatile uint32_t tick_count = 0;

static void putc_(char c) {
    while (!(USART2_SR & (1u << 7))) { }
    USART2_DR = (uint32_t)(unsigned char)c;
}
static void puts_(const char *s) { while (*s) putc_(*s++); }
static void putu(uint32_t v) {
    char b[11]; int i = 10; b[i] = 0;
    if (v == 0) b[--i] = '0';
    while (v) { b[--i] = (char)('0' + v % 10u); v /= 10u; }
    puts_(&b[i]);
}

void SysTick_Handler(void) {
    tick_count++;
}

int main(void) {
    USART2_CR1 = (1u << 13) | (1u << 3); /* UE | TE */

    /* systickFrequency in stm32f4.repl: 72000000 */
    /* 100 Hz timer tick: 72000000 / 100 = 720000 */
    SYST_RVR = 720000 - 1;
    SYST_CVR = 0;
    SYST_CSR = (1u << 0) | (1u << 1) | (1u << 2);

    /* Renode run_stm32f4.resc runs for 2 seconds */
    /* Wait in a loop until tick_count reaches at least 150 (approx 1.5 - 2.0 s) or timeout */
    while (tick_count < 180) { }

    putc_('{');
    puts_("\"target\":\"stm32f4\",\"timer\":\"systick\",\"ticks\":");
    putu(tick_count);
    puts_("}\r\nDONE\r\n");

    for (;;) { }
}

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
    (void (*)(void))(&_estack), Reset_Handler, Default_Handler, Default_Handler,
    Default_Handler, Default_Handler, Default_Handler, 0,
    0, 0, 0, Default_Handler,
    Default_Handler, 0, Default_Handler, SysTick_Handler
};
