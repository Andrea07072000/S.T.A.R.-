"""Sweep of Renode-simulated STM32 microcontrollers with the unchanged star_aos.c (S.T.A.R., 2026-10-06).

  python sweep_renode_stm32.py  ->  12_EVIDENCE/hw/renode_stm32_sweep_20261006.json

For every target of TARGETS: build fw/main_sweep.c + src/star_aos.c bare-metal for that core (arm-none-eabi-gcc,
-ffreestanding -nostdlib, libgcc only), load it on the Renode platform description of that microcontroller, capture
the USART output and compare each of the six lines with the Python reference engine on the same NASA F Prime frames
(five native frames and a corrupted copy that must fail the FECF). A target PASSES only if all six lines match and the
firmware prints DONE. Simulated models, no physical hardware: what is verified is that the same C source builds for
the core and gives the reference answers through that SoC's memory map and USART model.
Targets already covered by their own tests (STM32F407, STM32F103, STM32F746) are not repeated here.
"""
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

# name: (platform description, -mcpu, usart node, usart base, v2 register layout, flash origin)
TARGETS = {
    "stm32f042": ("platforms/cpus/stm32f042.repl", "cortex-m0", "usart1", 0x40013800, 1, 0x08000000),
    "stm32f072": ("platforms/cpus/stm32f072.repl", "cortex-m0", "usart1", 0x40013800, 1, 0x08000000),
    "stm32g0": ("platforms/cpus/stm32g0.repl", "cortex-m0plus", "usart1", 0x40013800, 1, 0x08000000),
    "stm32l071": ("platforms/cpus/stm32l071.repl", "cortex-m0plus", "usart2", 0x40004400, 1, 0x08000000),
    "stm32l072": ("platforms/cpus/stm32l072.repl", "cortex-m0plus", "usart2", 0x40004400, 1, 0x08000000),
    "stm32l151": ("platforms/cpus/stm32l151.repl", "cortex-m3", "usart1", 0x40013800, 0, 0x08000000),
    "stm32f412": ("platforms/cpus/stm32f412.repl", "cortex-m4", "usart6", 0x40011400, 0, 0x08000000),
    "stm32f429": ("platforms/cpus/stm32f429.repl", "cortex-m4", "usart1", 0x40011000, 0, 0x08000000),
    "stm32f777": ("platforms/cpus/stm32f777.repl", "cortex-m7", "usart1", 0x40011000, 1, 0x08000000),
    "stm32h743": ("platforms/cpus/stm32h743.repl", "cortex-m7", "usart1", 0x40011000, 1, 0x08000000),
    "stm32h753": ("platforms/cpus/stm32h753.repl", "cortex-m7", "usart1", 0x40011000, 1, 0x08000000),
    "stm32l552": ("platforms/cpus/stm32l552.repl", "cortex-m33", "usart1", 0x40013800, 1, 0x08000000),
    "stm32wba52": ("platforms/cpus/stm32wba52.repl", "cortex-m33", "usart1", 0x40013800, 1, 0x08000000),
}
LD = """MEMORY
{{
  FLASH (rx)  : ORIGIN = {flash:#010x}, LENGTH = 64K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 4K
}}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS
{{
  .isr_vector : {{ KEEP(*(.isr_vector)) }} > FLASH
  .text : {{ *(.text*) *(.rodata*) . = ALIGN(4); }} > FLASH
  _sidata = LOADADDR(.data);
  .data : ALIGN(4) {{ _sdata = .; *(.data*) _edata = .; }} > RAM AT > FLASH
  .bss : ALIGN(4) {{ _sbss = .; *(.bss*) *(COMMON) _ebss = .; }} > RAM
}}
"""
RESC = """mach create "{name}"
machine LoadPlatformDescription @{repl}
sysbus LoadELF $elf
{uart} CreateFileBackend $out true
emulation RunFor "2"
quit
"""
W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]


def wsl(cmd, timeout=600):
    return subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout)


def reference():
    """The six expected records from the Python engine, and the raw frames."""
    from star_telemetry.engine import CcsdsTransferFrameEngine
    raw = (HERE.parent / "star_telemetry" / "fprime_native_frames.bin").read_bytes()
    out, off = [], 0
    for n, fecf in [(256, True)] * 4 + [(254, False)]:
        h, _ = CcsdsTransferFrameEngine(frame_length=n, has_fecf=fecf).parse_frame(raw[off:off + n])
        off += n
        out.append({"tfvn": h.tfvn, "scid": h.scid, "vcid": h.vcid, "vcfc": h.vcfc, "fhp": h.fhp, "fecf_valid": int(h.fecf_valid)})
    return raw, out


def run_target(name, raw, expected, work="/root/star_fw/sweep"):
    repl, cpu, uart, base, v2, flash = TARGETS[name]
    fw = HERE / "fw"
    (fw / "frames.h").write_text("const unsigned char fprime_native_frames_bin[] = {" + ",".join(str(x) for x in raw)
                                 + "};\nunsigned int fprime_native_frames_bin_len = " + str(len(raw)) + ";\n", encoding="utf-8")
    ld, resc = LD.format(flash=flash), RESC.format(name=name, repl=repl, uart=uart)
    prep = (f"mkdir -p {work} && cd {work} && cat > {name}.ld <<'EOF'\n{ld}EOF\ncat > {name}.resc <<'EOF'\n{resc}EOF\n"
            f"cd '{W(fw)}' && arm-none-eabi-gcc -mcpu={cpu} -mthumb -O2 -std=c99 -Wall -Wextra -Werror -ffreestanding -nostdlib "
            f"-DUART_BASE={base:#010x}u -DUART_V2={v2} -I../src -T {work}/{name}.ld main_sweep.c ../src/star_aos.c -lgcc -o {work}/{name}.elf")
    b = wsl(prep)
    if b.returncode:
        return {"status": "BUILD_FAILED", "detail": (b.stderr or b.stdout)[-300:]}
    r = wsl(f"cd {work} && rm -f {name}.txt && timeout 300 renode --disable-xwt --console -e "
            f"'$elf=@{work}/{name}.elf; $out=@{work}/{name}.txt; include @{work}/{name}.resc' > {name}.log 2>&1; cat {name}.txt 2>/dev/null; "
            f"echo; echo @@LOG; grep -i -m3 'error\\|exception\\|could not' {name}.log")
    text, _, log = r.stdout.partition("@@LOG")
    lines = [ln for ln in text.splitlines() if ln.startswith("{")]
    done = text.strip().endswith("DONE")
    if not done or len(lines) != 6:
        return {"status": "NO_OUTPUT" if not lines else "INCOMPLETE", "lines": len(lines), "done": done, "detail": log.strip()[-300:]}
    try:
        got = [json.loads(ln) for ln in lines]
    except ValueError:
        return {"status": "GARBLED", "detail": lines[0][:120]}
    wrong = [i for i, exp in enumerate(expected) if any(got[i].get(k) != v for k, v in exp.items())]
    corrupted_rejected = got[5].get("fecf_valid") == 0 and got[5].get("fecf_received") != got[5].get("fecf_computed")
    ok = not wrong and corrupted_rejected
    return {"status": "PASS" if ok else "MISMATCH", "mismatching_frames": wrong, "corrupted_frame_rejected": corrupted_rejected,
            "output_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]}


def main(argv):
    names = [a for a in argv if a in TARGETS] or list(TARGETS)
    raw, expected = reference()
    renode = wsl("renode --version 2>/dev/null | tail -1; arm-none-eabi-gcc --version | head -1").stdout.strip().splitlines()
    results = {}
    for name in names:
        results[name] = dict(run_target(name, raw, expected), core=TARGETS[name][1], platform=TARGETS[name][0], usart=TARGETS[name][2])
        print(name, TARGETS[name][1], results[name]["status"], results[name].get("detail", "")[:120], flush=True)
    passed = sorted(n for n, r in results.items() if r["status"] == "PASS")
    out = {"date": str(date.today()), "tools": renode, "kind": "Renode-simulated microcontrollers (no physical hardware)",
           "check": "six frame records on the USART equal to the Python reference engine; corrupted frame rejected; DONE printed",
           "targets": len(results), "passed": passed, "not_passed": {n: r["status"] for n, r in results.items() if r["status"] != "PASS"},
           "results": results}
    if len(names) == len(TARGETS):
        dest = ROOT / "12_EVIDENCE" / "hw" / "renode_stm32_sweep_20261006.json"
        dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
        print("->", dest.name)
    print(f"PASS {len(passed)}/{len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
