/* PolarFire SoC entry: every hart starts here; hart 0 runs the check, harts 1..4 park in wfi. */
    .section .text.start
    .globl _start
_start:
    csrr t0, mhartid
    bnez t0, 2f
    lla sp, _estack
    call c_start
1:  j 1b
2:  wfi
    j 2b
