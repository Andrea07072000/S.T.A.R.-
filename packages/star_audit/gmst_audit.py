# -*- coding: utf-8 -*-
"""gmst_audit — cross-audit of Greenwich Mean Sidereal Time implementations, S.T.A.R., 2026-10-05.

Each implementation runs in its own interpreter through a driver defining gmst_deg(jd_ut1) -> degrees in [0, 360).
Where a model needs TT (IAU 2006), drivers use TT = UT1 + 69.184 s (the 2026 value of TT - UT1 within ~0.1 s; its
effect on GMST is below 1 microarcsecond). Probe validation (before any comparison is read): Vallado's published
Example 3-5 — GMST = 152.578787810 deg at 1992-08-20 12:14:00 UT1 (IAU 1982 model) — must be reproduced within
0.1 arcsec (models differ by milliarcseconds); otherwise the implementation is excluded. Then every pair of validated
implementations is compared on 201 epochs 1950-2050: divergence envelope in arcsec (wrap-safe), per half-century.
The audit reports agreement and model dependence, not correctness.
"""
from __future__ import annotations

import itertools
import json
import subprocess
from typing import Dict, List

from audit_guard import finite_rows  # a NaN must be a refusal, never vanish inside max() (2026-10-05)

VALLADO_JD_UT1 = 2448855.009722222        # 1992-08-20 12:14:00 UT1
VALLADO_GMST_DEG = 152.578787810           # Vallado, Fundamentals of Astrodynamics, Example 3-5 (IAU 1982)
VALIDATION_TOL_ARCSEC = 0.1
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __ga_json\n__ga_out = []\nfor __ga_jd in payload['epochs']:\n"
          "    try:\n        __ga_out.append({'v': float(gmst_deg(__ga_jd)) % 360.0})\n"
          "    except Exception as __ga_e:\n        __ga_out.append({'error': type(__ga_e).__name__ + ': ' + str(__ga_e)[:80]})\n"
          "print(__ga_json.dumps(__ga_out))\n")


def arcsec_diff(a_deg: float, b_deg: float) -> float:
    """|a - b| in arcsec on the circle (359.9999 vs 0.0001 deg is 0.72 arcsec, not 1296000)."""
    d = (a_deg - b_deg + 180.0) % 360.0 - 180.0
    return abs(d) * 3600.0


def default_epochs(n: int = 201) -> List[float]:
    a, b = 2433282.5, 2469807.5            # 1950-01-01 .. 2050-01-01
    return [a + (b - a) * k / (n - 1) for k in range(n)]


def run(command: List[str], driver: str, epochs: List[float], env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "epochs": epochs}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def audit(impls: Dict[str, Dict], epochs: List[float] | None = None) -> Dict:
    epochs = epochs or default_epochs()
    cases = [VALLADO_JD_UT1] + epochs
    res = {n: finite_rows(run(i["command"], i["driver"], cases, i.get("env")), ["v"]) for n, i in impls.items()}
    validation = {}
    for n, rows in res.items():
        x = rows[0]
        refused = sum(1 for r in rows if "error" in r)
        err = arcsec_diff(x["v"], VALLADO_GMST_DEG) if "v" in x else None
        validation[n] = {"vallado_err_arcsec": err, "refused": refused, "lineage": impls[n].get("lineage"),
                         "valid": err is not None and refused == 0 and err <= VALIDATION_TOL_ARCSEC}
    ok = sorted(n for n in res if validation[n]["valid"])
    pairs = {}
    for a, b in itertools.combinations(ok, 2):
        by_half: Dict[str, float] = {}
        mx = 0.0
        for k, jd in enumerate(epochs, start=1):
            d = arcsec_diff(res[a][k]["v"], res[b][k]["v"])
            h = "1950-2000" if jd < 2451544.5 else "2000-2050"
            by_half[h] = max(by_half.get(h, 0.0), d)
            mx = max(mx, d)
        pairs[f"{a}|{b}"] = {"max_arcsec": mx, "n": len(epochs), "max_arcsec_by_half_century": by_half,
                             "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    return {"epochs": len(epochs), "validation": validation, "validated": ok, "pairs": pairs}
