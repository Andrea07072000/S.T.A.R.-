# -*- coding: utf-8 -*-
"""XC-006: Lambert v1 — star_lambert (universal variables) vs hapsira (Izzo), lignaggi diversi, venv diversi.
Caso pubblicato Curtis Ex. 5.2 come riferimento + 20 casi casuali (seed fisso, LEO-GEO, 0 rivoluzioni)."""
import json, random, sys
from pathlib import Path
from star_crosscheck import Engine, crosscheck
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "08_PROTOTYPES/star_lambert"))
from star_lambert import lambert
HAPSIRA = """
import numpy as np, astropy.units as u, hapsira
from hapsira.iod import izzo
from hapsira.bodies import Earth
VERSION = hapsira.__version__
def compute(i):
    v1, v2 = izzo.lambert(Earth.k, np.array(i['r1'])*u.km, np.array(i['r2'])*u.km, i['tof']*u.s)
    return [float(x) for x in v1.to(u.km/u.s).value]
"""
engines = [Engine("star_lambert", "universal variables (BMW/Curtis)", lambda i: list(lambert(i["r1"], i["r2"], i["tof"])[0]), version="0.1"),
           Engine("hapsira-izzo", "Izzo 2015", python=str(ROOT / ".venvs/hapsira/Scripts/python.exe"), code=HAPSIRA)]
cases = [({"r1": [5000, 10000, 2100], "r2": [-14600, 2500, 7000], "tof": 3600}, {"value": [-5.9925, 1.9254, 3.2456], "source": "Curtis, Orbital Mechanics for Engineering Students, Ex. 5.2", "tolerance": 5e-4})]
rnd = random.Random(42)
while len(cases) < 21:
    import math
    a, b = rnd.uniform(6800, 42000), rnd.uniform(6800, 42000)
    th1, th2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
    if abs(math.sin(th2 - th1)) < 0.2: continue
    r1 = [a * math.cos(th1), a * math.sin(th1), rnd.uniform(-500, 500)]
    r2 = [b * math.cos(th2), b * math.sin(th2), rnd.uniform(-500, 500)]
    cases.append(({"r1": r1, "r2": r2, "tof": rnd.uniform(1800, 40000)}, None))
out, verdicts = [], {}
for inp, ref in cases:
    bnd = crosscheck("Lambert v1", inp, engines, 1e-6, "km/s", "norm", reference=ref)
    out.append(bnd); verdicts[bnd["verdict"]] = verdicts.get(bnd["verdict"], 0) + 1
diffs = [p["diff"] for b in out for p in b["pairs"]]
print("verdetti:", verdicts, "| max diff km/s:", max(diffs) if diffs else None, "| rif Curtis max_dev:", out[0]["reference"]["max_dev"])
for b in out:
    if b["verdict"] != "AGREE": print("NON AGREE:", b["inputs"], [ (r["engine"], r["state"], r.get("error","")[:80]) for r in b["engines"]], [p["diff"] for p in b["pairs"]])
Path(__file__).resolve().parents[1].joinpath("evidence", "XC-006_lambert_evidence.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
