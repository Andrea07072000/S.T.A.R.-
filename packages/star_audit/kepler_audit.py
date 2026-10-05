"""Independent audit of Kepler-equation solvers (elliptic, M -> E) (S.T.A.R., 2026-10-05).

Each implementation runs in its own interpreter through a driver defining m_to_e(M, e) -> E in radians.
1. Probe validation: Vallado (Fundamentals of Astrodynamics) Example 2-1, M = 235.4 deg, e = 0.4 -> E = 220.512074767522
   deg; an implementation that misses it by more than VALIDATION_TOL_RAD is reported, not compared.
2. Truth: for each eccentricity a grid of eccentric anomalies E is mapped forward, M = E - e sin E, in 40-digit
   arithmetic (mpmath), rounded to a double, and solved back in 40 digits: the truth is the exact inverse of the double
   M actually sent to the libraries. Errors are circular (E and E + 2 pi are the same angle).
3. Hostile inputs (NaN, e = 1, e > 1, e < 0, huge M, inf): the behaviour of each library is recorded as a category
   (value / nan / error), because what a solver does outside its domain is what callers rarely check.
A non-finite answer on a regular case is a refusal (audit_guard), never a hidden zero in a max().
"""
from __future__ import annotations

import itertools
import json
import math
import subprocess
from typing import Dict, List

from audit_guard import finite_rows  # a NaN must be a refusal, never vanish inside max()

VALLADO_M_DEG, VALLADO_ECC, VALLADO_E_DEG = 235.4, 0.4, 220.512074767522
VALIDATION_TOL_RAD = 1e-9
ECCS = [0.0, 1e-6, 0.1, 0.5, 0.9, 0.99, 0.999, 0.9999]
HOSTILE = [("M_nan", math.nan, 0.5), ("e_nan", 1.0, math.nan), ("e_one", 1.0, 1.0), ("e_hyperbolic", 1.0, 1.5),
           ("e_negative", 1.0, -0.1), ("M_inf", math.inf, 0.5), ("M_huge", 1e12, 0.5), ("M_negative", -1.0, 0.5)]
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __ka_json\n__ka_out = []\nfor __ka_M, __ka_e in payload['cases']:\n"
          "    try:\n        __ka_out.append({'v': float(m_to_e(__ka_M, __ka_e))})\n"
          "    except Exception as __ka_x:\n        __ka_out.append({'error': type(__ka_x).__name__ + ': ' + str(__ka_x)[:80]})\n"
          "print(__ka_json.dumps(__ka_out))\n")


def circ(a: float, b: float) -> float:
    """|a - b| on the circle, radians."""
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def _exact_inverse(M: float, e: float, E0: float) -> float:
    from mpmath import findroot, mp, mpf, sin
    mp.dps = 40
    if e == 0.0:
        return M
    return float(findroot(lambda E: E - mpf(e) * sin(E) - mpf(M), mpf(E0)))


def corpus(n: int = 36) -> List[Dict]:
    from mpmath import mp, mpf, sin
    mp.dps = 40
    grid = [0.0, 1e-8, 1e-4, math.pi, 2 * math.pi - 1e-4] + [2 * math.pi * (k + 0.5) / n for k in range(n)]
    cases = []
    for e in ECCS:
        for E in grid:
            M = float(mpf(E) - mpf(e) * sin(mpf(E)))
            cases.append({"e": e, "M": M, "truth": _exact_inverse(M, e, E)})
    return cases


def run(command: List[str], driver: str, cases: List, env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def category(row: Dict) -> str:
    if "error" in row:
        return "error:" + row["error"].split(":")[0]
    v = row["v"]
    return "nan" if v != v else ("inf" if math.isinf(v) else "value")


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    payload = ([[math.radians(VALLADO_M_DEG), VALLADO_ECC]] + [[c["M"], c["e"]] for c in cases]
               + [[m, e] for _, m, e in HOSTILE])
    raw = {n: run(i["command"], i["driver"], payload, i.get("env")) for n, i in impls.items()}
    n_reg = len(cases)
    reg = {n: finite_rows(rows[: 1 + n_reg], ["v"]) for n, rows in raw.items()}
    validation = {}
    for n, rows in reg.items():
        x = rows[0]
        err = circ(x["v"], math.radians(VALLADO_E_DEG)) if "v" in x else None
        validation[n] = {"vallado_err_rad": err, "valid": err is not None and err <= VALIDATION_TOL_RAD,
                         "lineage": impls[n].get("lineage")}
    ok = sorted(n for n in reg if validation[n]["valid"])
    vs_truth = {}
    for n in ok:
        by_e: Dict[str, Dict] = {}
        for c, row in zip(cases, reg[n][1:]):
            b = by_e.setdefault(repr(c["e"]), {"max_err_rad": 0.0, "refused": 0, "n": 0})
            b["n"] += 1
            if "error" in row:
                b["refused"] += 1
                continue
            b["max_err_rad"] = max(b["max_err_rad"], circ(row["v"], c["truth"]))
        vs_truth[n] = by_e
    pairs = {}
    for a, b in itertools.combinations(ok, 2):
        mx = 0.0
        for k in range(1, n_reg + 1):
            if "v" in reg[a][k] and "v" in reg[b][k]:
                mx = max(mx, circ(reg[a][k]["v"], reg[b][k]["v"]))
        pairs[f"{a}|{b}"] = {"max_rad": mx, "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    hostile = {n: {name: category(row) for (name, _, _), row in zip(HOSTILE, rows[1 + n_reg:])}
               for n, rows in raw.items()}
    return {"cases": n_reg, "eccentricities": ECCS, "validation": validation, "validated": ok,
            "vs_truth": vs_truth, "pairs": pairs, "hostile": hostile}
