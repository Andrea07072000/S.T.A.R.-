# -*- coding: utf-8 -*-
"""star_crosscheck — cross-solver verification fabric (S.T.A.R., 2026-10-03).

The question it answers: "do independent engines agree on this quantity, within a stated tolerance, and how
independent are they really?" Not "does one tool run".

Rules built into the code (each one has a test that fails if it is removed):
1. LINEAGE: every engine declares where its model/data come from (e.g. "JPL DE440", "VSOP87", "Vallado SGP4").
   Engines with the same lineage are ONE witness, not several. Agreement needs >= 2 distinct lineages.
2. A failed engine is never a vote for agreement: the verdict becomes DEGRADED, or INSUFFICIENT_INDEPENDENCE.
3. Engines may run in their own isolated Python environment (subprocess + JSON), so tools whose dependencies
   conflict can still be compared — interoperability is part of the product.
4. Every run returns an evidence bundle (inputs, engine versions, lineages, raw values, pairwise differences,
   tolerance, verdict, environment) with a sha256 over its canonical JSON.

Verdicts: AGREE · DISAGREE · INSUFFICIENT_INDEPENDENCE · DEGRADED.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence

AGREE, DISAGREE, INSUFFICIENT, DEGRADED = "AGREE", "DISAGREE", "INSUFFICIENT_INDEPENDENCE", "DEGRADED"


@dataclass
class Engine:
    """One way of computing the quantity. Either `func` (in-process) or `python` + `code` (isolated venv).

    In isolated mode `code` must define `compute(inputs) -> number | list[number]` and may print nothing else;
    the runner sends `inputs` as JSON on stdin and reads `{"value": ..., "version": ...}` from stdout.
    """
    name: str
    lineage: str
    func: Optional[Callable[[Dict[str, Any]], Any]] = None
    python: Optional[str] = None
    code: Optional[str] = None
    version: str = "unknown"
    timeout_s: float = 120.0

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            if self.func is not None:
                value, version = self.func(inputs), self.version
            elif self.python and self.code:
                value, version = _run_isolated(self.python, self.code, inputs, self.timeout_s)
            else:
                raise ValueError("engine has neither func nor python+code")
            return {"engine": self.name, "lineage": self.lineage, "version": version, "state": "OK",
                    "value": _as_list(value), "elapsed_s": round(time.perf_counter() - t0, 4)}
        except Exception as e:  # noqa: BLE001  a failure is recorded, never converted into a value
            return {"engine": self.name, "lineage": self.lineage, "version": self.version, "state": "FAILED",
                    "error": f"{type(e).__name__}: {e}"[:400], "elapsed_s": round(time.perf_counter() - t0, 4)}


_RUNNER = r'''
import json, sys
_inputs = json.loads(sys.stdin.read())
_ns = {}
exec(compile(_SRC, "<engine>", "exec"), _ns)
_v = _ns["compute"](_inputs)
_ver = _ns.get("VERSION", "unknown")
sys.stdout.write("\n@@STAR_XC@@" + json.dumps({"value": _v, "version": str(_ver)}))
'''


def _run_isolated(python: str, code: str, inputs: Dict[str, Any], timeout_s: float):
    prog = "_SRC = " + repr(code) + "\n" + _RUNNER
    p = subprocess.run([python, "-c", prog], input=json.dumps(inputs), capture_output=True, text=True, timeout=timeout_s)
    if p.returncode != 0 or "@@STAR_XC@@" not in p.stdout:
        raise RuntimeError(f"isolated engine failed (rc={p.returncode}): {(p.stderr or p.stdout)[-300:]}")
    out = json.loads(p.stdout.rsplit("@@STAR_XC@@", 1)[1])
    return out["value"], out["version"]


def _number(x) -> float:
    # 2026-10-05 probe: "1" (str) and True (bool) were accepted as numbers; NaN/inf compared as values
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError(f"engine returned {type(x).__name__} {x!r}, not a number")
    if not math.isfinite(x):
        raise ValueError(f"engine returned a non-finite value {x!r}")
    return float(x)


def _as_list(v) -> List[float]:
    out = [_number(x) for x in v] if isinstance(v, (list, tuple)) else [_number(v)]
    if not out:
        raise ValueError("engine returned an empty vector")   # used to crash crosscheck() in max()
    return out


def _lineage_key(lineage: str) -> str:
    # 'ERFA' and 'erfa', 'SOFA' and 'SOFA ' are ONE lineage (R2); they used to count as two independent witnesses
    return " ".join(str(lineage).split()).casefold()


DIFF_MODES = ("max_abs", "norm")


def _diff(a: List[float], b: List[float], mode: str) -> float:
    if len(a) != len(b):
        return math.inf
    if mode == "norm":                                     # vectors: Euclidean distance
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    return max(abs(x - y) for x, y in zip(a, b))           # scalars / component-wise: max abs difference


def crosscheck(quantity: str, inputs: Dict[str, Any], engines: Sequence[Engine], tolerance: float,
               unit: str, diff_mode: str = "max_abs", reference: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run every engine on the same inputs and return a verdict + evidence bundle.

    reference (optional): a published value {"value": ..., "source": "..."}; it is compared too, but it is reported
    separately and never counts as an engine lineage (a citation is not a computation).
    """
    # 2026-10-05 probe: an infinite tolerance gave AGREE for 1 vs 1e9, a misspelt diff_mode silently fell back to
    # max_abs (AGREE where 'norm' disagrees), an infinite reference tolerance hid a wrong published value, and an
    # empty lineage name counted as a witness. A verification tool must refuse such a configuration.
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) \
            or tolerance < 0:
        raise ValueError(f"tolerance must be finite and >= 0, got {tolerance!r}")
    if diff_mode not in DIFF_MODES:
        raise ValueError(f"diff_mode must be one of {DIFF_MODES}, got {diff_mode!r}")
    if reference is not None:
        rt = reference.get("tolerance", 0.0)
        if isinstance(rt, bool) or not isinstance(rt, (int, float)) or not math.isfinite(rt) or rt < 0:
            raise ValueError(f"reference tolerance must be finite and >= 0, got {rt!r}")
    if any(not _lineage_key(e.lineage) for e in engines):
        raise ValueError("every engine needs a non-empty lineage")
    results = [e.run(inputs) for e in engines]
    ok = [r for r in results if r["state"] == "OK"]
    failed = [r for r in results if r["state"] != "OK"]
    pairs = []
    for a, b in itertools.combinations(ok, 2):
        d = _diff(a["value"], b["value"], diff_mode)
        pairs.append({"a": a["engine"], "b": b["engine"],
                      "same_lineage": _lineage_key(a["lineage"]) == _lineage_key(b["lineage"]),
                      "diff": d, "within_tol": d <= tolerance})
    first_name = {}                                         # one reported name per normalised lineage (bundle hashes
    for r in ok:                                            # of existing campaigns stay identical)
        first_name.setdefault(_lineage_key(r["lineage"]), r["lineage"])
    lineages = sorted(first_name.values())
    cross = [p for p in pairs if not p["same_lineage"]]
    if any(not p["within_tol"] for p in cross):
        verdict = DISAGREE
    elif len(lineages) < 2:
        verdict = INSUFFICIENT
    elif failed:
        verdict = DEGRADED                                  # independent engines agree, but not all engines ran
    else:
        verdict = AGREE
    ref_check = None
    if reference is not None and ok:
        rv = _as_list(reference["value"])
        devs = {r["engine"]: _diff(r["value"], rv, diff_mode) for r in ok}
        # a printed reference has its own precision (e.g. 4 decimals -> 5e-5): compare against the LARGER of the
        # engine tolerance and the reference tolerance (found by XC-006: Curtis Ex. 5.2 printed to 1e-4 vs tol 1e-6)
        ref_tol = max(tolerance, float(reference.get("tolerance", 0.0)))
        ref_check = {"source": reference.get("source"), "value": rv, "max_dev": max(devs.values()), "ref_tolerance": ref_tol,
                     "within_tol": max(devs.values()) <= ref_tol, "per_engine": devs}
        if not ref_check["within_tol"] and verdict == AGREE:
            verdict = DISAGREE                              # engines agree with each other but not with the published value
    bundle = {
        "schema": "star_crosscheck/1", "quantity": quantity, "unit": unit, "inputs": inputs,
        "tolerance": tolerance, "diff_mode": diff_mode, "engines": results, "pairs": pairs,
        "independent_lineages": lineages, "n_failed": len(failed), "reference": ref_check, "verdict": verdict,
        "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    bundle["sha256"] = bundle_sha256(bundle)
    return bundle


def bundle_sha256(bundle: Dict[str, Any]) -> str:
    """Identity of a RESULT: timing, run time and the hash itself are excluded (they vary run to run, the evidence
    must not). Anyone can recompute it to check that a bundle was not altered (CLI: star-xc verify-bundle)."""
    # environment (python, platform) is RECORDED in the bundle but is not part of the result identity: the same
    # result computed on another machine must have the same hash (first version included it: limitation found
    # when reproducing XC-006, fixed 2026-10-03)
    stable = {k: v for k, v in bundle.items() if k not in ("run_at", "sha256", "environment")}
    stable["engines"] = [{k: v for k, v in r.items() if k != "elapsed_s"} for r in bundle.get("engines", [])]
    canon = json.dumps(stable, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode()).hexdigest()
