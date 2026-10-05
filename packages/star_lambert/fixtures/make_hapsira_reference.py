"""Freezes Lambert solutions from hapsira (poliastro fork, Izzo 2015 algorithm: an independent lineage from the Curtis
universal-variable method of star_lambert). Run with the hapsira venv; output hapsira_reference.json is committed so
the test needs no hapsira at run time. Geometries: seeded random 3-D LEO-GEO radii, transfer angles 20..340 deg,
times of flight between 0.15 and 0.9 of the minimum-energy-ish scale, both directions; zero revolutions only."""
import json
import math
import random
from pathlib import Path

import astropy.units as u
from hapsira.iod import izzo

MU = 398600.4418
rng = random.Random(20261004)
cases = []
while len(cases) < 24:
    r1n, r2n = rng.uniform(6700, 42000), rng.uniform(6700, 42000)
    th, inc = math.radians(rng.uniform(20, 340)), math.radians(rng.uniform(-80, 80))
    ax = rng.uniform(0, 2 * math.pi)
    r1 = [r1n * math.cos(ax), r1n * math.sin(ax), rng.uniform(-0.3, 0.3) * r1n]
    n1 = math.sqrt(sum(x * x for x in r1))
    r1 = [x * r1n / n1 for x in r1]
    # second vector: rotate r1 direction by th inside a plane tilted by inc
    e1 = [x / r1n for x in r1]
    k = [0.0, 0.0, 1.0]
    e2 = [k[1] * e1[2] - k[2] * e1[1], k[2] * e1[0] - k[0] * e1[2], k[0] * e1[1] - k[1] * e1[0]]
    m = math.sqrt(sum(x * x for x in e2))
    e2 = [x / m for x in e2]
    e3 = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
    d = [math.cos(inc) * a + math.sin(inc) * b for a, b in zip(e2, e3)]
    r2 = [r2n * (math.cos(th) * a + math.sin(th) * b) for a, b in zip(e1, d)]
    a_min = (r1n + r2n + math.dist(r1, r2)) / 4
    tof = rng.uniform(0.15, 0.9) * math.pi * math.sqrt(a_min ** 3 / MU)
    prograde = rng.random() < 0.5
    try:
        v1, v2 = izzo.lambert(MU * u.km ** 3 / u.s ** 2, r1 * u.km, r2 * u.km, tof * u.s, M=0, prograde=prograde)
    except Exception as e:  # noqa: BLE001 - recorded, not hidden
        print("skip", e)
        continue
    cases.append({"r1": r1, "r2": r2, "tof": tof, "prograde": prograde,
                  "v1": [float(x) for x in v1.to_value(u.km / u.s)], "v2": [float(x) for x in v2.to_value(u.km / u.s)]})
import hapsira
out = {"source": f"hapsira {hapsira.__version__} iod.izzo.lambert, M=0", "mu": MU, "cases": cases}
Path(__file__).with_name("hapsira_reference.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(len(cases), out["source"])
