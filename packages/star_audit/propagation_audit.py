"""Independent audit of two-body (Kepler) propagators, elliptic orbits (S.T.A.R., 2026-10-05).

Each implementation runs in its own interpreter through a driver defining propagate(r0, v0, tof, mu) -> [x, y, z, vx,
vy, vz] (km, km/s).
1. Probe validation: Vallado, Fundamentals of Astrodynamics, Example 2-4 (Kepler's problem): r0 = (1131.340, -2282.343,
   6672.423) km, v0 = (-5.64305, 4.30333, 2.42879) km/s, 40 min -> r = (-4219.7527, 4363.0292, -3958.7666) km,
   v = (3.689866, -1.916735, -6.112511) km/s. The constant was cross-checked with NAIF prop2b before being used.
2. Truth WITHOUT any propagator: each case is a known orbit sampled at two true anomalies with the closed-form perifocal
   equations; the time of flight is the forward chain nu -> E -> M, plus REVS whole periods (0 or 10), after which the
   exact state is unchanged - so long propagations expose loss of precision.
3. Hostile inputs (NaN, zero position, negative mu, huge time) are recorded as a category per library; each runs alone
   with a deadline, and a solver that never answers is recorded as "error:Hang".
A non-finite or wrong-length answer on a regular case is a refusal (audit_guard), never a hidden zero in a max().
"""
from __future__ import annotations

import itertools
import json
import math
import subprocess
from typing import Dict, List

from audit_guard import finite_rows

MU = 398600.4418
VALLADO = {"r0": [1131.340, -2282.343, 6672.423], "v0": [-5.64305, 4.30333, 2.42879], "tof": 2400.0,
           "r": [-4219.7527, 4363.0292, -3958.7666], "v": [3.689866, -1.916735, -6.112511]}
VALIDATION_TOL_KM, VALIDATION_TOL_KMS = 1e-3, 1e-5       # the printed values have 4 and 6 decimals
A_KM = (7000.0, 26600.0, 42164.0)
ECC = (0.0, 0.1, 0.5, 0.8, 0.95)
INC_DEG = (5.0, 63.4, 98.0)
DNU_DEG = (15.0, 100.0, 179.0, 181.0, 300.0)
REVS = (0, 10)
HOSTILE = [("tof_nan", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], math.nan, MU), ("r_zero", [0.0, 0.0, 0.0], [0.0, 7.5, 0.0], 100.0, MU),
           ("r_nan", [math.nan, 0.0, 0.0], [0.0, 7.5, 0.0], 100.0, MU), ("mu_negative", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], 100.0, -1.0),
           ("tof_huge", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], 1e12, MU), ("tof_negative", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], -3600.0, MU)]
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __pa_json\n__pa_out = []\nfor __pa_c in payload['cases']:\n"
          "    try:\n        __pa_out.append({'s': [float(x) for x in propagate(__pa_c[0], __pa_c[1], __pa_c[2], __pa_c[3])]})\n"
          "    except Exception as __pa_x:\n        __pa_out.append({'error': type(__pa_x).__name__ + ': ' + str(__pa_x)[:80]})\n"
          "print(__pa_json.dumps(__pa_out))\n")


def _rot(i, raan, argp, x, y):
    cO, sO, ci, si, cw, sw = math.cos(raan), math.sin(raan), math.cos(i), math.sin(i), math.cos(argp), math.sin(argp)
    return [(cO * cw - sO * sw * ci) * x + (-cO * sw - sO * cw * ci) * y,
            (sO * cw + cO * sw * ci) * x + (-sO * sw + cO * cw * ci) * y,
            (sw * si) * x + (cw * si) * y]


def _state(a, e, inc, raan, argp, nu, mu):
    p = a * (1 - e * e)
    h, rm = math.sqrt(mu * p), p / (1 + e * math.cos(nu))
    return (_rot(inc, raan, argp, rm * math.cos(nu), rm * math.sin(nu))
            + _rot(inc, raan, argp, -mu / h * math.sin(nu), mu / h * (e + math.cos(nu))))


def _mean(nu, e):
    E = 2.0 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
    return E - e * math.sin(E)


def case(a, e, inc, raan, argp, nu1, dnu, revs=0, mu=MU) -> Dict:
    """One propagation problem with its exact answer: the orbit (a, e, inc, raan, argp) from nu1 to nu1 + dnu."""
    s0, s1 = _state(a, e, inc, raan, argp, nu1, mu), _state(a, e, inc, raan, argp, nu1 + dnu, mu)
    n = math.sqrt(mu / a ** 3)
    dM = (_mean(nu1 + dnu, e) - _mean(nu1, e)) % (2 * math.pi)
    return {"r0": s0[:3], "v0": s0[3:], "tof": (dM + 2 * math.pi * revs) / n, "mu": mu, "truth": s1, "e": e, "revs": revs,
            "a": a, "dnu_deg": math.degrees(dnu)}


def corpus() -> List[Dict]:
    out = []
    for k, (a, e, inc, dnu, revs) in enumerate(itertools.product(A_KM, ECC, INC_DEG, DNU_DEG, REVS)):
        nu1 = math.radians((41.0 * k) % 360.0)
        out.append(case(a, e, math.radians(inc), math.radians(40.0), math.radians(25.0), nu1, math.radians(dnu), revs))
    return out


HOSTILE_DEADLINE_S = 120


def run(command: List[str], driver: str, cases: List, env: Dict | None = None, timeout: float = 1800) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases}),
                       capture_output=True, text=True, timeout=timeout, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def category(row: Dict) -> str:
    if "error" in row:
        return "error:" + row["error"].split(":")[0]
    return "nan" if any(x != x for x in row["s"]) else ("inf" if any(math.isinf(x) for x in row["s"]) else "value")


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    payload = [[VALLADO["r0"], VALLADO["v0"], VALLADO["tof"], MU]] + [[c["r0"], c["v0"], c["tof"], c["mu"]] for c in cases]
    raw = {}
    for n, i in impls.items():
        rows = run(i["command"], i["driver"], payload, i.get("env"))
        # each hostile case alone, with a deadline: the first audit hung for 30 min inside one library (2026-10-05);
        # a solver that never answers is a category ("hang"), not a reason to lose the whole audit
        for _, r, v, tof, mu in HOSTILE:
            try:
                rows += run(i["command"], i["driver"], [[r, v, tof, mu]], i.get("env"), timeout=HOSTILE_DEADLINE_S)
            except subprocess.TimeoutExpired:
                rows.append({"error": f"Hang: no answer in {HOSTILE_DEADLINE_S} s"})
        raw[n] = rows
    n_reg = len(cases)
    reg = {n: finite_rows(rows[: 1 + n_reg], ["s"]) for n, rows in raw.items()}
    validation = {}
    for n, rows in reg.items():
        x = rows[0]
        good = "s" in x and len(x["s"]) == 6
        er = math.dist(x["s"][:3], VALLADO["r"]) if good else None
        ev = math.dist(x["s"][3:], VALLADO["v"]) if good else None
        validation[n] = {"vallado_pos_err_km": er, "vallado_vel_err_kms": ev, "lineage": impls[n].get("lineage"),
                         "valid": good and er <= VALIDATION_TOL_KM and ev <= VALIDATION_TOL_KMS}
    ok = sorted(n for n in reg if validation[n]["valid"])
    vs_truth = {}
    for n in ok:
        buckets: Dict[str, Dict] = {}
        for c, row in zip(cases, reg[n][1:]):
            b = buckets.setdefault(f"e={c['e']!r},revs={c['revs']}", {"max_pos_err_km": 0.0, "max_vel_err_kms": 0.0,
                                                                     "refused": 0, "n": 0})
            b["n"] += 1
            if "error" in row or len(row["s"]) != 6:
                b["refused"] += 1
                continue
            b["max_pos_err_km"] = max(b["max_pos_err_km"], math.dist(row["s"][:3], c["truth"][:3]))
            b["max_vel_err_kms"] = max(b["max_vel_err_kms"], math.dist(row["s"][3:], c["truth"][3:]))
        vs_truth[n] = buckets
    pairs = {}
    for a, b in itertools.combinations(ok, 2):
        mx = 0.0
        for k in range(1, n_reg + 1):
            if "s" in reg[a][k] and "s" in reg[b][k] and len(reg[a][k]["s"]) == len(reg[b][k]["s"]) == 6:
                mx = max(mx, math.dist(reg[a][k]["s"][:3], reg[b][k]["s"][:3]))
        pairs[f"{a}|{b}"] = {"max_pos_km": mx, "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    hostile = {n: {h[0]: category(row) for h, row in zip(HOSTILE, rows[1 + n_reg:])} for n, rows in raw.items()}
    return {"cases": n_reg, "validation": validation, "validated": ok, "vs_truth": vs_truth, "pairs": pairs,
            "hostile": hostile}
