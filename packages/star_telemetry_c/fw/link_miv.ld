/* Microchip Mi-V as modelled by Renode's miv-board (platforms/cpus/miv.repl): 64 MiB DDR at 0x80000000 holds code, data
 * and stack (ELF loaded directly). NB: 0x40000000 is the PLIC on this board (first attempt wrote the ELF into it). */
/* ALIGN(4) (2026-10-05): .data's load address followed 16-bit compressed code (0x20000B22) and the word copy in
 * c_start trapped on the misaligned load (the real FE310 traps too) -- the cause of the FE310 failure. */
ENTRY(_start)
MEMORY
{
  RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 64M
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS
{
  .text : { *(.text.start) *(.text*) *(.rodata*) *(.srodata*) . = ALIGN(4); } > RAM
  _sidata = LOADADDR(.data);
  .data : ALIGN(4) { _sdata = .; *(.data*) *(.sdata*) _edata = .; } > RAM
  .bss : ALIGN(4) { _sbss = .; *(.bss*) *(.sbss*) *(COMMON) _ebss = .; } > RAM
}
