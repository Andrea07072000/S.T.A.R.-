"""Bare-metal stage: the unchanged star_aos.c is cross-compiled for STM32F407 (Cortex-M4, arm-none-eabi, -nostdlib)
and executed on a SIMULATED STM32F4 Discovery in Renode; the USART2 output must equal the Python reference on the 5
NASA F Prime frames, and a bit-flipped frame must be rejected. Skips ONLY if the toolchain/simulator is absent.
Renode's platform does not model the DWT cycle counter, so no timing is claimed from this test.
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

W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]


def wsl(cmd, timeout=600):
    return subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)


def test_firmware_on_simulated_stm32f4_matches_python():
    if not shutil.which("wsl.exe") or wsl("command -v renode && command -v arm-none-eabi-gcc").returncode:
        pytest.skip("Renode or arm-none-eabi-gcc not installed")
    fw = HERE / "fw"
    raw = (HERE.parent / "star_telemetry" / "fprime_native_frames.bin").read_bytes()
    (fw / "frames.h").write_text("const unsigned char fprime_native_frames_bin[] = {" + ",".join(str(x) for x in raw)
                                 + "};\nunsigned int fprime_native_frames_bin_len = " + str(len(raw)) + ";\n",
                                 encoding="utf-8")
    b = wsl(f"cd '{W(fw)}' && arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O2 -std=c99 -Wall -Wextra -Werror -ffreestanding "
            f"-nostdlib -I../src -T link.ld main.c ../src/star_aos.c -o star_aos_fw.elf")
    assert b.returncode == 0, b.stderr
    r = wsl(f"mkdir -p /root/star_fw && cp '{W(fw)}/star_aos_fw.elf' '{W(fw)}/run_stm32f4.resc' /root/star_fw/ && "
            "cd /root/star_fw && rm -f uart2.txt && renode --disable-xwt --console -e "
            "'$elf=@/root/star_fw/star_aos_fw.elf; $out=@/root/star_fw/uart2.txt; include @/root/star_fw/run_stm32f4.resc'"
            " > run.log 2>&1; cat uart2.txt")
    lines = [l for l in r.stdout.splitlines() if l.startswith("{")]
    assert r.stdout.strip().endswith("DONE") and len(lines) == 6, r.stdout[-500:]
    got = [json.loads(l) for l in lines]
    off = 0
    for i, (n, fecf) in enumerate([(256, True)] * 4 + [(254, False)]):
        h, _ = CcsdsTransferFrameEngine(frame_length=n, has_fecf=fecf).parse_frame(raw[off:off + n]); off += n
        g = got[i]
        assert (g["tfvn"], g["scid"], g["vcid"], g["vcfc"], g["fhp"], g["fecf_valid"]) == (h.tfvn, h.scid, h.vcid, h.vcfc, h.fhp, int(h.fecf_valid))
    assert got[5]["fecf_valid"] == 0 and got[5]["fecf_received"] != got[5]["fecf_computed"]
