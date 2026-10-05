# -*- coding: utf-8 -*-
"""XC-011: ECEF -> WGS-84 geodetic near the surface (-1 km .. 100 km), three lineages (S.T.A.R., 2026-10-03).
Engines: star_geodesy (iterative, S.T.A.R.) · PROJ via pyproj (EPSG:4978 -> 4979) · pymap3d.
Value: [lat, lon] in nano-degrees and h in units of 0.1 mm, so one tolerance (10) means 1e-8 deg and 1 mm.
Scope: near-surface only. Above ~1000 km the third-party engines diverge (09_DISCOVERIES DISC-GEO-001)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from star_crosscheck import Engine, crosscheck

ROOT = Path(__file__).resolve().parents[3]
PY = lambda n: str(ROOT / ".venvs" / n / "Scripts" / "python.exe")
sys.path.insert(0, str(ROOT / "08_PROTOTYPES" / "star_geodesy"))
from star_geodesy import ecef_to_geodetic, geodetic_to_ecef  # noqa: E402

S = lambda la, lo, h: [round(la * 1e9), round(lo * 1e9), round(h * 1e4)]
PROJ_CODE = """
import pyproj
from pyproj import Transformer
VERSION = pyproj.__version__ + "/PROJ " + pyproj.proj_version_str
T = Transformer.from_crs("EPSG:4978", "EPSG:4979", always_xy=True)
def compute(i):
    lo, la, h = T.transform(*i["xyz"])
    return [round(la * 1e9), round(lo * 1e9), round(h * 1e4)]
"""
PYMAP_CODE = """
import pymap3d
VERSION = getattr(pymap3d, "__version__", "?")
def compute(i):
    la, lo, h = pymap3d.ecef2geodetic(*i["xyz"])
    return [round(float(la) * 1e9), round(float(lo) * 1e9), round(float(h) * 1e4)]
"""
ENGINES = [Engine(name="star_geodesy", lineage="S.T.A.R. iterative latitude", func=lambda i: S(*ecef_to_geodetic(*i["xyz"])), version="0.1.0"),
           Engine(name="pyproj", lineage="PROJ (OSGeo)", python=PY("pyproj"), code=PROJ_CODE),
           Engine(name="pymap3d", lineage="pymap3d (scivision)", python=PY("pymap3d"), code=PYMAP_CODE)]
POINTS = [(0, 0, 0), (45, 7.7, 300), (-33.9, 18.4, 15), (64.1, -21.9, 50), (89.5, 120, 10), (-75, -60, 3000),
          (10, 100, 100000), (51.5, -0.13, -1000)]
CASES = [{"xyz": [round(c, 3) for c in geodetic_to_ecef(*p)], "geodetic_in": list(p)} for p in POINTS]


def run():
    out, verdicts = [], {}
    for inp in CASES:
        b = crosscheck(quantity="Geodetic [lat ndeg, lon ndeg, h 0.1mm]", inputs=inp, engines=ENGINES, tolerance=10,
                       unit="ndeg / 0.1 mm", diff_mode="max_abs")
        out.append(b)
        verdicts[b["verdict"]] = verdicts.get(b["verdict"], 0) + 1
    diffs = [p["diff"] for b in out for p in b["pairs"]]
    print(f"XC-011 verdicts: {verdicts} | max diff: {max(diffs) if diffs else None}")
    path = ROOT / "08_PROTOTYPES" / "star_crosscheck" / "evidence" / "XC-011_geodesy_ecef_evidence.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"Evidence written to {path}")
    return out


if __name__ == "__main__":
    run()
