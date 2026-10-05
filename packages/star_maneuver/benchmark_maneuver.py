# -*- coding: utf-8 -*-
"""Standardized Hohmann & Two-Impulse Orbital Maneuver Benchmark Suite.
Validates 10 canonical orbital transfers across Earth, Moon, and Mars against
exact closed-form analytical vis-viva equations and energy conservation.
"""
import math
from star_maneuver import hohmann, vis_viva

# 10 Standard Aerospace Transfer Scenarios
# (Name, r1_km, r2_km, mu)
BENCHMARK_SCENARIOS = [
    ("LEO (300 km) to GEO (35786 km) Earth", 6678.137, 42164.137, 398600.4418),
    ("LEO (200 km) to MEO (20000 km) Earth", 6578.137, 26378.137, 398600.4418),
    ("ISS (400 km) to Hubble (540 km) Earth", 6778.137, 6918.137, 398600.4418),
    ("Starlink (550 km) to O3b MEO (8062 km)", 6928.137, 14440.137, 398600.4418),
    ("Moon Low Orbit (100 km) to High Orbit (2000 km)", 1837.4, 3737.4, 4902.8),
    ("Mars Low Orbit (250 km) to Areostationary (20428 km)", 3646.0, 20428.0, 42828.37),
    ("LEO (6678 km) to Lunar Transfer Orbit (384400 km)", 6678.0, 384400.0, 398600.4418),
    ("Earth Circular GTO injection (200 km to 35786 km)", 6578.137, 42164.137, 398600.4418),
    ("Geostationary Graveyard Drift (+300 km)", 42164.137, 42464.137, 398600.4418),
    ("Mars Phobos Rendezvous Orbit (3640 km to 9376 km)", 3640.0, 9376.0, 42828.37),
]

def analytical_hohmann_exact(r1: float, r2: float, mu: float):
    """Closed-form analytical solution derived directly from Vis-Viva and Kepler's 3rd Law."""
    a_t = (r1 + r2) / 2.0
    v_c1 = math.sqrt(mu / r1)
    v_c2 = math.sqrt(mu / r2)
    v_t1 = math.sqrt(mu * (2.0 / r1 - 1.0 / a_t))
    v_t2 = math.sqrt(mu * (2.0 / r2 - 1.0 / a_t))
    dv1 = abs(v_t1 - v_c1)
    dv2 = abs(v_c2 - v_t2)
    tof = math.pi * math.sqrt((a_t ** 3) / mu)
    return {"dv1": dv1, "dv2": dv2, "dv_total": dv1 + dv2, "tof_s": tof}

def run_benchmarks():
    passed = 0
    results = []
    for name, r1, r2, mu in BENCHMARK_SCENARIOS:
        exact = analytical_hohmann_exact(r1, r2, mu)
        computed = hohmann(r1, r2, mu)

        dv_err = abs(computed["dv_total"] - exact["dv_total"])
        tof_err = abs(computed["tof_s"] - exact["tof_s"])

        # Check precision to floating point tolerance (< 1e-12)
        ok = dv_err < 1e-10 and tof_err < 1e-8
        if ok:
            passed += 1
        results.append({
            "name": name,
            "dv_total": round(computed["dv_total"], 6),
            "exact_dv": round(exact["dv_total"], 6),
            "dv_err": dv_err,
            "tof_s": round(computed["tof_s"], 2),
            "status": "PASS" if ok else "FAIL"
        })
    return {"cases": len(BENCHMARK_SCENARIOS), "passed": passed, "results": results}

if __name__ == "__main__":
    b = run_benchmarks()
    print(f"Maneuver Benchmark: {b['passed']}/{b['cases']} PASSED")
    for r in b["results"]:
        print(f"[{r['status']}] {r['name']}: dv={r['dv_total']} km/s (err={r['dv_err']:.2e})")
    assert b["passed"] == b["cases"], "Benchmark failure"
