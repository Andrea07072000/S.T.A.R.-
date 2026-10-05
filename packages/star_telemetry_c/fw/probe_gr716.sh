#!/bin/sh
# Which BCC2 flag sets link a trivial program for the GR716 BSP? (diagnosis of 'cannot open linker script file linkcmds')
cd "$(mktemp -d)" || exit 1
printf 'int main(void){return 0;}\n' > g.c
G=/opt/bcc-2.2.4-gcc/bin/sparc-gaisler-elf-gcc
for f in "-qbsp=gr716 -mcpu=leon3" "-qbsp=gr716 -mcpu=leon3 -qsvt" "-qbsp=gr716 -mcpu=leon3 -mfix-gr712rc" \
         "-qbsp=gr716" "-qbsp=gr716b -mcpu=leon3" "-qbsp=gr716 -mcpu=leon3 -qnano"; do
  if $G $f g.c -o g.elf > err.txt 2>&1; then echo "OK   $f"; else echo "FAIL $f: $(tail -1 err.txt | cut -c1-120)"; fi
done
$G -qbsp=gr716 -mcpu=leon3 -print-multi-directory
ls /opt/bcc-2.2.4-gcc/sparc-gaisler-elf/bsp/gr716/leon3 | head
