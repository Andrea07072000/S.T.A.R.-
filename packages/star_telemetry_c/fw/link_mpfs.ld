/* Renode polarfire-soc.repl: DDR at 0x80000000; the firmware uses the first MiB. */
/* ALIGN(4) (2026-10-05): .data's load address followed 16-bit compressed code (0x20000B22) and the word copy in
 * c_start trapped on the misaligned load (the real FE310 traps too) -- the cause of the FE310 failure. */
ENTRY(_start)
MEMORY
{
  RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 1M
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS
{
  .text : { *(.text.start) *(.text*) *(.rodata*) *(.srodata*) . = ALIGN(4); } > RAM
  _sidata = LOADADDR(.data);
  .data : ALIGN(4) { _sdata = .; *(.data*) *(.sdata*) _edata = .; } > RAM
  .bss : ALIGN(4) { _sbss = .; *(.bss*) *(.sbss*) *(COMMON) _ebss = .; } > RAM
}
