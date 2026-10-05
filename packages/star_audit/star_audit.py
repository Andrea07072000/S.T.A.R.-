# -*- coding: utf-8 -*-
"""star_audit — accuracy envelope of third-party ECEF->geodetic conversions vs an exact reference (S.T.A.R.,
2026-10-04). Standard library + star_geodesy (exact forward transform, iterative inverse to 1e-14 rad).

Method (the one that produced DISC-GEO-001): for each altitude band, generate points with KNOWN geodetic coordinates,
convert them to ECEF with the exact forward transform, give the ECEF to the library under audit, and measure its errors
against the known truth: latitude (deg), height (m) and the 3-D position error of the forward transform of the library
answer (m). The library is called through a plain function, or through `run_external` in its own venv (isolation).
Output: one envelope row per altitude band (max errors), plus the worst case. Nothing is tuned to the library.
"""
from __future__ import annotations

import json
import math
import subprocess
from typing import Callable, Dict, List, Sequence, Tuple

from star_geodesy import geodetic_to_ecef

ALTITUDES_M = (0.0, 1e3, 1e4, 1e5, 4e5, 1e6, 5e6, 2e7, 3.6e7)
LATS = (-89.0, -60.0, -34.5, -10.0, 0.0, 15.0, 34.0, 51.5, 72.0, 89.0)
LONS = (-170.0, -45.0, 0.0, 46.0, 120.0)


def points() -> List[Tuple[float, float, float]]:
    return [(la, lo, h) for h in ALTITUDES_M for la in LATS for lo in LONS]


def envelope(truth: Sequence[Tuple[float, float, float]], answers: Sequence[Tuple[float, float, float]]) -> Dict:
    """Max errors per altitude band. answers[i] = (lat_deg, lon_deg, h_m) returned by the library for truth[i]."""
    if len(truth) != len(answers):
        raise ValueError("one answer per truth point required")
    bands: Dict[float, Dict[str, float]] = {}
    for (la, lo, h), (la2, lo2, h2) in zip(truth, answers):
        x0 = geodetic_to_ecef(la, lo, h)
        x1 = geodetic_to_ecef(la2, lo2, h2)
        d3 = math.dist(x0, x1)
        b = bands.setdefault(h, {"lat_err_deg": 0.0, "h_err_m": 0.0, "pos_err_m": 0.0})
        b["lat_err_deg"] = max(b["lat_err_deg"], abs(la2 - la))
        b["h_err_m"] = max(b["h_err_m"], abs(h2 - h))
        b["pos_err_m"] = max(b["pos_err_m"], d3)
    worst = max(bands.items(), key=lambda kv: kv[1]["pos_err_m"])
    return {"bands": {str(k): v for k, v in sorted(bands.items())},
            "worst": {"altitude_m": worst[0], **worst[1]}, "n_points": len(truth)}


def audit_function(fn: Callable[[float, float, float], Tuple[float, float, float]]) -> Dict:
    """Audit an in-process ECEF->geodetic function fn(x, y, z) -> (lat_deg, lon_deg, h_m)."""
    pts = points()
    return envelope(pts, [fn(*geodetic_to_ecef(*p)) for p in pts])


def run_external(python_exe: str, code: str) -> Dict:
    """Audit a library in its OWN interpreter. `code` must define convert(x, y, z) -> (lat, lon, h)."""
    pts = points()
    ecef = [geodetic_to_ecef(*p) for p in pts]
    driver = code + "\nimport json, sys\nprint(json.dumps([list(convert(*p)) for p in json.loads(sys.stdin.read())]))\n"
    r = subprocess.run([python_exe, "-c", driver], input=json.dumps(ecef), capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"library run failed: {r.stderr[-300:]}")
    answers = [tuple(a) for a in json.loads(r.stdout.strip().splitlines()[-1])]
    return envelope(pts, answers)
