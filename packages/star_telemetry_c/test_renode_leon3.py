"""Space-processor stage: the unchanged star_aos.c built with Gaisler BCC2 for LEON3 (SPARC V8, big-endian, the ESA /
Gaisler space processor family) and run on Renode's simulated leon3 board. Output must equal the Python reference on
the 5 NASA F Prime frames and a bit-flipped frame must be rejected. Renode plays the boot loader (initial SP), as BCC2
detects end-of-RAM from it (BCC manual sec. 2.10). Skips ONLY if BCC2 or Renode is absent. No timing is claimed."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from star_telemetry.engine import CcsdsTransferFrameEngine  # noqa: E402

BCC = "/opt/bcc-2.2.4-gcc/bin"
W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]


def wsl(cmd, timeout=600):
    return subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)


def test_firmware_on_simulated_leon3_matches_python():
    if not shutil.which("wsl.exe") or wsl(f"command -v renode && test -x {BCC}/sparc-gaisler-elf-gcc").returncode:
        pytest.skip("Renode or Gaisler BCC2 not installed")
    fw = HERE / "fw"
    raw = (HERE.parent / "star_telemetry" / "fprime_native_frames.bin").read_bytes()
    (fw / "frames.h").write_text("const unsigned char fprime_native_frames_bin[] = {" + ",".join(str(x) for x in raw)
                                 + "};\nunsigned int fprime_native_frames_bin_len = " + str(len(raw)) + ";\n",
                                 encoding="utf-8")
    b = wsl(f"cd '{W(fw)}' && {BCC}/sparc-gaisler-elf-gcc -qbsp=leon3 -mcpu=leon3 -O2 -std=c99 -Wall -Wextra -Werror "
            f"-I../src main_leon3.c ../src/star_aos.c -o /root/star_fw/star_aos_leon3.elf "
            f"&& cp run_leon3.resc /root/star_fw/")
    assert b.returncode == 0, b.stderr
    r = wsl("cd /root/star_fw && rm -f leon3_uart.txt && renode --disable-xwt --console -e "
            "'$elf=@/root/star_fw/star_aos_leon3.elf; $out=@/root/star_fw/leon3_uart.txt; "
            "include @/root/star_fw/run_leon3.resc' > leon3.log 2>&1; cat leon3_uart.txt")
    lines = [l for l in r.stdout.splitlines() if l.startswith("{")]
    assert r.stdout.strip().endswith("DONE") and len(lines) == 6, r.stdout[-400:]
    got = [json.loads(l) for l in lines]
    off = 0
    for i, (n, fecf) in enumerate([(256, True)] * 4 + [(254, False)]):
        h, _ = CcsdsTransferFrameEngine(frame_length=n, has_fecf=fecf).parse_frame(raw[off:off + n]); off += n
        g = got[i]
        assert (g["tfvn"], g["scid"], g["vcid"], g["vcfc"], g["fhp"], g["fecf_valid"], g["fecf_received"]) == \
               (h.tfvn, h.scid, h.vcid, h.vcfc, h.fhp, int(h.fecf_valid), h.fecf_received if fecf else 0)
    assert got[5]["fecf_valid"] == 0 and got[5]["fecf_received"] != got[5]["fecf_computed"]
