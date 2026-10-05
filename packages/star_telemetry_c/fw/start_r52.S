/* Cortex-R52 (AArch32) reset entry: stack at the top of the first 1 MiB of DRAM, then C. ARM state. */
    .syntax unified
    .arm
    .section .text.start
    .globl _start
_start:
    ldr sp, =_estack
    bl c_start
1:  b 1b
