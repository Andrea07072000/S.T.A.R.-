# -*- coding: utf-8 -*-
"""elements_audit — cross-audit of state-vector -> classical orbital elements implementations, S.T.A.R., 2026-10-05.

Each implementation runs in its own interpreter through a driver defining elements(r_km, v_kms, mu) -> dict with
p (semi-latus rectum, km), e, i, raan, argp, nu (degrees). Probe validation: Vallado's published Example 2-5
(r = 6524.834, 6862.875, 6448.296 km; v = 4.901327, 5.533756, -1.976341 km/s) -> p 11067.790 km, e 0.832853,
i 87.870, RAAN 227.898, argp 53.38, nu 92.335 deg, within (0.01 km, 1e-5, 0.01 deg). Corpus (seeded): 60 regular
elliptic states + 20 SINGULAR ones (near-circular, near-equatorial, both), generated here from elements with an
independent formula. Regular cases: per-element envelopes against the generating truth and between implementations.
Singular cases: each implementation's CONVENTION is recorded (which angles it reports and how), since there the
classical elements are not uniquely defined. The audit reports agreement and conventions, not correctness.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import subprocess
from typing import Dict, List

MU = 398600.4418
VALLADO_RV = ([6524.834, 6862.875, 6448.296], [4.901327, 5.533756, -1.976341])
VALLADO_COE = {"p": 11067.790, "e": 0.832853, "i": 87.870, "raan": 227.898, "argp": 53.38, "nu": 92.335}
VALIDATION_TOL = {"p": 0.01, "e": 1e-5, "i": 0.01, "raan": 0.01, "argp": 0.01, "nu": 0.01}
ELEMENTS = ("p", "e", "i", "raan", "argp", "nu")
ANGLES = ("i", "raan", "argp", "nu")
BOOT = "import json, sys\npayload = json.loads(sys.stdin.read())\nexec(payload['code'])\n"
RUNNER = ("\nimport json as __ea_json\n__ea_out = []\nfor __ea_r, __ea_v in payload['cases']:\n"
          "    try:\n        __ea_x = elements(__ea_r, __ea_v, payload['mu'])\n"
          "        __ea_out.append({'c': {__ea_k: float(__ea_x[__ea_k]) for __ea_k in ('p','e','i','raan','argp','nu')}})\n"
          "    except Exception as __ea_e:\n        __ea_out.append({'error': type(__ea_e).__name__ + ': ' + str(__ea_e)[:80]})\n"
          "print(__ea_json.dumps(__ea_out))\n")


def coe_to_rv(p, e, i, raan, argp, nu, mu=MU):
    """Perifocal -> inertial (standard textbook rotation R3(-raan) R1(-i) R3(-argp)); angles in degrees."""
    i, raan, argp, nu = (math.radians(x) for x in (i, raan, argp, nu))
    rpf = [p * math.cos(nu) / (1 + e * math.cos(nu)), p * math.sin(nu) / (1 + e * math.cos(nu)), 0.0]
    vpf = [-math.sqrt(mu / p) * math.sin(nu), math.sqrt(mu / p) * (e + math.cos(nu)), 0.0]
    cO, sO, ci, si, cw, sw = math.cos(raan), math.sin(raan), math.cos(i), math.sin(i), math.cos(argp), math.sin(argp)
    m = [[cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci, sO * si],
         [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci, -cO * si],
         [sw * si, cw * si, ci]]
    return [sum(m[k][j] * rpf[j] for j in range(3)) for k in range(3)], [sum(m[k][j] * vpf[j] for j in range(3)) for k in range(3)]


def corpus(seed: int = 20261005) -> List[Dict]:
    rng = random.Random(seed)
    out = []
    for k in range(60):
        coe = {"p": rng.uniform(6800, 40000), "e": rng.uniform(0.001, 0.8), "i": rng.uniform(1, 179),
               "raan": rng.uniform(0, 360), "argp": rng.uniform(0, 360), "nu": rng.uniform(0, 360)}
        r, v = coe_to_rv(**coe)
        out.append({"id": f"reg{k}", "kind": "regular", "truth": coe, "r": r, "v": v})
    for k in range(20):
        kind = ("circular", "equatorial", "circular_equatorial")[k % 3] if k < 18 else "circular_equatorial"
        coe = {"p": rng.uniform(6800, 40000), "e": 1e-12 if "circular" in kind else rng.uniform(0.01, 0.5),
               "i": 1e-10 if "equatorial" in kind else rng.uniform(5, 175),
               "raan": rng.uniform(0, 360), "argp": rng.uniform(0, 360), "nu": rng.uniform(0, 360)}
        r, v = coe_to_rv(**coe)
        out.append({"id": f"sing{k}", "kind": kind, "truth": coe, "r": r, "v": v})
    return out


def classify(x: float) -> str:
    """How an implementation reports a possibly undefined angle: nan, Vallado's sentinel (999999.1 rad -> huge deg),
    exactly/near zero (a convention), or a value."""
    if x != x:
        return "nan"
    if abs(x) > 1e5:
        return "sentinel"
    if abs(x) < 1e-9:
        return "0"
    return "value"


def ang(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def diff(x, y, k):
    return ang(x[k], y[k]) if k in ANGLES else abs(x[k] - y[k])


def run(command: List[str], driver: str, cases: List, env: Dict | None = None) -> List[Dict]:
    r = subprocess.run(command + [BOOT], input=json.dumps({"code": driver + RUNNER, "cases": cases, "mu": MU}),
                       capture_output=True, text=True, timeout=1800, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"implementation run failed: {r.stderr[-300:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def audit(impls: Dict[str, Dict], cases: List[Dict] | None = None) -> Dict:
    cases = cases or corpus()
    payload = [list(VALLADO_RV)] + [[c["r"], c["v"]] for c in cases]
    res = {n: run(i["command"], i["driver"], payload, i.get("env")) for n, i in impls.items()}
    validation = {}
    for n, rows in res.items():
        x = rows[0]
        if "error" in x:
            validation[n] = {"valid": False, "why": x["error"], "lineage": impls[n].get("lineage")}
            continue
        dev = {k: diff(x["c"], VALLADO_COE, k) for k in ELEMENTS}
        validation[n] = {"valid": all(dev[k] <= VALIDATION_TOL[k] for k in ELEMENTS), "dev": dev,
                         "lineage": impls[n].get("lineage")}
    ok = sorted(n for n in res if validation[n]["valid"])
    regular = [k for k, c in enumerate(cases, start=1) if c["kind"] == "regular"]
    vs_truth = {}
    for n in ok:
        env = {e: 0.0 for e in ELEMENTS}
        refused = 0
        for k in regular:
            if "error" in res[n][k]:
                refused += 1
                continue
            for e in ELEMENTS:
                env[e] = max(env[e], diff(res[n][k]["c"], cases[k - 1]["truth"], e))
        vs_truth[n] = {"max_dev": env, "refused": refused}
    pairs = {}
    for a, b in itertools.combinations(ok, 2):
        env = {e: 0.0 for e in ELEMENTS}
        for k in regular:
            if "c" in res[a][k] and "c" in res[b][k]:
                for e in ELEMENTS:
                    env[e] = max(env[e], diff(res[a][k]["c"], res[b][k]["c"], e))
        pairs[f"{a}|{b}"] = {"max_dev": env, "same_lineage": impls[a].get("lineage") == impls[b].get("lineage")}
    singular = {}
    for n in ok:
        conv = {}
        for k, c in enumerate(cases, start=1):
            if c["kind"] == "regular":
                continue
            x = res[n][k]
            sig = "error" if "error" in x else ",".join(f"{e}={classify(x['c'][e])}" for e in ("raan", "argp"))
            conv.setdefault(c["kind"], {}).setdefault(sig, 0)
            conv[c["kind"]][sig] += 1
        singular[n] = conv
    return {"cases": len(cases), "validation": validation, "validated": ok, "regular_vs_truth": vs_truth,
            "pairs": pairs, "singular_conventions": singular}
