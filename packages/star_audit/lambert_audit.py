"""Independent audit of Lambert solvers (zero-revolution, elliptic transfers) (S.T.A.R., 2026-10-05).

Each implementation runs in its own interpreter through a driver defining lambert(r1, r2, tof, mu) -> v1 (km/s),
prograde transfer, zero revolutions.
1. Probe validation: Curtis, Orbital Mechanics for Engineering Students, Example 5.2: r1 = (5000, 10000, 2100) km,
   r2 = (-14600, 2500, 7000) km, 3600 s, mu = 398600 -> v1 = (-5.9925, 1.9254, 3.2456) km/s (printed to 4 decimals).
2. Truth WITHOUT any Lambert solver: each case is built from a known orbit (a, e, i, raan, argp, nu1, dnu). r1, the true
   v1 and r2 come from the closed-form perifocal equations; the time of flight comes from the forward chain
   nu -> E -> M (no equation is solved). A solver is right when it returns that orbit's v1.
3. Hostile inputs (NaN, tof <= 0, zero vector, 0 and 180 degree transfers) are recorded as a category per library.
A non-finite answer on a regular case is a refusal (audit_guard), never a hidden zero in a max().
"""
from __future__ import annotations

import itertools
import json
import math
import subprocess
from typing import Dict, List

from audit_guard import driver_rows, finite_rows

MU = 398600.4418
CURTIS = {"r1": [5000.0, 10000.0, 2100.0], "r2": [-14600.0, 2500.0, 7000.0], "tof": 3600.0, "mu": 398600.0,
          "v1": [-5.9925, 1.9254, 3.2456]}
VALIDATION_TOL_KMS = 1e-4          # the printed value has 4 decimals
A_KM = (7000.0, 26600.0, 42164.0)
ECC = (0.0, 0.1, 0.5, 0.8, 0.95)
INC_DEG = (5.0, 45.0, 80.0)
DNU_DEG = (10.0, 60.0, 120.0, 170.0, 190.0, 250.0, 330.0)
HOSTILE = [("tof_nan", [7000.0, 0.0, 0.0], [0.0, 7000.0, 0.0], math.nan), ("tof_zero", [7000.0, 0.0, 0.0], [0.0, 7000.0, 0.0], 0.0),
           ("tof_negative", [7000.0, 0.0, 0.0], [0.0, 7000.0, 0.0], -100.0), ("r1_zero", [0.0, 0.0, 0.0], [0.0, 7000.0, 0.0], 3000.0),
           ("r1_nan", [math.nan, 0.0, 0.0], [0.0, 7000.0, 0.0], 3000.0), ("transfer_180", [7000.0, 0.0, 0.0], [-7000.0, 0.0, 0.0], 3000.0),
           ("transfer_0", [7000.0, 0.0, 0.0], [8000.0, 0.0, 0.0], 3000.0)]
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __la_json\n__la_out = []\nfor __la_c in payload['cases']:\n"
          "    try:\n        __la_out.append({'v': [float(x) for x in lambert(__la_c[0], __la_c[1], __la_c[2], __la_c[3])]})\n"
          "    except Exception as __la_x:\n        __la_out.append({'error': type(__la_x).__name__ + ': ' + str(__la_x)[:80]})\n"
          "print(__la_json.dumps(__la_out))\n")


def _rot(i, raan, argp, x, y):
    cO, sO, ci, si, cw, sw = math.cos(raan), math.sin(raan), math.cos(i), math.sin(i), math.cos(argp), math.sin(argp)
    return [(cO * cw - sO * sw * ci) * x + (-cO * sw - sO * cw * ci) * y,
            (sO * cw + cO * sw * ci) * x + (-sO * sw + cO * cw * ci) * y,
            (sw * si) * x + (cw * si) * y]


def _mean(nu, e):
    E = 2.0 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
    return E - e * math.sin(E)


def case(a, e, inc, raan, argp, nu1, dnu, mu=MU) -> Dict:
    """One Lambert problem with its exact answer, from the orbit (a, e, inc, raan, argp) between nu1 and nu1 + dnu."""
    p = a * (1 - e * e)
    h = math.sqrt(mu * p)
    nu2 = nu1 + dnu
    r1m, r2m = p / (1 + e * math.cos(nu1)), p / (1 + e * math.cos(nu2))
    r1 = _rot(inc, raan, argp, r1m * math.cos(nu1), r1m * math.sin(nu1))
    r2 = _rot(inc, raan, argp, r2m * math.cos(nu2), r2m * math.sin(nu2))
    v1 = _rot(inc, raan, argp, -mu / h * math.sin(nu1), mu / h * (e + math.cos(nu1)))
    n = math.sqrt(mu / a ** 3)
    dM = (_mean(nu2, e) - _mean(nu1, e)) % (2 * math.pi)
    return {"r1": r1, "r2": r2, "tof": dM / n, "mu": mu, "v1": v1, "e": e, "dnu_deg": math.degrees(dnu), "a": a}


def corpus() -> List[Dict]:
    out = []
    for k, (a, e, inc, dnu) in enumerate(itertools.product(A_KM, ECC, INC_DEG, DNU_DEG)):
        nu1 = math.radians((37.0 * k) % 360.0)                       # deterministic spread of the departure anomaly
        out.append(case(a, e, math.radians(inc), math.radians(40.0), math.radians(25.0), nu1, math.radians(dnu)))
    return out


def run(command: List[str], driver: str, cases: List, env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return driver_rows(r.stdout, len(cases))


def category(row: Dict) -> str:
    if "error" in row:
        return "error:" + row["error"].split(":")[0]
    return "nan" if any(x != x for x in row["v"]) else ("inf" if any(math.isinf(x) for x in row["v"]) else "value")


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    payload = ([[CURTIS["r1"], CURTIS["r2"], CURTIS["tof"], CURTIS["mu"]]]
               + [[c["r1"], c["r2"], c["tof"], c["mu"]] for c in cases] + [[r1, r2, tof, MU] for _, r1, r2, tof in HOSTILE])
    raw = {n: run(i["command"], i["driver"], payload, i.get("env")) for n, i in impls.items()}
    n_reg = len(cases)
    reg = {n: finite_rows(rows[: 1 + n_reg], ["v"]) for n, rows in raw.items()}
    validation = {}
    for n, rows in reg.items():
        x = rows[0]
        err = math.dist(x["v"], CURTIS["v1"]) if "v" in x and len(x["v"]) == 3 else None
        validation[n] = {"curtis_err_kms": err, "valid": err is not None and err <= VALIDATION_TOL_KMS,
                         "lineage": impls[n].get("lineage")}
    ok = sorted(n for n in reg if validation[n]["valid"])
    vs_truth = {}
    for n in ok:
        by_e: Dict[str, Dict] = {}
        for c, row in zip(cases, reg[n][1:]):
            b = by_e.setdefault(repr(c["e"]), {"max_err_kms": 0.0, "refused": 0, "n": 0})
            b["n"] += 1
            if "error" in row or len(row["v"]) != 3:
                b["refused"] += 1
                continue
            b["max_err_kms"] = max(b["max_err_kms"], math.dist(row["v"], c["v1"]))
        vs_truth[n] = by_e
    pairs = {}
    for a, b in itertools.combinations(ok, 2):
        mx = 0.0
        for k in range(1, n_reg + 1):
            if "v" in reg[a][k] and "v" in reg[b][k]:
                mx = max(mx, math.dist(reg[a][k]["v"], reg[b][k]["v"]))
        pairs[f"{a}|{b}"] = {"max_kms": mx, "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    hostile = {n: {h[0]: category(row) for h, row in zip(HOSTILE, rows[1 + n_reg:])} for n, rows in raw.items()}
    return {"cases": n_reg, "validation": validation, "validated": ok, "vs_truth": vs_truth, "pairs": pairs,
            "hostile": hostile}
