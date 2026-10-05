#!/bin/sh
# Build star_aos with libFuzzer + ASan + UBSan and fuzz for $1 seconds (default 120). Exit code != 0 = a finding.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
W="$(mktemp -d)"
clang-14 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=undefined \
  "$HERE/../src/star_aos.c" "$HERE/fuzz_aos.c" -I"$HERE/../src" -o "$W/fuzz_aos"
cd "$W"
./fuzz_aos -max_total_time="${1:-120}" -seed=20261004 2>&1 | tail -4
