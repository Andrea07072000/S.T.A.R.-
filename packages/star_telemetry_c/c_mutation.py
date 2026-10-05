"""Mutation testing for star_aos.c (S.T.A.R., 2026-10-05): the Python runner of star_foundation mutates Python ASTs only,
so C needed its own. Operators (one site per mutant, comments and preprocessor lines excluded): comparison swaps
(== !=, < <=, > >=), arithmetic swaps (+ -), bitwise swaps (& |, << >>), logical swaps (&& ||) and integer constants
(+1 and -> 0). Each mutant is compiled for the WSL host; a mutant that does not compile is EXCLUDED (not counted).
Oracle (strong, two independent corpora): (1) 305 AOS frames (5 NASA F Prime native + 300 bit-flipped, as
test_c_vs_python) compared field by field with the Python reference; (2) the 300-frame pinned TM corpus of ccsds_audit
compared with the generator truth and the FECF recomputation. A mutant is KILLED if any output differs, the program
fails, or it exceeds the timeout. Usage: python c_mutation.py [max_mutants] -> 12_EVIDENCE/mutation/star_aos_c_<date>.json"""
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "star_audit"))
from star_telemetry.engine import CcsdsTransferFrameEngine  # noqa: E402
import ccsds_audit  # noqa: E402
import test_c_vs_python as bench  # noqa: E402

W = lambda p: "/mnt/" + str(p).replace("\\", "/")[0].lower() + str(p).replace("\\", "/")[2:]
OPS = [(r"==", "!="), (r"!=", "=="), (r"<=", "<"), (r"(?<![<-])<(?![<=])", "<="), (r">=", ">"),
       (r"(?<![>-])>(?![>=])", ">="), (r"(?<![+])\+(?![+=])", "-"), (r"(?<![-])-(?![->=])", "+"),
       (r"(?<![&])&(?![&=])", "|"), (r"(?<![|])\|(?![|=])", "&"), (r"<<", ">>"), (r">>", "<<"),
       (r"&&", "||"), (r"\|\|", "&&")]
NUM = re.compile(r"\b(0x[0-9A-Fa-f]+|\d+)(u|U)?\b")


def sites(src):
    out = []
    in_comment = False
    for ln, line in enumerate(src.split("\n")):
        code = line
        if in_comment:
            if "*/" not in code:
                continue
            code = " " * (code.index("*/") + 2) + code[code.index("*/") + 2:]
            in_comment = False
        if code.lstrip().startswith("#"):
            continue
        if "/*" in code:
            start = code.index("/*")
            if "*/" in code[start:]:
                end = code.index("*/", start) + 2
                code = code[:start] + " " * (end - start) + code[end:]
            else:
                code = code[:start]
                in_comment = True
        for pat, rep in OPS:
            for m in re.finditer(pat, code):
                out.append((ln, m.start(), m.end(), rep, f"{m.group(0)}->{rep}"))
        for m in NUM.finditer(code):
            v = int(m.group(1), 0)
            for nv in ({v + 1, 0} - {v}):
                out.append((ln, m.start(), m.end(), f"{hex(nv) if m.group(1).startswith('0x') else nv}{m.group(2) or ''}",
                            f"{m.group(0)}->{nv}"))
    return out


def mutate(src, site):
    lines = src.split("\n")
    ln, a, b, rep, _ = site
    lines[ln] = lines[ln][:a] + rep + lines[ln][b:]
    return "\n".join(lines)


def oracle_inputs(tmp):
    aos = bench.stream()
    (tmp / "aos.bin").write_bytes(b"".join(f for f, _ in aos))
    aos_specs = " ".join(f"{len(f)}:{int(fecf)}" for f, fecf in aos)
    tm = ccsds_audit.corpus()
    frames = [bytes.fromhex(c["frame"]) for c in tm]
    (tmp / "tm.bin").write_bytes(b"".join(frames))
    tm_specs = " ".join(f"{len(f)}:1" for f in frames)
    ref_aos = bench.python_reference(aos)
    return aos_specs, tm_specs, ref_aos, tm, frames


def tm_ok(rows, tm, frames):
    for c, f, x in zip(tm, frames, rows):
        if "error" in x:
            return False
        if c["truth"] is not None:
            t = c["truth"]
            o, n, k = x["data_offset"], x["data_len"], x["ocf_len"]
            got = {"crc_ok": bool(x["fecf_valid"]), "scid": x["scid"], "vcid": x["vcid"], "mc": f[2], "vc": x["vcfc"],
                   "fhp": x["fhp"], "ocf": f[o + n:o + n + k].hex() if k else None, "data": f[o:o + n].hex()}
            if got != t:
                return False
        elif bool(x["fecf_valid"]) != c["crc_ok"]:
            return False
    return True


def run(max_mutants=10_000, timeout=60):
    src = (HERE / "src" / "star_aos.c").read_text(encoding="utf-8")
    tmp = Path(tempfile.mkdtemp(prefix="cmut_"))
    aos_specs, tm_specs, ref_aos, tm, frames = oracle_inputs(tmp)
    (tmp / "src").mkdir()
    for f in ("star_aos.h", "host_main.c"):
        (tmp / "src" / f).write_text((HERE / "src" / f).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    def evaluate(code):
        (tmp / "src" / "star_aos.c").write_text(code, encoding="utf-8", newline="\n")
        s, t = W(tmp / "src"), W(tmp)
        cmd = (f"gcc -std=c99 -O1 -w '{s}/star_aos.c' '{s}/host_main.c' -o /tmp/cmut_host 2>/dev/null || exit 77; "
               f"timeout {timeout} /tmp/cmut_host '{t}/aos.bin' {aos_specs} > '{t}/aos.out' || exit 3; "
               f"timeout {timeout} /tmp/cmut_host '{t}/tm.bin' {tm_specs} > '{t}/tm.out' || exit 4")
        r = subprocess.run(["wsl.exe", "-e", "bash", "-c", cmd], capture_output=True, text=True, timeout=timeout * 3)
        if r.returncode == 77:
            return "invalid"
        if r.returncode != 0:
            return "killed"
        try:
            aos_rows = [json.loads(l) for l in (tmp / "aos.out").read_text().splitlines() if l.startswith("{")]
            tm_rows = [json.loads(l) for l in (tmp / "tm.out").read_text().splitlines() if l.startswith("{")]
        except ValueError:
            return "killed"
        if len(aos_rows) != len(ref_aos) or len(tm_rows) != len(tm):
            return "killed"
        for g, e in zip(aos_rows, ref_aos):
            if any(g.get(k) != e.get(k) for k in bench.FIELDS):
                return "killed"
        return "survived" if tm_ok(tm_rows, tm, frames) else "killed"

    if evaluate(src) != "survived":
        raise RuntimeError("the unmutated C source must pass both oracles first (green base)")
    killed, survivors, invalid = 0, [], 0
    for site in sites(src)[:max_mutants]:
        v = evaluate(mutate(src, site))
        if v == "killed":
            killed += 1
        elif v == "invalid":
            invalid += 1
        else:
            survivors.append({"line": site[0] + 1, "mutation": site[4]})
    valid = killed + len(survivors)
    res = {"module": "star_telemetry_c/src/star_aos.c", "killed": killed, "survived": len(survivors),
           "invalid_excluded": invalid, "score": round(killed / valid, 4) if valid else None,
           "operators": "cmp/arith/bitwise/shift/logical swaps, int const +1 and ->0", "survivors": survivors}
    out = ROOT / "12_EVIDENCE" / "mutation" / f"star_aos_c_{date.today():%Y%m%d}.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else 10_000)
    print(r["killed"], r["survived"], r["invalid_excluded"], r["score"])
