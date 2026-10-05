# -*- coding: utf-8 -*-
"""tdb_audit — cross-audit of TDB - TT implementations (geocentric), S.T.A.R., 2026-10-05.

Each implementation runs in its own interpreter through a driver defining tdb_minus_tt(jd_tt) -> seconds.
Probe validation (before any comparison is read): every implementation must agree with the published low-precision
formula TDB - TT = 0.001657 sin g + 0.000014 sin 2g, g = 357.53 + 0.9856003 (JD_TT - 2451545.0) deg (Explanatory
Supplement to the Astronomical Almanac; stated accuracy ~30 us) to within 50 us on every epoch, else it is NOT
validated and excluded from the comparison. Then every pair of validated implementations is compared on the same
epochs: divergence envelope overall and per century. The audit reports agreement, not correctness.
"""
from __future__ import annotations

import itertools
import json
import math
import subprocess
from typing import Dict, List

from audit_guard import finite_rows  # a NaN must be a refusal, never vanish inside max() (2026-10-05)

VALIDATION_TOL_S = 50e-6
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __ta_json\n__ta_out = []\nfor __ta_jd in payload['epochs']:\n"
          "    try:\n        __ta_out.append({'v': float(tdb_minus_tt(__ta_jd))})\n"
          "    except Exception as __ta_e:\n        __ta_out.append({'error': type(__ta_e).__name__ + ': ' + str(__ta_e)[:80]})\n"
          "print(__ta_json.dumps(__ta_out))\n")


def low_precision(jd_tt: float) -> float:
    g = math.radians(357.53 + 0.9856003 * (jd_tt - 2451545.0))
    return 0.001657 * math.sin(g) + 0.000014 * math.sin(2.0 * g)


def default_epochs(n: int = 401) -> List[float]:
    """n epochs evenly spread over 1900-01-01 .. 2100-01-01 TT (plus J2000 exactly)."""
    a, b = 2415020.5, 2488069.5
    return sorted({a + (b - a) * k / (n - 1) for k in range(n)} | {2451545.0})


def run(command: List[str], driver: str, epochs: List[float], env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "epochs": epochs}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def audit(impls: Dict[str, Dict], epochs: List[float] | None = None) -> Dict:
    epochs = epochs or default_epochs()
    res = {n: finite_rows(run(i["command"], i["driver"], epochs, i.get("env")), ["v"]) for n, i in impls.items()}
    validation = {}
    for n, rows in res.items():
        errs = [abs(x["v"] - low_precision(jd)) for jd, x in zip(epochs, rows) if "v" in x]
        refused = sum(1 for x in rows if "error" in x)
        validation[n] = {"max_dev_from_published_s": max(errs) if errs else None, "refused": refused,
                         "valid": bool(errs) and refused == 0 and max(errs) <= VALIDATION_TOL_S,
                         "lineage": impls[n].get("lineage")}
    ok = sorted(n for n in res if validation[n]["valid"])
    pairs = {}
    for a, b in itertools.combinations(ok, 2):
        d = [(jd, abs(res[a][k]["v"] - res[b][k]["v"])) for k, jd in enumerate(epochs)]
        by_century: Dict[str, float] = {}
        for jd, x in d:
            c = "19xx" if jd < 2451544.5 else "20xx"
            by_century[c] = max(by_century.get(c, 0.0), x)
        pairs[f"{a}|{b}"] = {"max_s": max(x for _, x in d), "n": len(d), "max_s_by_century": by_century,
                             "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    return {"epochs": len(epochs), "validation": validation, "validated": ok, "pairs": pairs}
