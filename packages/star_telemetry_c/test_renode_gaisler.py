"""Space-processor family stage: the unchanged star_aos.c built with Gaisler BCC2 for each GRLIB/LEON SoC BSP and run
on Renode's model of that SoC: GR712RC (dual-core LEON3FT, flown on ESA missions) and GR716 (LEON3FT space
microcontroller). Same oracle as test_renode_leon3: output must equal the Python reference on the 5 NASA F Prime frames
and a bit-flipped frame must be rejected. Renode plays the boot loader (initial SP at the top of the RAM the BSP links
to). Skips ONLY if BCC2 or Renode is absent; a build or run failure is a FAIL. No timing or radiation claim.
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

BCC = "/opt/bcc-2.2.4-gcc/bin"
W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]
# name: (BCC flags, Renode platform, UART peripheral name, APBUART base, initial stack pointer = top of the BSP's RAM)
# GR712RC needs -mfix-gr712rc (BCC2 manual: errata workarounds; only that multilib ships the GR712RC linkcmds)
SOCS = {
    "gr712rc": ("-qbsp=gr712rc -mcpu=leon3 -mfix-gr712rc", "platforms/cpus/gr712rc.repl", "uart0", "0x80000100u", "0x48000000"),
    "gr716": ("-qbsp=gr716 -mcpu=leon3", "platforms/cpus/gr716.repl", "uart", "0x80300000u", "0x30010000"),
}


def wsl(cmd, timeout=600):
    return subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)


@pytest.mark.parametrize("soc", list(SOCS))
def test_firmware_on_simulated_gaisler_soc_matches_python(soc):
    if not shutil.which("wsl.exe") or wsl(f"command -v renode && test -x {BCC}/sparc-gaisler-elf-gcc").returncode:
        pytest.skip("Renode or Gaisler BCC2 not installed")
    bsp, repl, uart, base, sp = SOCS[soc]
    fw = HERE / "fw"
    raw = (HERE.parent / "star_telemetry" / "fprime_native_frames.bin").read_bytes()
    (fw / "frames.h").write_text("const unsigned char fprime_native_frames_bin[] = {" + ",".join(str(x) for x in raw)
                                 + "};\nunsigned int fprime_native_frames_bin_len = " + str(len(raw)) + ";\n",
                                 encoding="utf-8")
    resc = (f':name: S.T.A.R. AOS frame check on a simulated {soc}\n'
            f'mach create "{soc}"\nmachine LoadPlatformDescription @{repl}\nsysbus LoadELF $elf\n'
            f'cpu SetRegister 14 {sp}\n{uart} CreateFileBackend $out true\nemulation RunFor "2"\nquit\n')
    (fw / f"run_{soc}.resc").write_text(resc, encoding="utf-8", newline="\n")
    b = wsl(f"mkdir -p /root/star_fw && cd '{W(fw)}' && {BCC}/sparc-gaisler-elf-gcc {bsp} -O2 -std=c99 "
            f"-Wall -Wextra -Werror -DSTAR_APBUART_BASE={base} -I../src main_leon3.c ../src/star_aos.c "
            f"-o /root/star_fw/star_aos_{soc}.elf && cp run_{soc}.resc /root/star_fw/")
    assert b.returncode == 0, b.stderr
    r = wsl(f"cd /root/star_fw && rm -f {soc}_uart.txt && renode --disable-xwt --console -e "
            f"'$elf=@/root/star_fw/star_aos_{soc}.elf; $out=@/root/star_fw/{soc}_uart.txt; "
            f"include @/root/star_fw/run_{soc}.resc' > {soc}.log 2>&1; cat {soc}_uart.txt")
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
