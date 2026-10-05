/* SiFive FE310 (HiFive1) as modelled by Renode: XIP flash at 0x20000000, 16 KiB DTIM at 0x80000000. */
/* ALIGN(4) (2026-10-05): .data's load address followed 16-bit compressed code (0x20000B22) and the word copy in
 * c_start trapped on the misaligned load (the real FE310 traps too) -- the cause of the FE310 failure. */
ENTRY(_start)
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x20000000, LENGTH = 4M
  RAM   (rwx) : ORIGIN = 0x80000000, LENGTH = 16K
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS
{
  .text : { *(.text.start) *(.text*) *(.rodata*) *(.srodata*) . = ALIGN(4); } > FLASH
  _sidata = LOADADDR(.data);
  .data : ALIGN(4) { _sdata = .; *(.data*) *(.sdata*) _edata = .; } > RAM AT > FLASH
  .bss : ALIGN(4) { _sbss = .; *(.bss*) *(.sbss*) *(COMMON) _ebss = .; } > RAM
}
