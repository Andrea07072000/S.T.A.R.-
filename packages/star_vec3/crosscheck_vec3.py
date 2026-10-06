"""Cross-check of star_vec3 against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_vec3.py  ->  12_EVIDENCE/crosscheck_vec3_20261006.json

Lineages, each in its own interpreter:
  spice  SPICE vdot, vcrss, vnorm, vdist, vhat, vsep, vproj, vperp (C): every function except the triple product;
  erfa   ERFA pdp, pxp, pm, pn, sepp (C): dot, cross, norm, unit and angle;
  numpy  numpy.dot, numpy.cross, numpy.linalg.norm and numpy.linalg.det (the triple product is the determinant of
         the three vectors as rows).
Probe (by hand; there is no published numerical example for definitions): i x j = k, (3, 4, 0) has length 5, and the
angle between (1, 0, 0) and (1, 1, 0) is 45 degrees. A lineage that does not return them is excluded.
Corpus (seed 20261006): 600 triples of vectors with lengths from 1e-3 to 1e9; in 200 of them the second vector is
within 1e-9 ... 1e-3 rad of parallel or antiparallel to the first, where the angle is the hard part.
Differences are relative to the product of the lengths involved; angles are compared in degrees.
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_vec3 as sv  # noqa: E402

PROBE = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [3.0, 4.0, 0.0]]
SPICE = ("import spiceypy as sp, math\nL = lambda v: [float(x) for x in v]\ndef f(a, b, c):\n"
         "    return {'dot': float(sp.vdot(a, b)), 'cross': L(sp.vcrss(a, b)), 'norm': float(sp.vnorm(c)), 'dist': float(sp.vdist(a, b)), 'unit': L(sp.vhat(a)),\n"
         "            'angle': math.degrees(float(sp.vsep(a, b))), 'proj': L(sp.vproj(a, b)), 'rej': L(sp.vperp(a, b))}\n")
ERFA = ("import erfa, math\ndef f(a, b, c):\n"
        "    return {'dot': float(erfa.pdp(a, b)), 'cross': erfa.pxp(a, b).tolist(), 'norm': float(erfa.pm(c)), 'unit': erfa.pn(a)[1].tolist(),\n"
        "            'angle': math.degrees(float(erfa.sepp(a, b)))}\n")
NUMPY = ("import numpy as np\ndef f(a, b, c):\n"
         "    return {'dot': float(np.dot(a, b)), 'cross': np.cross(a, b).tolist(), 'norm': float(np.linalg.norm(c)), 'triple': float(np.linalg.det(np.array([a, b, c])))}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"spice": (venv("spiceypy"), SPICE), "erfa": (sys.executable, ERFA), "numpy": (venv("scipy"), NUMPY)}


def vmax(a, b):
    return max(abs(p - q) for p, q in zip(a, b))


def main():
    rnd = random.Random(20261006)

    def vec():
        m = 10 ** rnd.uniform(-3, 9)
        z, t = rnd.uniform(-1, 1), rnd.uniform(0, 2 * math.pi)
        s = math.sqrt(1 - z * z)
        return [m * s * math.cos(t), m * s * math.sin(t), m * z]

    cases = [PROBE]
    for k in range(600):
        a = vec()
        if k % 3 == 0:                                      # b nearly parallel or antiparallel to a
            p, eps, sign = vec(), 10 ** rnd.uniform(-9, -3), rnd.choice((-1.0, 1.0))
            na, npp = sv.norm(a), sv.norm(p)
            b = [sign * 3.7 * a[i] + eps * 3.7 * na * p[i] / npp for i in range(3)]
        else:
            b = vec()
        cases.append([a, b, vec()])
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
        valid = isinstance(p, dict) and p.get("cross") == [0.0, 0.0, 1.0] and p.get("norm") == 5.0 and p.get("dot") == 0.0
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {}
            n = 0
            for (a, b, c), x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                na, nb, nc = sv.norm(a), sv.norm(b), sv.norm(c)
                pairs = {"dot": abs(sv.dot(a, b) - x["dot"]) / (na * nb), "cross": vmax(sv.cross(a, b), x["cross"]) / (na * nb), "norm": abs(sv.norm(c) / x["norm"] - 1.0)}
                if "unit" in x:
                    pairs["unit"] = vmax(sv.unit(a), x["unit"])
                    pairs["angle_deg"] = abs(sv.angle_deg(a, b) - x["angle"])
                if "proj" in x:
                    pairs["distance"] = abs(sv.distance(a, b) - x["dist"]) / (na + nb)
                    pairs["project"] = vmax(sv.project(a, b), x["proj"]) / na
                    pairs["reject"] = vmax(sv.reject(a, b), x["rej"]) / na
                if "triple" in x:
                    pairs["triple"] = abs(sv.triple(a, b, c) - x["triple"]) / (na * nb * nc)
                for k2, v in pairs.items():
                    m[k2] = max(m.get(k2, 0.0), v)
            entry.update(compared=n, **{"max_" + k2 + "_diff": v for k2, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {p}", "errors", len(errors), errors[:1], {k[4:-5]: v for k, v in entry.items() if k.startswith("max_")}, flush=True)
    L = out["lineages"]
    worst = {n: max((v for k, v in e.items() if k.startswith("max_")), default=1.0) for n, e in L.items()}
    mine_ok = sv.cross(PROBE[0], PROBE[1]) == (0.0, 0.0, 1.0) and sv.norm(PROBE[2]) == 5.0 and abs(sv.angle_deg([1, 0, 0], [1, 1, 0]) - 45.0) < 1e-13
    covered = {k[4:-5] for e in L.values() for k in e if k.startswith("max_")}
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and mine_ok and max(worst.values()) < 1e-11 \
        and covered == {"dot", "cross", "norm", "distance", "unit", "angle_deg", "project", "reject", "triple"}
    out["by_hand"] = {"cases": "i x j = k; |(3, 4, 0)| = 5; angle((1, 0, 0), (1, 1, 0)) = 45 deg", "star_vec3_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SPICE vdot / vcrss / vnorm / vdist / vhat / vsep / vproj / vperp (C)", "ERFA pdp / pxp / pm / pn / sepp (C)", "NumPy dot / cross / norm / det"],
                      "claim": "star_vec3 computes the products, lengths, angles and projections of three-dimensional vectors as three independent libraries do, nearly parallel vectors included",
                      "crosscheck": f"600 triples of vectors (lengths 1e-3 to 1e9; 200 pairs within 1e-9 to 1e-3 rad of parallel or antiparallel): largest difference, relative to the "
                                    f"lengths involved or in degrees for the angle: SPICE {worst['spice']:.1e}, ERFA {worst['erfa']:.1e}, NumPy {worst['numpy']:.1e}; every function is "
                                    f"compared with at least one library, the triple product with NumPy's determinant only",
                      "benchmark": "; ".join(f"{n} {w:.1e}" for n, w in worst.items())}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_vec3_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "by hand:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
