#!/bin/sh
# Rebuild the fuzz target and replay one input given as base64 ($1); prints the sanitizer/assertion report.
HERE="$(cd "$(dirname "$0")" && pwd)"
W="$(mktemp -d)"
clang-14 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=undefined \
  "$HERE/../src/star_aos.c" "$HERE/fuzz_aos.c" -I"$HERE/../src" -o "$W/fuzz_aos"
echo "$1" | base64 -d > "$W/input"
"$W/fuzz_aos" "$W/input" 2>&1 | grep -v "^INFO" | head -20
