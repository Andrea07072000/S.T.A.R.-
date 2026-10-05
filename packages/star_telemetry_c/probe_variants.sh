#!/bin/sh
# Which ISA/ABI/endianness variants can be built as static hosted binaries with the installed cross compilers, and run
# under qemu-user? Prints one line per variant: name BUILD_OK|BUILD_FAIL RUN_OK|RUN_FAIL.
cd "$(mktemp -d)" || exit 1
printf '#include <stdio.h>\nint main(void){unsigned x=1;printf("%%s\\n", *(unsigned char*)&x ? "LE" : "BE");return 0;}\n' > h.c
try() {
  name=$1; cc=$2; run=$3
  if sh -c "$cc -static h.c -o $name" 2>/dev/null; then
    out=$(sh -c "$run ./$name" 2>/dev/null) && echo "$name BUILD_OK RUN_OK $out" || echo "$name BUILD_OK RUN_FAIL"
  else
    echo "$name BUILD_FAIL"
  fi
}
try i386 "x86_64-linux-gnu-gcc -m32" "qemu-i386 -B 0x100000000"
try mips64 "mips-linux-gnu-gcc -mabi=64" "qemu-mips64"
try mipsn32 "mips-linux-gnu-gcc -mabi=n32" "qemu-mipsn32 -B 0x100000000"
try mips64el "mipsel-linux-gnu-gcc -mabi=64" "qemu-mips64el"
try riscv32 "riscv64-linux-gnu-gcc -march=rv32imac -mabi=ilp32" "qemu-riscv32 -B 0x100000000"
try ppc64be "powerpc64le-linux-gnu-gcc -mbig-endian" "qemu-ppc64"
try ppc64be_b "powerpc-linux-gnu-gcc -m64" "qemu-ppc64"
try aarch64_be "aarch64-linux-gnu-gcc -mbig-endian" "qemu-aarch64_be"
try armeb "arm-linux-gnueabihf-gcc -mbig-endian" "qemu-armeb -B 0x100000000"
try x32 "x86_64-linux-gnu-gcc -mx32" "qemu-x86_64"
