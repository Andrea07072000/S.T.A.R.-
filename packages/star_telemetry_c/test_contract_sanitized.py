# -*- coding: utf-8 -*-
"""Contract of the C frame check under AddressSanitizer + UndefinedBehaviorSanitizer, as a normal test (until now these
invariants were checked only by the libFuzzer harness, outside pytest and outside CI).
Verifies: R2, R3, R4 (README).

The deterministic driver fuzz/contract_main.c runs the fuzz invariants of fuzz/fuzz_aos.c on the 305 frames of the
equivalence corpus (5 NASA F Prime frames + 300 corrupted copies) AND on every truncation of each frame, each in a heap
buffer of exactly its size (any read past the end is an ASan error). It also checks the error codes for NULL and short
inputs and the published CRC-16/CCITT-FALSE check value 0x29B1 over "123456789".
The test is itself checked: three planted defects (a weakened length guard, a missing NULL check, a wrong CRC initial
value) must each make the contract FAIL."""
import shutil
import struct

import pytest

from test_c_vs_python import HERE, stream, wsl, wsl_path

MUTANTS = {
    "short_guard": ("if (len < 8u + fecf_len) return STAR_AOS_ERR_SHORT;", "if (len < 6u + fecf_len) return STAR_AOS_ERR_SHORT;"),
    "null_out": ("if (!f || !o) return STAR_AOS_ERR_NULL;", "if (!f) return STAR_AOS_ERR_NULL;"),
    "crc_init": ("uint16_t crc = 0xFFFFu;", "uint16_t crc = 0x0000u;"),
}


@pytest.fixture(scope="module")
def corpus_file(tmp_path_factory):
    if not shutil.which("bash") and not shutil.which("wsl.exe"):
        pytest.skip("bash/WSL not available")
    if wsl("command -v gcc && echo 'int main(void){return 0;}' > /tmp/_asan_probe.c && "
           "gcc -fsanitize=address,undefined /tmp/_asan_probe.c -o /tmp/_asan_probe && /tmp/_asan_probe").returncode:
        pytest.skip("gcc with AddressSanitizer not available")
    d = tmp_path_factory.mktemp("contract")
    (d / "corpus.bin").write_bytes(b"".join(struct.pack("<I", len(f)) + f for f, _ in stream()))
    return d


def build_and_run(d, src_dir, name):
    exe = f"{wsl_path(d)}/{name}"
    b = wsl(f"gcc -std=c99 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all "
            f"-I'{src_dir}' '{src_dir}/star_aos.c' '{wsl_path(HERE / 'fuzz')}/fuzz_aos.c' "
            f"'{wsl_path(HERE / 'fuzz')}/contract_main.c' -o '{exe}'")
    assert b.returncode == 0, b.stderr
    return wsl(f"ASAN_OPTIONS=detect_leaks=0 '{exe}' '{wsl_path(d)}/corpus.bin'", timeout=600)


def test_contract_holds_on_corpus_and_all_truncations(corpus_file):
    r = build_and_run(corpus_file, wsl_path(HERE / "src"), "contract")
    assert r.returncode == 0, (r.stdout[-300:], r.stderr[-800:])
    n_inputs = sum(len(f) + 1 for f, _ in stream())
    assert r.stdout.strip() == f"CONTRACT OK {n_inputs}"
    assert n_inputs > 70000  # 305 frames of 254-256 octets, every prefix length


@pytest.mark.parametrize("mutant", list(MUTANTS))
def test_contract_detects_planted_defect(corpus_file, mutant):
    old, new = MUTANTS[mutant]
    src = (HERE / "src" / "star_aos.c").read_text(encoding="utf-8")
    assert src.count(old) == 1, f"mutation site not found: {old}"
    m = corpus_file / f"mut_{mutant}"
    m.mkdir(exist_ok=True)
    (m / "star_aos.c").write_text(src.replace(old, new), encoding="utf-8", newline="\n")
    shutil.copy(HERE / "src" / "star_aos.h", m / "star_aos.h")
    r = build_and_run(corpus_file, wsl_path(m), f"contract_{mutant}")
    assert r.returncode != 0, f"planted defect {mutant} NOT detected: {r.stdout[-200:]}"
