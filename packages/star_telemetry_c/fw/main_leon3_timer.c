#include <stdint.h>
#include <bcc/bcc.h>
#include <bcc/regs/gptimer.h>

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

static void puts_(const char *s) {
    while (*s) putc_(*s++);
}

static void putu(uint32_t v) {
    char b[11];
    int i = 10;
    b[i] = 0;
    if (v == 0) b[--i] = '0';
    while (v) {
        b[--i] = (char)('0' + v % 10u);
        v /= 10u;
    }
    puts_(&b[i]);
}

static volatile uint32_t tick_count = 0;

static void timer_isr(void *arg, int source) {
    (void)arg;
    (void)source;
    tick_count++;
    volatile struct gptimer_regs *gpt = (volatile struct gptimer_regs *)0x80000300;
    /* Clear pending interrupt in GPTimer */
    gpt->timer[0].ctrl |= GPTIMER_CTRL_IP;
}

int main(void) {
    APBUART_CTRL |= (1u << 1);

    /* Register timer interrupt on IRQ 8 */
    bcc_isr_register(8, timer_isr, 0);
    bcc_int_unmask(8);
    bcc_set_pil(0);

    volatile struct gptimer_regs *gpt = (volatile struct gptimer_regs *)0x80000300;
    /* Prescaler: 50 MHz / 50 = 1 MHz */
    gpt->scaler_reload = 49;
    gpt->scaler_value = 49;

    /* Subtimer 0: 1 MHz / 10,000 = 100 Hz */
    gpt->timer[0].reload = 9999;
    gpt->timer[0].counter = 9999;
    /* Enable, Restart, Load, Interrupt Enable */
    gpt->timer[0].ctrl = GPTIMER_CTRL_EN | GPTIMER_CTRL_RS | GPTIMER_CTRL_LD | GPTIMER_CTRL_IE;

    /* Wait until tick_count reaches at least 180 ticks (approx 1.8 s) */
    while (tick_count < 180) { }

    putc_('{');
    puts_("\"target\":\"leon3\",\"timer\":\"gptimer\",\"ticks\":");
    putu(tick_count);
    puts_("}\r\nDONE\r\n");

    for (;;) { }
    return 0;
}
