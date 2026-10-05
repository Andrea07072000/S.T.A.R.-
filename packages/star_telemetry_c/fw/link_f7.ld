/* STM32F746 (Renode stm32f7_discovery-bb): 1 MiB flash at 0x08000000, 320 KiB SRAM at 0x20000000 (128K used) */
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS
{
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
  .text : { *(.text*) *(.rodata*) . = ALIGN(4); } > FLASH
  _sidata = LOADADDR(.data);
  .data : ALIGN(4) { _sdata = .; *(.data*) _edata = .; } > RAM AT > FLASH
  .bss : ALIGN(4) { _sbss = .; *(.bss*) *(COMMON) _ebss = .; } > RAM
}
