/* RISC-V reset entry: set the stack pointer at the top of the DTIM and jump to C. */
    .section .text.start
    .globl _start
_start:
    lla sp, _estack   /* lla: PC-relative; 'la' became a GOT load from not-yet-copied .data under the default PIE */
    call c_start
1:  j 1b
