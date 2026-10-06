# -*- coding: utf-8 -*-
"""tle_audit — what do TLE readers accept? Differential audit of two-line-element ingestion, S.T.A.R., 2026-10-05.

Each implementation runs in its own interpreter through a driver defining ingest(line1, line2) -> dict with at least
satnum and inclination (deg), or raising to reject. Reference: the TLE format rule itself (NORAD/CelesTrak): checksum =
sum of digits with '-' counting 1, mod 10, in column 69; line numbers '1'/'2' in column 1; satellite number in columns
3-7 equal on both lines; 69 characters. Base corpus: the SGP4-VER TLEs (Vallado, fixtures/SGP4-VER.TLE) whose checksums
are valid under that rule. Six derived kinds, each with the verdict the rule implies:
  valid (accept) · field_digit (one digit changed, checksum NOT updated: reject) · checksum (checksum digit changed:
  reject) · line_number (line 2 starts with '1': reject) · satnum_mismatch (line 2 satnum changed, checksum recomputed:
  reject) · truncated (last data character removed: reject) · resummed (one digit changed AND checksum recomputed:
  a different but well-formed TLE: accept).
Probe validation: an implementation counts only if it accepts every valid TLE and reads its inclination within
1e-4 deg of the value in columns 9-16 of line 2. Reported: per kind, how many each implementation accepts.
"""
from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path
from typing import Dict, List

from audit_guard import driver_rows  # one result row per case, or a declared error (2026-10-06)

HERE = Path(__file__).resolve().parent
KINDS = ("valid", "field_digit", "checksum", "line_number", "satnum_mismatch", "truncated", "resummed")
SHOULD_ACCEPT = {"valid": True, "resummed": True}
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __tl_json\n__tl_out = []\nfor __tl_a, __tl_b in payload['cases']:\n"
          "    try:\n        __tl_x = ingest(__tl_a, __tl_b)\n"
          "        __tl_out.append({'ok': {'satnum': int(__tl_x['satnum']), 'inc': float(__tl_x['inc'])}})\n"
          "    except Exception as __tl_e:\n        __tl_out.append({'error': type(__tl_e).__name__ + ': ' + str(__tl_e)[:80]})\n"
          "print(__tl_json.dumps(__tl_out))\n")


def checksum(line: str) -> int:
    return sum(int(c) if c.isdigit() else (1 if c == "-" else 0) for c in line[:68]) % 10


def well_formed(l1: str, l2: str) -> bool:
    return (len(l1) == 69 and len(l2) == 69 and l1[0] == "1" and l2[0] == "2" and l1[2:7] == l2[2:7]
            and checksum(l1) == int(l1[68]) and checksum(l2) == int(l2[68]))


def _default_fixture() -> Path:
    # next to the module in the source tree; in the working directory when installed (the release pipeline copies
    # fixtures/ next to the tests: first 0.9.0 attempt failed outside the tree because only the module dir was searched)
    for p in (HERE / "fixtures" / "SGP4-VER.TLE", Path.cwd() / "fixtures" / "SGP4-VER.TLE"):
        if p.exists():
            return p
    raise FileNotFoundError("fixtures/SGP4-VER.TLE not found next to tle_audit.py nor in the working directory")


def base_tles(path: Path | None = None) -> List[tuple]:
    path = path or _default_fixture()
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    pairs = [(lines[i][:69], lines[i + 1][:69]) for i in range(len(lines) - 1)
             if lines[i].startswith("1 ") and lines[i + 1].startswith("2 ")]
    seen, out = set(), []
    for p in pairs:
        if well_formed(*p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _digit_positions(line: str) -> List[int]:
    return [k for k in range(8, 68) if line[k].isdigit()]


def _with(line: str, k: int, ch: str) -> str:
    return line[:k] + ch + line[k + 1:]


def _resum(line: str) -> str:
    return line[:68] + str(checksum(line))


def corpus(seed: int = 20261005) -> List[Dict]:
    rng = random.Random(seed)
    out = []
    for n, (l1, l2) in enumerate(base_tles()):
        out.append({"id": f"{n}:valid", "kind": "valid", "l1": l1, "l2": l2})
        k = rng.choice(_digit_positions(l2))
        d = str((int(l2[k]) + 1 + rng.randrange(8)) % 10)
        bad = _with(l2, k, d)
        if checksum(bad) != int(l2[68]):                     # only if the change really breaks the checksum
            out.append({"id": f"{n}:field_digit", "kind": "field_digit", "l1": l1, "l2": bad})
        out.append({"id": f"{n}:resummed", "kind": "resummed", "l1": l1, "l2": _resum(bad)})
        out.append({"id": f"{n}:checksum", "kind": "checksum", "l1": l1, "l2": _with(l2, 68, str((int(l2[68]) + 1 + rng.randrange(9)) % 10))})
        out.append({"id": f"{n}:line_number", "kind": "line_number", "l1": l1, "l2": _resum("1" + l2[1:])})
        sn = f"{(int(l2[2:7]) + 1 + rng.randrange(1000)) % 100000:05d}"
        out.append({"id": f"{n}:satnum_mismatch", "kind": "satnum_mismatch", "l1": l1, "l2": _resum(l2[:2] + sn + l2[7:])})
        out.append({"id": f"{n}:truncated", "kind": "truncated", "l1": l1, "l2": l2[:67] + l2[68]})
    return out


def run(command: List[str], driver: str, cases: List, env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return driver_rows(r.stdout, len(cases))


def _read_ok(got, case: Dict) -> bool:
    """True when the values read from a valid TLE are the ones printed in it (inclination to 1e-4 deg, catalogue number)."""
    if not isinstance(got, dict):
        return False
    inc, sat = got.get("inc"), got.get("satnum")
    if isinstance(inc, bool) or not isinstance(inc, (int, float)) or isinstance(sat, bool) or not isinstance(sat, int):
        return False
    return abs(inc - float(case["l2"][8:16])) <= 1e-4 and sat == int(case["l1"][2:7])


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    res = {n: run(i["command"], i["driver"], [[c["l1"], c["l2"]] for c in cases], i.get("env")) for n, i in impls.items()}
    per_impl = {}
    for n, rows in res.items():
        acc = {k: 0 for k in KINDS}
        tot = {k: 0 for k in KINDS}
        bad_read = []
        for c, x in zip(cases, rows):
            tot[c["kind"]] += 1
            if "ok" in x:
                acc[c["kind"]] += 1
                # 2026-10-06: `abs(nan - inc) > 1e-4` is False, so a NaN inclination counted as a correct read, and the
                # satellite number was collected but never compared
                if c["kind"] == "valid" and not _read_ok(x["ok"], c):
                    bad_read.append(c["id"])
        validated = acc["valid"] == tot["valid"] and not bad_read
        wrong = {k: (acc[k] if not SHOULD_ACCEPT.get(k) else tot[k] - acc[k]) for k in KINDS}
        per_impl[n] = {"accepted": acc, "total": tot, "validated": validated, "valid_misread": bad_read,
                       "verdict_errors": wrong, "lineage": impls[n].get("lineage")}
    return {"cases": len(cases), "kinds": {k: sum(1 for c in cases if c["kind"] == k) for k in KINDS}, "per_impl": per_impl}
