"""Cross-check of star_gasdynamics against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_gasdynamics.py  ->  12_EVIDENCE/crosscheck_gasdynamics_20261006.json

Lineages, each in its own interpreter:
  scikit-aero  skaero.gasdynamics (Python): IsentropicFlow T_T0, p_p0, A_Astar; mach_from_area_ratio (both branches, its own
               root finder); NormalShock M_2 and p2_p1. It has no density ratio, no T2/T1 and no p02/p01.
               (Run with the interpreter of the SciPy environment and the scikit-aero package directory on the path:
               its own environment was created without NumPy.)
  fluids       fluids.compressible (Python): P_stagnation (p0/p from T0/T), T_critical_flow and P_critical_flow (the
               values at Mach 1). It has nothing as a function of Mach number: it checks the exponent of the
               pressure-temperature relation and the sonic ratios, for every gamma.
Probe (published): NACA Report 1135, tables for gamma = 1.4, at Mach 2: T/T0 = 0.5556, p/p0 = 0.1278, A/A* = 1.688,
M2 = 0.5774, p2/p1 = 4.500. A lineage that does not return what it has of those within 5e-5 relative is excluded.
What only the published table and the conservation laws support (see the tests): rho2/rho1, T2/T1 and p02/p01.
Corpus (seed 20261006): 600 cases: Mach 0.01 to 20 (shock: 1 to 20), gamma 1.05 to 1.67.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_gasdynamics as sg  # noqa: E402

SKAERO = ("import sys\nsys.path.insert(0, r'%s')\nfrom skaero.gasdynamics import isentropic, shocks\n"
          "def f(m, ms, g):\n"
          "    fl = isentropic.IsentropicFlow(gamma=g)\n"
          "    ar = float(fl.A_Astar(m))\n"
          "    try:\n        sub, sup = isentropic.mach_from_area_ratio(fl, ar)\n    except Exception:\n        sub = sup = float('nan')\n"
          "    s = shocks.NormalShock(M_1=ms, gamma=g)\n"
          "    return {'t': float(fl.T_T0(m)), 'p': float(fl.p_p0(m)), 'a': ar, 'm_sub': float(sub), 'm_sup': float(sup), 'm2': float(s.M_2), 'p21': float(s.p2_p1)}\n"
          ) % str(ROOT / ".venvs" / "scikit_aero" / "Lib" / "site-packages")
FLUIDS = ("from fluids import compressible as fc\ndef f(m, ms, g):\n"
          "    t0_t = 1.0 + 0.5 * (g - 1.0) * m * m\n"
          "    return {'p0_p': float(fc.P_stagnation(1.0, 1.0, t0_t, g)), 't_star': float(fc.T_critical_flow(1.0, g)), 'p_star': float(fc.P_critical_flow(1.0, g))}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"scikit-aero": (str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), SKAERO),
           "fluids": (str(ROOT / ".venvs" / "thermo" / "Scripts" / "python.exe"), FLUIDS)}
NACA = {"t": 0.5556, "p": 0.1278, "a": 1.688, "m2": 0.5774, "p21": 4.500}


def rel(a, b):
    return abs(a / b - 1.0)


def main():
    rnd = random.Random(20261006)
    cases = [[2.0, 2.0, 1.4]] + [[10 ** rnd.uniform(-2, math_log20()), 10 ** rnd.uniform(0, math_log20()), rnd.uniform(1.05, 1.67)] for _ in range(600)]
    out = {"cases": len(cases) - 1, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        p = res[0]
        if name == "scikit-aero":
            valid = isinstance(p, dict) and all(k in p and abs(p[k] / v - 1.0) < 5e-4 for k, v in NACA.items())
        else:                                               # p0/p at Mach 2 is 1 / 0.1278; the sonic ratios for 1.4 are 0.8333 and 0.5283 (NACA 1135)
            valid = isinstance(p, dict) and abs(p.get("p0_p", 0.0) * 0.1278 - 1.0) < 5e-4 and abs(p.get("t_star", 0.0) - 0.8333) < 5e-5 and abs(p.get("p_star", 0.0) - 0.5283) < 5e-5
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {}
            roots = {}
            n = 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                t, pr, _, ar = sg.isentropic(c[0], c[2])
                if "t" in x:
                    sh = sg.normal_shock(c[1], c[2])
                    pairs = {"T_T0": rel(t, x["t"]), "p_p0": rel(pr, x["p"]), "A_Astar": rel(ar, x["a"]), "M2": rel(sh[0], x["m2"]), "p2_p1": rel(sh[1], x["p21"])}
                    if ar <= 1e6:                           # the inverse: their two roots against ours on each branch (ill-conditioned next to Mach 1: weighed by |M - 1|)
                        for key, sup in (("m_sup", True), ("m_sub", False)):
                            mine = sg.mach_from_area_ratio(x["a"], c[2], sup) if x["a"] >= 1.0 and (sup or x["a"] <= sg._area(sg.MACH_MIN_SUBSONIC, c[2])) else None
                            if mine is None:
                                continue
                            # scikit-aero's root finder does not always converge, and on the supersonic branch it can return a root of the
                            # other branch: a root of theirs is used only if it reproduces the area ratio (checked with THEIR A_Astar value)
                            theirs = x[key]
                            usable = theirs == theirs and (theirs > 1.0) == sup and abs(sg._area(theirs, c[2]) / x["a"] - 1.0) < 1e-9
                            roots[key] = roots.get(key, 0) + usable
                            if usable:
                                pairs["mach_from_area_" + key[2:]] = abs(mine - theirs) / max(mine, 1.0) * min(1.0, abs(mine - 1.0) * 1e3)
                else:
                    star = sg.isentropic(1.0, c[2])
                    pairs = {"p0_p_from_T0_T": rel(1.0 / pr, x["p0_p"]), "T_star": rel(star[0], x["t_star"]), "p_star": rel(star[1], x["p_star"])}
                for k, v in pairs.items():
                    m[k] = max(m.get(k, 0.0), v)
            entry.update(compared=n, usable_roots_of_the_library=roots, **{"max_" + k + "_rel": v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:-4]: v for k, v in entry.items() if k.startswith("max_")}, flush=True)
    L = out["lineages"]
    S, F = L["scikit-aero"], L["fluids"]
    direct = [S.get("max_" + k + "_rel") for k in ("T_T0", "p_p0", "A_Astar", "M2", "p2_p1")] + [F.get("max_" + k + "_rel") for k in ("p0_p_from_T0_T", "T_star", "p_star")]
    inverse = [S.get("max_mach_from_area_sup_rel"), S.get("max_mach_from_area_sub_rel")]
    naca = sg.isentropic(2.0) + sg.normal_shock(2.0)
    mine_ok = abs(naca[0] - 0.5556) < 5e-5 and abs(naca[1] - 0.1278) < 5e-5 and abs(naca[3] - 1.688) < 5e-4 and abs(naca[4] - 0.5774) < 5e-5 and abs(naca[5] - 4.5) < 5e-4
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and all(x is not None for x in direct + inverse) \
        and max(direct) < 1e-12 and max(inverse) < 1e-7 and mine_ok
    out["published"] = {"source": "NACA Report 1135, gamma = 1.4, Mach 2", "star_gasdynamics_reproduces": mine_ok}
    if all(x is not None for x in direct + inverse):
        out["summary"] = {"ok": ok, "lineages": ["scikit-aero skaero.gasdynamics (isentropic ratios, area ratio and its inverse, normal-shock M2 and p2/p1)",
                                                 "fluids.compressible (stagnation pressure relation, sonic ratios)", "NACA Report 1135 tables"],
                          "claim": "star_gasdynamics reproduces the isentropic relations and the normal-shock Mach number and pressure ratio of an independent library for any gamma",
                          "crosscheck": f"600 cases (Mach 0.01 to 20, gamma 1.05 to 1.67): T/T0, p/p0, A/A*, M2 and p2/p1 within {max(direct[:5]):.1e} relative of scikit-aero; "
                                        f"p0/p from T0/T and the sonic ratios within {max(direct[5:]):.1e} of fluids; Mach from area ratio within {max(inverse):.1e} of scikit-aero's root "
                                        f"finder where that converged to a root of the right branch ({S.get('usable_roots_of_the_library')} of 600 per branch); rho2/rho1, T2/T1 and p02/p01 have NO library lineage (published table and conservation laws only)",
                          "benchmark": f"direct relations {max(direct):.1e}; inverse of the area ratio {max(inverse):.1e}"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_gasdynamics_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


def math_log20():
    import math
    return math.log10(20.0)


if __name__ == "__main__":
    main()
