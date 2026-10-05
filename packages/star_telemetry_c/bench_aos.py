"""Throughput benchmark of the AOS/TM frame check: C port on x86_64 (native), aarch64 and armhf (qemu-user) vs the
Python engine, same 30,000-frame stream (the 5 NASA F Prime native frames repeated). Emulated numbers measure the
emulator, NOT ARM hardware: they are reported for completeness and must not be read as target performance."""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TELEM = HERE.parent / "star_telemetry"
sys.path.insert(0, str(TELEM.parent))
from star_telemetry.engine import CcsdsTransferFrameEngine  # noqa: E402

REPS = 6000
SPEC = [(256, 1)] * 4 + [(254, 0)]
w = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]


def main():
    raw = (TELEM / "fprime_native_frames.bin").read_bytes()
    out_dir = HERE / "_bench"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "stream.bin").write_bytes(raw * REPS)
    n = REPS * len(SPEC)
    res = {"frames": n, "bytes": len(raw) * REPS}
    frames, off = [], 0
    for ln, fecf in SPEC:
        frames.append((raw[off:off + ln], fecf)); off += ln
    eng = {ln_f: CcsdsTransferFrameEngine(frame_length=ln_f[0], has_fecf=bool(ln_f[1])) for ln_f in set(SPEC)}
    t = time.perf_counter()
    for _ in range(REPS):
        for f, fecf in frames:
            eng[(len(f), fecf)].parse_frame(f)
    res["python_frames_per_s"] = round(n / (time.perf_counter() - t))
    # the C tool takes one len:fecf spec per frame; for 30k frames we loop inside a tiny driver instead
    drv = HERE / "src" / "bench_driver.c"
    for tgt, cc, run in (("x86_64", "gcc", ""), ("aarch64", "aarch64-linux-gnu-gcc -static", "qemu-aarch64 "),
                         ("armhf", "arm-linux-gnueabihf-gcc -static", "qemu-arm -B 0x100000000 ")):
        exe = f"'{w(out_dir)}/drv_{tgt}'"
        cmd = (f"{cc} -std=c99 -O2 -I'{w(HERE / 'src')}' '{w(HERE / 'src')}/star_aos.c' '{w(drv)}' -o {exe} && "
               f"{run}{exe} '{w(out_dir)}/stream.bin' > '{w(out_dir)}/out_{tgt}.txt'")
        r = subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=600)
        if r.returncode:
            res[tgt] = {"error": r.stderr[-200:]}; continue
        k, bad, s = (out_dir / f"out_{tgt}.txt").read_text().split()
        res[tgt] = {"frames": int(k), "invalid": int(bad), "seconds": float(s), "frames_per_s": round(int(k) / float(s))}
    print(json.dumps(res, indent=1))
    (HERE / "bench_result.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
