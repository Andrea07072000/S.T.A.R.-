"""Arm stage (Cortex-R52, Cortex-R8, Zynq-7000 Cortex-A9, STM32F746 Cortex-M7): the unchanged star_aos.c built bare-metal (arm-none-eabi, -nostdlib) for Arm Cortex-R cores and
run on Renode's models. Same oracle as the other firmware stages: output equals the Python reference on the 5 NASA
F Prime frames and a bit-flipped frame is rejected. Hard timeout on Renode: an aborted machine is a FAIL in minutes.
Skips ONLY if Renode or the compiler is absent. No timing or certification claim.
Verifies: R5 (README)."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from star_telemetry.engine import CcsdsTransferFrameEngine  # noqa: E402

CC = "arm-none-eabi-gcc"
W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]
# name: (gcc flags, sources, linker script, Renode platform, UART peripheral)
CORES = {
    "cortex_r52": ("-mcpu=cortex-r52 -marm", "start_r52.S main_r52.c", "link_r52.ld", "platforms/cpus/cortex-r52.repl", "uart0"),
    "cortex_r8": ("-mcpu=cortex-r8 -marm", "start_r52.S main_r8.c", "link_r52.ld", "platforms/cpus/cortex-r8.repl", "uart1"),
    # Zynq-7000 (Cortex-A9, common in CubeSat on-board computers): same Cadence UART at another base
    "zynq7000_a9": ("-mcpu=cortex-a9 -marm -DSTAR_CDNS_BASE=0xE0000000u", "start_r52.S main_r8.c", "link_r52.ld",
                    "platforms/cpus/zynq-7000.repl", "uart0"),
    # STM32F746 (Cortex-M7, USART v2 layout): vector-table startup inside main_f7.c, aligned .data load address
    "stm32f7_m7": ("-mcpu=cortex-m7 -mthumb", "main_f7.c", "link_f7.ld", "platforms/boards/stm32f7_discovery-bb.repl",
                   "usart1"),
}


def wsl(cmd, timeout=900):
    return subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)


@pytest.mark.parametrize("core", list(CORES))
def test_firmware_on_simulated_cortex_r_matches_python(core):
    if not shutil.which("wsl.exe") or wsl(f"command -v renode && command -v {CC}").returncode:
        pytest.skip("Renode or arm-none-eabi-gcc not installed")
    flags, srcs, ld, repl, uart = CORES[core]
    fw = HERE / "fw"
    raw = (HERE.parent / "star_telemetry" / "fprime_native_frames.bin").read_bytes()
    (fw / "frames.h").write_text("const unsigned char fprime_native_frames_bin[] = {" + ",".join(str(x) for x in raw)
                                 + "};\nunsigned int fprime_native_frames_bin_len = " + str(len(raw)) + ";\n",
                                 encoding="utf-8")
    resc = (f':name: S.T.A.R. AOS frame check on a simulated {core}\nmach create "{core}"\n'
            f'machine LoadPlatformDescription @{repl}\nsysbus LoadELF $elf\n'
            f'{uart} CreateFileBackend $out true\nemulation RunFor "2"\nquit\n')
    (fw / f"run_{core}.resc").write_text(resc, encoding="utf-8", newline="\n")
    b = wsl(f"mkdir -p /root/star_fw && cd '{W(fw)}' && {CC} {flags} -O2 -std=c99 -Wall -Wextra -Werror -ffreestanding "
            f"-fno-builtin -fno-tree-loop-distribute-patterns -nostdlib -T {ld} -I../src {srcs} ../src/star_aos.c "
            f"-lgcc -o /root/star_fw/star_aos_{core}.elf && cp run_{core}.resc /root/star_fw/")
    assert b.returncode == 0, b.stderr
    r = wsl(f"cd /root/star_fw && rm -f {core}_uart.txt && timeout 300 renode --disable-xwt --console -e "
            f"'$elf=@/root/star_fw/star_aos_{core}.elf; $out=@/root/star_fw/{core}_uart.txt; "
            f"include @/root/star_fw/run_{core}.resc' > {core}.log 2>&1; cat {core}_uart.txt")
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
