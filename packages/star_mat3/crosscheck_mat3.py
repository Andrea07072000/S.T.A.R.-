"""Cross-check of star_mat3 against three independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_mat3.py  ->  12_EVIDENCE/crosscheck_mat3_20261006.json

Lineages, each in its own interpreter:
  sympy  sympy.Matrix on the exact rational value of every float: determinant, inverse, product, matrix times vector
         in EXACT arithmetic, rounded once. This is the truth the others are measured against.
  spice  SPICE det, invert, mxm, mxv, xpose, isrot (C, double precision);
  numpy  numpy.linalg.det, numpy.linalg.inv, @ (LAPACK, double precision).
Probe (by hand; there is no published numerical example for definitions): the matrix [[2, 0, 1], [1, 3, 2], [1, 0, 1]]
has determinant 3 and inverse [[1, 0, -1], [1/3, 1/3, -1], [-1, 0, 2]]. A lineage that does not return the determinant
is excluded.
Corpus (seed 20261006): 600 matrices: 300 with random entries of mixed magnitude, 150 rotations (from random unit
quaternions), 150 ill-conditioned (a rotation times a diagonal with ratios up to 1e8 times a rotation).
Differences: determinant relative to the product of the row lengths; inverse relative to its largest entry;
products relative to the largest entry of the result.
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
import star_mat3 as sm  # noqa: E402

PROBE = [[[2.0, 0.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 1.0]], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], [1.0, 2.0, 3.0]]
SYMPY = ("from sympy import Matrix, Rational\nfrom fractions import Fraction\n"
         "def R(v):\n    f = Fraction(v); return Rational(f.numerator, f.denominator)\n"
         "def F(M):\n    return [[float(M[i, j]) for j in range(M.cols)] for i in range(M.rows)]\n"
         "def f(a, b, v):\n"
         "    A, B, V = Matrix(3, 3, [R(x) for r in a for x in r]), Matrix(3, 3, [R(x) for r in b for x in r]), Matrix(3, 1, [R(x) for x in v])\n"
         "    return {'det': float(A.det()), 'inv': F(A.inv()), 'mm': F(A * B), 'mv': [float(x) for x in A * V]}\n")
SPICE = ("import spiceypy as sp\nL = lambda M: [[float(x) for x in r] for r in M]\ndef f(a, b, v):\n"
         "    return {'det': float(sp.det(a)), 'inv': L(sp.invert(a)), 'mm': L(sp.mxm(a, b)), 'mv': [float(x) for x in sp.mxv(a, v)], 'tr': L(sp.xpose(a)),\n"
         "            'rot': bool(sp.isrot(a, 1e-9, 1e-9))}\n")
NUMPY = ("import numpy as np\ndef f(a, b, v):\n"
         "    A, B = np.array(a), np.array(b)\n"
         "    return {'det': float(np.linalg.det(A)), 'inv': np.linalg.inv(A).tolist(), 'mm': (A @ B).tolist(), 'mv': (A @ np.array(v)).tolist()}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"sympy": (venv("sympy"), SYMPY), "spice": (venv("spiceypy"), SPICE), "numpy": (venv("scipy"), NUMPY)}


def mmax(a, b):
    return max(abs(p - q) for ra, rb in zip(a, b) for p, q in zip(ra, rb))


def big(m):
    return max(abs(c) for r in m for c in r) or 1.0


def main():
    rnd = random.Random(20261006)

    def rotation():
        q = [rnd.gauss(0, 1) for _ in range(4)]
        n = math.sqrt(sum(c * c for c in q))
        w, x, y, z = (c / n for c in q)
        return [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]

    def general():
        return [[rnd.uniform(-1, 1) * 10 ** rnd.uniform(-3, 6) for _ in range(3)] for _ in range(3)]

    cases, kinds = [PROBE], []
    for k in range(600):
        if k < 300:
            a, kind = general(), "general"
        elif k < 450:
            a, kind = rotation(), "rotation"
        else:
            d = [1.0, 10 ** rnd.uniform(-8, 0), 10 ** rnd.uniform(-8, 0)]
            a = [list(r) for r in sm.matmul(sm.matmul(rotation(), [[d[0], 0, 0], [0, d[1], 0], [0, 0, d[2]]]), rotation())]
            kind = "ill-conditioned"
        try:
            sm.inverse(a)
        except ValueError:
            continue                                        # a random matrix that the module refuses to invert is not sent
        cases.append([a, general(), [rnd.uniform(-1e3, 1e3) for _ in range(3)]])
        kinds.append(kind)
    out = {"cases": len(cases) - 1, "kinds": {k: kinds.count(k) for k in sorted(set(kinds))}, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=1800)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = isinstance(res[0], dict) and abs(res[0].get("det", 0.0) - 3.0) < 1e-12
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"determinant": 0.0, "inverse": 0.0, "inverse_ill_conditioned": 0.0, "matmul": 0.0, "matvec": 0.0}
            rot_disagree = n = 0
            for (a, b, v), x, kind in zip(cases[1:], res[1:], kinds):
                if isinstance(x, str):
                    continue
                n += 1
                rows = math.prod(math.hypot(*r) for r in a)
                m["determinant"] = max(m["determinant"], abs(sm.determinant(a) - x["det"]) / rows)
                key = "inverse_ill_conditioned" if kind == "ill-conditioned" else "inverse"
                m[key] = max(m[key], mmax(sm.inverse(a), x["inv"]) / big(x["inv"]))
                m["matmul"] = max(m["matmul"], mmax(sm.matmul(a, b), x["mm"]) / big(x["mm"]))
                m["matvec"] = max(m["matvec"], max(abs(p - q) for p, q in zip(sm.matvec(a, v), x["mv"])) / (max(abs(c) for c in x["mv"]) or 1.0))
                if "tr" in x:
                    m["transpose"] = max(m.get("transpose", 0.0), mmax(sm.transpose(a), x["tr"]))
                    rot_disagree += sm.is_rotation(a, 1e-9) != x["rot"]
            entry.update(compared=n, **{"max_" + k + "_diff": v for k, v in m.items()})
            if "rot" in res[0]:
                entry["is_rotation_disagreements"] = rot_disagree
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k[4:-5]: v for k, v in entry.items() if k.startswith("max_")},
              entry.get("is_rotation_disagreements"), flush=True)
    L = out["lineages"]
    S = L["sympy"]
    n_cases = len(cases) - 1
    mine_ok = sm.determinant(PROBE[0]) == 3.0 and mmax(sm.inverse(PROBE[0]), [[1, 0, -1], [1 / 3, 1 / 3, -1], [-1, 0, 2]]) < 1e-15
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == n_cases for v in L.values()) and mine_ok and n_cases >= 550 \
        and max(S["max_determinant_diff"], S["max_inverse_diff"], S["max_matmul_diff"], S["max_matvec_diff"]) < 1e-12 and S["max_inverse_ill_conditioned_diff"] < 1e-6 \
        and L["spice"].get("is_rotation_disagreements") == 0 and L["spice"].get("max_transpose_diff") == 0.0
    out["by_hand"] = {"case": "det [[2,0,1],[1,3,2],[1,0,1]] = 3 and its inverse", "star_mat3_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["SymPy exact rational matrices", "SPICE det / invert / mxm / mxv / xpose / isrot (C)", "NumPy linalg det / inv and @"],
                      "claim": "star_mat3 computes determinant, inverse and products of 3x3 matrices to the accuracy double precision allows, as measured against exact arithmetic, "
                               "and recognises rotations as SPICE does",
                      "crosscheck": f"{n_cases} matrices ({out['kinds']}): against exact arithmetic, determinant within {S['max_determinant_diff']:.1e} (relative to the row lengths), "
                                    f"inverse within {S['max_inverse_diff']:.1e} of its largest entry ({S['max_inverse_ill_conditioned_diff']:.1e} on matrices with condition numbers "
                                    f"up to 1e8), products within {max(S['max_matmul_diff'], S['max_matvec_diff']):.1e}; is_rotation agrees with SPICE on every matrix",
                      "benchmark": "inverse of ill-conditioned matrices against the exact one: star_mat3 "
                                   f"{S['max_inverse_ill_conditioned_diff']:.1e}; and star_mat3 against SPICE {L['spice']['max_inverse_ill_conditioned_diff']:.1e}, "
                                   f"NumPy {L['numpy']['max_inverse_ill_conditioned_diff']:.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_mat3_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "by hand:", mine_ok, "cases", n_cases, "->", dest.name)


if __name__ == "__main__":
    main()
