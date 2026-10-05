#!/bin/sh
# Is the sparc64 crash in our code or in the emulator? A plain hello world, static, under qemu-sparc64.
cd "$(mktemp -d)" || exit 1
printf '#include <stdio.h>\nint main(void){puts("hi");return 0;}\n' > h.c
sparc64-linux-gnu-gcc -static h.c -o h64 && qemu-sparc64 ./h64; echo "hello static rc=$?"
sparc64-linux-gnu-gcc h.c -o h64d && qemu-sparc64 -L /usr/sparc64-linux-gnu ./h64d; echo "hello dynamic rc=$?"
qemu-sparc64 --version | head -1
