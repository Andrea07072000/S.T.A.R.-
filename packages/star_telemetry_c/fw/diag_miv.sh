#!/bin/sh
# Diagnose the Mi-V run: leftover Renode processes (listed by exact name, never killed by pattern), log tail, UART output,
# and the ELF entry / sections.
ps -eo pid,etimes,comm | awk '$3 ~ /^(renode|Renode|mono)$/'
echo "--- miv.log tail"; tail -15 /root/star_fw/miv.log 2>/dev/null
echo "--- uart"; head -c 300 /root/star_fw/miv_uart.txt 2>/dev/null; echo
echo "--- elf"; riscv64-linux-gnu-readelf -h /root/star_fw/star_aos_miv.elf | grep -E "Entry|Class|Machine"
riscv64-linux-gnu-readelf -lW /root/star_fw/star_aos_miv.elf | grep -E "LOAD"
