# -*- coding: utf-8 -*-
"""STAR-HW-HOST / STAR-HW-CROSS: the C port of the AOS/TM frame check must agree field-by-field with the Python
reference (star_telemetry.engine) on the 5 NASA F Prime native frames AND on 300 deterministic fault-injected frames,
on every target that is available: x86_64 host, aarch64 and armhf under qemu-user (WSL). A target that cannot be built
or run is reported as SKIPPED with the reason, never as passed.
Verifies: R1, R2, R5 (README)."""
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TELEM = HERE.parent / "star_telemetry"
sys.path.insert(0, str(TELEM.parent))
from star_telemetry.engine import CcsdsTransferFrameEngine  # noqa: E402

SPEC = [(256, True)] * 4 + [(254, False)]
FIELDS = ("tfvn", "scid", "vcid", "vcfc", "replay", "fhp", "fecf_valid", "fecf_received")
TARGETS = {  # name: (compiler, runner prefix)
    "x86_64": ("gcc", ""),
    "aarch64": ("aarch64-linux-gnu-gcc -static", "qemu-aarch64 "),
    # WSL cannot reserve the low 4 GiB for 32-bit qemu-user ("Operation not supported"); a guest base above it works
    "armhf": ("arm-linux-gnueabihf-gcc -static", "qemu-arm -B 0x100000000 "),
    # ISA portability targets (emulated Linux user space, NOT space hardware): little- and big-endian, 32 and 64 bit
    "riscv64": ("riscv64-linux-gnu-gcc -static", "qemu-riscv64 -B 0x100000000 "),
    "mips_be": ("mips-linux-gnu-gcc -static", "qemu-mips -B 0x100000000 "),
    "mipsel": ("mipsel-linux-gnu-gcc -static", "qemu-mipsel -B 0x100000000 "),
    "ppc_be": ("powerpc-linux-gnu-gcc -static", "qemu-ppc -B 0x100000000 "),
    "ppc64le": ("powerpc64le-linux-gnu-gcc -static", "qemu-ppc64le "),
    "s390x_be": ("s390x-linux-gnu-gcc -static", "qemu-s390x "),
    # 2026-10-04: Ubuntu cross toolchains (registered in THIRD_PARTY_MANIFEST system_tools); 32-bit guests need -B
    "i386": ("i686-linux-gnu-gcc -static", "qemu-i386 -B 0x100000000 "),
    "armel_softfp": ("arm-linux-gnueabi-gcc -static", "qemu-arm -B 0x100000000 "),
    "mips64_be": ("mips64-linux-gnuabi64-gcc -static", "qemu-mips64 "),
    "mips64el": ("mips64el-linux-gnuabi64-gcc -static", "qemu-mips64el "),
    "ppc64_be": ("powerpc64-linux-gnu-gcc -static", "qemu-ppc64 "),
    # sparc64 NOT listed: qemu-sparc64 6.2.0 (Ubuntu jammy) crashes (rc 139) on a plain static or dynamic hello world
    # (probe_sparc64.sh, 2026-10-04) -> an emulator defect, not a target; re-probe after a qemu upgrade
    "m68k_be": ("m68k-linux-gnu-gcc -static", "qemu-m68k -B 0x100000000 "),
    "sh4": ("sh4-linux-gnu-gcc -static", "qemu-sh4 -B 0x100000000 "),
    "alpha": ("alpha-linux-gnu-gcc -static", "qemu-alpha "),
    "hppa_be": ("hppa-linux-gnu-gcc -static", "qemu-hppa -B 0x100000000 "),
}


NATIVE = sys.platform != "win32"  # Linux/macOS (e.g. a public CI runner): run bash directly, no WSL


def wsl_path(p: Path) -> str:
    if NATIVE:
        return str(p)
    s = str(p).replace("\\", "/")
    return "/mnt/" + s[0].lower() + s[2:]


def wsl(cmd: str, timeout=300):
    argv = ["bash", "-c", cmd] if NATIVE else ["wsl.exe", "-e", "bash", "-c", cmd]
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def stream():
    """Native frames + 300 corrupted copies (seed 20261003): bit flips anywhere, header-only flips, FECF-only flips."""
    raw = (TELEM / "fprime_native_frames.bin").read_bytes()
    frames, off = [], 0
    for n, fecf in SPEC:
        frames.append((raw[off:off + n], fecf))
        off += n
    rnd = random.Random(20261003)
    out = list(frames)
    for k in range(300):
        f, fecf = frames[k % len(frames)]
        b = bytearray(f)
        region = k % 3
        lo, hi = {0: (0, len(b)), 1: (0, 8), 2: (len(b) - 2, len(b))}[region]
        for _ in range(1 + k % 4):
            i = rnd.randrange(lo, hi)
            b[i] ^= 1 << rnd.randrange(8)
        out.append((bytes(b), fecf))
    return out


def python_reference(frames):
    res = []
    for f, fecf in frames:
        h, _ = CcsdsTransferFrameEngine(frame_length=len(f), has_fecf=fecf).parse_frame(f)
        res.append({"tfvn": h.tfvn, "scid": h.scid, "vcid": h.vcid, "vcfc": h.vcfc, "replay": int(h.replay_flag),
                    "fhp": h.fhp, "fecf_valid": int(h.fecf_valid), "fecf_received": h.fecf_received if fecf else 0})
    return res


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    if not shutil.which("bash" if NATIVE else "wsl.exe"):
        pytest.skip("bash/WSL not available")
    frames = stream()
    d = tmp_path_factory.mktemp("aos")
    (d / "stream.bin").write_bytes(b"".join(f for f, _ in frames))
    specs = " ".join(f"{len(f)}:{int(fecf)}" for f, fecf in frames)
    return frames, d, specs


@pytest.mark.parametrize("target", list(TARGETS))
def test_c_matches_python_on_native_and_corrupted_frames(corpus, target):
    frames, d, specs = corpus
    cc, run = TARGETS[target]
    exe = f"'{wsl_path(d)}/star_aos_dump_{target}'"
    src = wsl_path(HERE / "src")
    tools = [cc.split()[0]] + ([run.split()[0]] if run else [])
    missing = [t for t in tools if wsl(f"command -v {t}").returncode != 0]
    if missing:
        pytest.skip(f"{target}: not installed: {missing}")
    # from here on a failure is a FAIL, never a skip (a skip must not hide a build bug)
    b = wsl(f"{cc} -std=c99 -O2 -Wall -Wextra -Werror -pedantic '{src}/star_aos.c' '{src}/host_main.c' -o {exe}")
    assert b.returncode == 0, b.stderr
    # output goes to a file inside WSL: the wsl.exe stdout pipe was observed to garble long outputs (2 of 10 runs)
    out = d / f"out_{target}.jsonl"
    r = wsl(f"{run}{exe} '{wsl_path(d)}/stream.bin' {specs} > '{wsl_path(out)}'")
    assert r.returncode == 0, r.stderr
    lines = out.read_text(encoding="utf-8").splitlines()
    bad = [ln for ln in lines if not ln.startswith("{")]
    assert not bad, f"non-JSON output from {target}: {bad[:3]!r} (stderr {r.stderr[-200:]!r})"
    got = [json.loads(line) for line in lines]
    ref = python_reference(frames)
    assert len(got) == len(ref) == 305
    mism = [(i, k, got[i][k], ref[i][k]) for i in range(len(ref)) for k in FIELDS if got[i][k] != ref[i][k]]
    assert not mism, mism[:10]
    # the corruption is real: the CRC must reject every frame whose FECF-protected bytes were flipped
    # (a double flip of the same bit restores the original frame: only frames that really changed must be rejected)
    changed = [k for k, (f, fecf) in enumerate(frames[5:]) if fecf and f != frames[k % 5][0]]
    rejected = sum(1 for k in changed if not got[5 + k]["fecf_valid"])
    protected = len(changed)
    assert protected >= 230
    assert rejected == protected, f"{rejected}/{protected} corrupted FECF frames rejected"
