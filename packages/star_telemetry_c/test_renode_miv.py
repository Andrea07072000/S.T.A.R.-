"""RISC-V space-FPGA stage: the unchanged star_aos.c built freestanding (Ubuntu riscv64 cross gcc, no libc) and run on
Renode's models of Microchip's space-relevant RISC-V parts: the Mi-V soft core (RTG4 / PolarFire FPGAs; modelled core is
rv32imaf without C — a first build with compressed instructions trapped on the first 16-bit opcode) and the PolarFire
SoC (RV64 E51 + 4 U54 harts, architecture of the RT PolarFire SoC; hart 0 runs the check, the others are parked).
The Ubuntu cross gcc defaults to PIE: without -fno-pie the start code loaded sp from a GOT in uncopied .data
(sp = 0) -- the cause of the FE310 'stuck at reset' seen for two days. Same oracle as the other firmware stages. Hard timeout on Renode. Skips ONLY if Renode or the compiler is absent; a
build or run failure is a FAIL. No timing or radiation claim."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from star_telemetry.engine import CcsdsTransferFrameEngine  # noqa: E402

CC = "riscv64-linux-gnu-gcc"
W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]
# name: (gcc arch flags, start file, main, linker script, Renode platform, UART peripheral)
TARGETS = {
    "miv": ("-march=rv32ima -mabi=ilp32", "start_fe310.S", "main_miv.c", "link_miv.ld",
            "platforms/boards/miv-board.repl", "uart"),
    "polarfire_soc": ("-march=rv64imac -mabi=lp64 -mcmodel=medany", "start_mpfs.S", "main_mpfs.c", "link_mpfs.ld",
                      "platforms/boards/mpfs-icicle-kit.repl", "mmuart0"),
    "fe310": ("-march=rv32imac -mabi=ilp32", "start_fe310.S", "main_fe310.c", "link_fe310.ld",
              "platforms/cpus/sifive-fe310.repl", "uart0"),
}


def wsl(cmd, timeout=900):
    return subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)


@pytest.mark.parametrize("target", list(TARGETS))
def test_firmware_on_simulated_riscv_space_part_matches_python(target):
    if not shutil.which("wsl.exe") or wsl(f"command -v renode && command -v {CC}").returncode:
        pytest.skip("Renode or riscv64 cross gcc not installed")
    arch, start, main, ld, repl, uart = TARGETS[target]
    fw = HERE / "fw"
    raw = (HERE.parent / "star_telemetry" / "fprime_native_frames.bin").read_bytes()
    (fw / "frames.h").write_text("const unsigned char fprime_native_frames_bin[] = {" + ",".join(str(x) for x in raw)
                                 + "};\nunsigned int fprime_native_frames_bin_len = " + str(len(raw)) + ";\n",
                                 encoding="utf-8")
    resc = (f':name: S.T.A.R. AOS frame check on a simulated {target}\nmach create "{target}"\n'
            f'machine LoadPlatformDescription @{repl}\nsysbus LoadELF $elf\n'
            f'{uart} CreateFileBackend $out true\nemulation RunFor "2"\nquit\n')
    (fw / f"run_{target}.resc").write_text(resc, encoding="utf-8", newline="\n")
    b = wsl(f"mkdir -p /root/star_fw && cd '{W(fw)}' && {CC} {arch} -O2 -std=c99 -Wall -Wextra -Werror -ffreestanding -fno-pie -no-pie "
            f"-fno-builtin -fno-tree-loop-distribute-patterns -nostdlib -static -T {ld} -I../src {start} {main} "
            f"../src/star_aos.c -o /root/star_fw/star_aos_{target}.elf && cp run_{target}.resc /root/star_fw/")
    assert b.returncode == 0, b.stderr
    r = wsl(f"cd /root/star_fw && rm -f {target}_uart.txt && timeout 300 renode --disable-xwt --console -e "
            f"'$elf=@/root/star_fw/star_aos_{target}.elf; $out=@/root/star_fw/{target}_uart.txt; "
            f"include @/root/star_fw/run_{target}.resc' > {target}.log 2>&1; cat {target}_uart.txt")
    lines = [l for l in r.stdout.splitlines() if l.startswith("{")]
    assert r.stdout.strip().endswith("DONE") and len(lines) == 6, (r.stdout[-400:], r.stderr[-300:])
    got = [json.loads(l) for l in lines]
    off = 0
    for i, (n, fecf) in enumerate([(256, True)] * 4 + [(254, False)]):
        h, _ = CcsdsTransferFrameEngine(frame_length=n, has_fecf=fecf).parse_frame(raw[off:off + n])
        off += n
        g = got[i]
        assert (g["tfvn"], g["scid"], g["vcid"], g["vcfc"], g["fhp"], g["fecf_valid"], g["fecf_received"]) == \
               (h.tfvn, h.scid, h.vcid, h.vcfc, h.fhp, int(h.fecf_valid), h.fecf_received if fecf else 0)
    assert got[5]["fecf_valid"] == 0 and got[5]["fecf_received"] != got[5]["fecf_computed"]
