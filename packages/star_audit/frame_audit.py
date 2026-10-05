# -*- coding: utf-8 -*-
"""frame_audit — independent cross-audit of TEME -> GCRS transformations (the step every SGP4 user needs to put a TLE
state into an inertial frame), S.T.A.R., Claude Code, 2026-10-04.

Each implementation runs in its own interpreter through a driver defining teme_to_gcrs(utc_iso, r_km) -> [x, y, z] km.
Probe validation (before any comparison is read): Vallado's published example (Fundamentals of Astrodynamics, 4th ed.,
TEME -> GCRF, 2004-04-06 07:51:28.386009 UTC) must be reproduced to < 1 m by an implementation for its results to count.
Then every pair of implementations is compared on the same epochs (1980..2050) and vectors: the output is the
divergence envelope per pair and per epoch, plus each implementation's refusals. No implementation is the truth outside
the published case; the audit reports agreement, not correctness.
"""
from __future__ import annotations

import itertools
import json
import math
import subprocess
from typing import Dict, List

VALLADO_UTC = "2004-04-06T07:51:28.386009"
VALLADO_TEME = [5094.18016210, 6127.64465950, 6380.34453270]
VALLADO_GCRF = [5102.50895790, 6123.01140070, 6378.13692820]   # km, Vallado ex. 3-15 / teme2eci companion values

# runner names are prefixed __fa_ so they cannot shadow driver globals (2026-10-04: a loop variable 'u' overwrote
# astropy.units imported as u, and every astropy case 'failed' — a probe defect, not a library one)
RUNNER = ("\nimport json as __fa_json\n__fa_out = []\nfor __fa_t, __fa_r in payload['cases']:\n"
          "    try:\n        __fa_out.append({'r': [float(__fa_x) for __fa_x in teme_to_gcrs(__fa_t, __fa_r)]})\n"
          "    except Exception as __fa_e:\n"
          "        __fa_out.append({'error': type(__fa_e).__name__ + ': ' + str(__fa_e)[:80]})\n"
          "print(__fa_json.dumps(__fa_out))\n")
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"


def default_cases() -> List:
    """Vallado case first, then 3 vectors x 15 epochs from 1980 to 2050."""
    vecs = [VALLADO_TEME, [-6045.0, -3490.0, 2500.0], [42164.0, 0.0, 0.0]]
    years = list(range(1980, 2051, 5))
    return [[VALLADO_UTC, VALLADO_TEME]] + [[f"{y}-06-15T12:00:00", v] for y in years for v in vecs]


def run(command: List[str], driver: str, cases: List) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases}),
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def audit(impls: Dict[str, Dict], cases: List | None = None) -> Dict:
    """impls = {name: {'command': [...], 'driver': code, 'lineage': str}}. Case 0 must be the Vallado case."""
    cases = cases or default_cases()
    res = {n: run(i["command"], i["driver"], cases) for n, i in impls.items()}
    validated = {}
    for n, rows in res.items():
        x = rows[0]
        validated[n] = ({"error_m": None, "valid": False, "why": x["error"]} if "error" in x else
                        {"error_m": math.dist(x["r"], VALLADO_GCRF) * 1000.0,
                         "valid": math.dist(x["r"], VALLADO_GCRF) * 1000.0 < 1.0})
    pairs = {}
    for a, b in itertools.combinations(sorted(res), 2):
        diffs = [(cases[k][0][:4], math.dist(res[a][k]["r"], res[b][k]["r"]) * 1000.0)
                 for k in range(1, len(cases)) if "r" in res[a][k] and "r" in res[b][k]]
        by_year: Dict[str, float] = {}
        for y, d in diffs:
            by_year[y] = max(by_year.get(y, 0.0), d)
        pairs[f"{a}|{b}"] = {"max_m": max((d for _, d in diffs), default=None), "n": len(diffs),
                             "max_m_by_year": by_year,
                             "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    refused = {n: [cases[k][0] for k, x in enumerate(rows) if "error" in x] for n, rows in res.items()}
    return {"cases": len(cases), "validation": validated, "pairs": pairs, "refused": refused}
