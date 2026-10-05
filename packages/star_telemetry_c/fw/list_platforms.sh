#!/bin/sh
# List Renode platform descriptions relevant to spacecraft processors (where the installed Renode keeps them).
R=$(dirname "$(readlink -f "$(command -v renode)")")
for d in "$R/platforms" "$R/../platforms" /opt/renode/platforms /usr/lib/renode/platforms; do
  [ -d "$d" ] && { echo "dir: $d"; find "$d" -name '*.repl' | grep -i -E 'polarfire|icicle|leon|gr7|zynq|stm32l4|stm32f7|tms570|cortex-r|sam[ev]7|kv260|versal|rv32|litex' | sed "s|$d/||" | sort | head -40; break; }
done
