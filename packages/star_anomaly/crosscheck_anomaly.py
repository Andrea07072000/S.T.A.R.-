"""Cross-check of star_anomaly against three independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_anomaly.py  ->  12_EVIDENCE/crosscheck_anomaly_20261007.json

Lineages:
  mpmath   Kepler's equation solved at 50 digits by mpmath.findroot inside a bracket, and the textbook half-angle
           relations tan(nu/2) = sqrt((1+e)/(1-e)) tan(E/2), tanh(F/2) = sqrt((e-1)/(e+1)) tan(nu/2) at 50 digits
           (written in the driver: other formulas than the module's, same author);
  hapsira  hapsira.core.angles M_to_E, E_to_nu, nu_to_E, E_to_M, M_to_F, F_to_nu, nu_to_F, F_to_M (its own interpreter);
  orekit   Orekit KeplerianAnomalyUtility (Java, run in WSL).
Probe (published): Vallado, Fundamentals of Astrodynamics and Applications, the worked examples of Kepler's equation:
M = 235.4 deg, e = 0.4 gives E = 220.512074767522 deg; M = 235.4 deg, e = 2.4 gives H = 1.6013761449 rad.
Corpus (seed 20261007): 500 closed orbits with e in [0, 0.99] and 120 nearly parabolic ones (1 - e from 1e-3 to
1e-9), M in [-pi, pi] with every fifth one within 1e-6 of zero; 400 open orbits with e in [1.01, 10] and 100 with
e - 1 from 1e-3 to 1e-8, |M| up to 50. Each implementation is given M and e (to solve Kepler's equation) and the
eccentric (or hyperbolic) and true anomaly star_anomaly found (to convert each way).
Differences in radians, angles compared modulo a turn. On the nearly parabolic sets the two libraries are measured
apart and reported, not held to the limit of the ordinary set; star_anomaly is held to the 50-digit values everywhere.
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
import star_anomaly as sa  # noqa: E402

MPMATH = '''
import mpmath as mp
from fractions import Fraction
mp.mp.dps = 50
def M_(v):
    f = Fraction(v)
    return mp.mpf(f.numerator) / mp.mpf(f.denominator)
def closed(M, e, E, nu):
    M, e, E, nu = M_(M), M_(e), M_(E), M_(nu)
    if M == 0:
        root = mp.mpf(0)
    else:
        a = abs(M)
        root = mp.sign(M) * mp.findroot(lambda x: x - e * mp.sin(x) - a, (a, min(mp.pi, a + e) + mp.mpf(10) ** -40), solver="anderson", tol=mp.mpf(10) ** -40, maxsteps=500)
    k = mp.sqrt((1 + e) / (1 - e))
    return [float(root), float(2 * mp.atan(k * mp.tan(E / 2))), float(2 * mp.atan(mp.tan(nu / 2) / k)), float(E - e * mp.sin(E))]
def opened(M, e, F, nu):
    M, e, F, nu = M_(M), M_(e), M_(F), M_(nu)
    if M == 0:
        root = mp.mpf(0)
    else:
        a = abs(M)
        hi = min(mp.asinh(a / (e - 1)), mp.cbrt(6 * a / e)) * (1 + mp.mpf(10) ** -30) + mp.mpf(10) ** -40
        root = mp.sign(M) * mp.findroot(lambda x: e * mp.sinh(x) - x - a, (mp.mpf(0), hi), solver="anderson", tol=mp.mpf(10) ** -40, maxsteps=500)
    k = mp.sqrt((e + 1) / (e - 1))
    return [float(root), float(2 * mp.atan(k * mp.tanh(F / 2))), float(2 * mp.atanh(mp.tan(nu / 2) / k)), float(e * mp.sinh(F) - F)]
'''
HAPSIRA = '''
from hapsira.core import angles as A
def closed(M, e, E, nu):
    return [float(A.M_to_E(M, e)), float(A.E_to_nu(E, e)), float(A.nu_to_E(nu, e)), float(A.E_to_M(E, e))]
def opened(M, e, F, nu):
    return [float(A.M_to_F(M, e)), float(A.F_to_nu(F, e)), float(A.nu_to_F(nu, e)), float(A.F_to_M(F, e))]
'''
OREKIT = '''
import orekit_jpype
orekit_jpype.initVM()
from org.orekit.orbits import KeplerianAnomalyUtility as K
def closed(M, e, E, nu):
    return [K.ellipticMeanToEccentric(e, M), K.ellipticEccentricToTrue(e, E), K.ellipticTrueToEccentric(e, nu), K.ellipticEccentricToMean(e, E)]
def opened(M, e, F, nu):
    return [K.hyperbolicMeanToEccentric(e, M), K.hyperbolicEccentricToTrue(e, F), K.hyperbolicTrueToEccentric(e, nu), K.hyperbolicEccentricToMean(e, F)]
'''
RUNNER = '''
import json, sys, warnings
warnings.simplefilter("ignore")
job = json.load(sys.stdin)
out = {}
for name, fn in (("closed", closed), ("opened", opened)):
    out[name] = []
    for args in job[name]:
        try:
            out[name].append([float(x) for x in fn(*args)])
        except Exception as e:
            out[name].append("error:" + type(e).__name__ + ":" + str(e)[:60])
print("@@" + json.dumps(out))
'''
COMMANDS = {"mpmath": [str(ROOT / ".venvs" / "mpmath" / "Scripts" / "python.exe"), "-W", "ignore", "-c"],
            "hapsira": [str(ROOT / ".venvs" / "hapsira" / "Scripts" / "python.exe"), "-W", "ignore", "-c"],
            "orekit": ["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-W", "ignore", "-c"]}
DRIVERS = {"mpmath": MPMATH, "hapsira": HAPSIRA, "orekit": OREKIT}
LIMITS = {"mpmath": 1e-13, "hapsira": 1e-11, "orekit": 1e-11}
ORDINARY_CLOSED, ORDINARY_OPEN = 500, 400
LABELS = ("kepler", "true_from", "to_from_true", "mean_from")


def corpus():
    rnd = random.Random(20261007)
    closed, opened = [], []
    for k in range(620):
        e = rnd.uniform(0.0, 0.99) if k < ORDINARY_CLOSED else 1.0 - 10.0 ** rnd.uniform(-9, -3)
        M = rnd.choice([-1, 1]) * 10.0 ** rnd.uniform(-9, -6) if k % 5 == 0 else rnd.uniform(-math.pi, math.pi)
        E = sa.eccentric_from_mean(M, e)
        closed.append([M, e, E, sa.true_from_eccentric(E, e)])
    for k in range(500):
        e = rnd.uniform(1.01, 10.0) if k < ORDINARY_OPEN else 1.0 + 10.0 ** rnd.uniform(-8, -3)
        M = rnd.choice([-1, 1]) * 10.0 ** rnd.uniform(-9, -6) if k % 5 == 0 else rnd.uniform(-50.0, 50.0)
        F = sa.hyperbolic_from_mean(M, e)
        opened.append([M, e, F, sa.true_from_hyperbolic(F, e)])
    return {"closed": closed + [[math.radians(235.4) - 2 * math.pi, 0.4, 0.0, 0.0]], "opened": opened + [[math.radians(235.4), 2.4, 0.0, 0.0]]}


def gaps(kind, args, theirs, wrap):
    """star_anomaly applied to the SAME inputs the reference received (the inverse from a true anomaly is badly conditioned
    near a parabola: comparing it with the anomaly the true one was computed from would measure the float, not the code)."""
    M, e, anomaly, nu = args
    if kind == "closed":
        mine = (sa.eccentric_from_mean(M, e), sa.true_from_eccentric(anomaly, e), sa.eccentric_from_true(nu, e), sa.mean_from_eccentric(anomaly, e))
    else:
        mine = (sa.hyperbolic_from_mean(M, e), sa.true_from_hyperbolic(anomaly, e), sa.hyperbolic_from_true(nu, e), sa.mean_from_hyperbolic(anomaly, e))
    scale = (1.0, 1.0, 1.0, max(1.0, abs(M)))                 # the mean anomaly of an open orbit reaches 50: relative there
    return [(abs(math.remainder(a - b, 2 * math.pi)) if wrap else abs(a - b)) / s for a, b, s in zip(mine, theirs, scale)]


def main():
    job = corpus()
    e_probe = math.degrees(sa.eccentric_from_mean(math.radians(235.4), 0.4))
    h_probe = sa.hyperbolic_from_mean(math.radians(235.4), 2.4)
    mine_ok = abs(e_probe - 220.512074767522) < 1e-11 and abs(h_probe - 1.6013761449) < 1e-10
    out = {"cases": {k: len(v) for k, v in job.items()}, "seed": 20261007, "lineages": {}}
    for name, driver in DRIVERS.items():
        r = subprocess.run(COMMANDS[name] + [driver + RUNNER], input=json.dumps(job), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if any(len(res[k]) != len(job[k]) for k in job):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for k in job for x in res[k] if isinstance(x, str)]
        pc, po = res["closed"][-1], res["opened"][-1]
        valid = isinstance(pc, list) and isinstance(po, list) and abs(math.remainder(pc[0] - math.radians(220.512074767522), 2 * math.pi)) < 1e-10 and abs(po[0] - 1.6013761449) < 1e-9
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid and not errors:
            ordinary = dict.fromkeys(LABELS, 0.0)
            near = dict.fromkeys(LABELS, 0.0)
            for kind, count, wrap in (("closed", ORDINARY_CLOSED, True), ("opened", ORDINARY_OPEN, False)):
                for i, (args, theirs) in enumerate(zip(job[kind][:-1], res[kind][:-1])):
                    table = ordinary if i < count else near
                    for label, gap in zip(LABELS, gaps(kind, args, theirs, wrap)):
                        table[label] = max(table[label], gap)
            held = max(ordinary.values()) if name != "mpmath" else max(max(ordinary.values()), max(near.values()))
            entry.update(compared=sum(len(v) - 1 for v in job.values()), max_diff_rad={"ordinary": ordinary, "nearly_parabolic": near}, within=held <= LIMITS[name], limit_rad=LIMITS[name],
                         limit_applies_to="every case" if name == "mpmath" else "the ordinary sets (the nearly parabolic ones are measured and reported)")
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1], entry.get("max_diff_rad"), entry.get("within"), flush=True)
    L = out["lineages"]
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("within") for v in L.values())

    def top(name, part):
        return max(((L[name].get("max_diff_rad") or {}).get(part) or {"x": 0.0}).values())

    out["published"] = {"source": "Vallado, Fundamentals of Astrodynamics and Applications, worked examples of Kepler's equation: M = 235.4 deg, e = 0.4 -> E = 220.512074767522 deg; "
                                  "M = 235.4 deg, e = 2.4 -> H = 1.6013761449 rad", "star_anomaly_reproduces": mine_ok, "star_anomaly_values": [e_probe, h_probe]}
    out["summary"] = {"ok": ok, "lineages": ["Kepler's equation and half-angle relations at 50 digits in mpmath (same author)", "hapsira.core.angles", "Orekit KeplerianAnomalyUtility"],
                      "claim": "star_anomaly solves Kepler's equation and converts between mean, eccentric, hyperbolic and true anomaly to within 1e-13 rad of 50-digit arithmetic, nearly parabolic "
                               "orbits included",
                      "crosscheck": f"1120 orbits (620 closed, 500 open) and Vallado's two examples, four conversions each: largest difference from the 50-digit values {top('mpmath', 'ordinary'):.1e} rad "
                                    f"on the ordinary sets and {top('mpmath', 'nearly_parabolic'):.1e} on the nearly parabolic ones; from hapsira {top('hapsira', 'ordinary'):.1e} and "
                                    f"{top('hapsira', 'nearly_parabolic'):.1e}; from Orekit {top('orekit', 'ordinary'):.1e} and {top('orekit', 'nearly_parabolic'):.1e}",
                      "benchmark": f"largest difference from 50-digit arithmetic: {max(top('mpmath', 'ordinary'), top('mpmath', 'nearly_parabolic')):.1e} rad; hapsira on nearly parabolic orbits: "
                                   f"{top('hapsira', 'nearly_parabolic'):.1e} rad; Orekit: {top('orekit', 'nearly_parabolic'):.1e} rad"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_anomaly_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
