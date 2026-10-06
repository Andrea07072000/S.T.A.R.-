"""Cross-check of star_j2 against two independent determinations of the secular rates (S.T.A.R., 2026-10-06).

  python crosscheck_j2.py  ->  12_EVIDENCE/crosscheck_j2_20261006.json

Lineages, each in its own interpreter:
  orekit_eh   Orekit EcksteinHechlerPropagator with J2 only (C20 = -J2, higher zonals zero), started from MEAN elements:
              an analytical theory that also carries J2-squared terms; near-circular orbits only (its domain);
  numerical   SciPy DOP853 integration of the equations of motion with the J2 acceleration (no secular model at
              all), started with osculating = mean elements; node and perigee drift from a least-squares line.
Each lineage returns samples (t, RAAN, argument of perigee); the rate is the slope of the unwrapped angle.
Probe: for the ISS-like orbit (a = 6778.137 km, circular, i = 51.6 deg) the node must regress by 5.0 +- 0.05 deg/day
(the textbook figure); a lineage outside is excluded.
Expected agreement: the formulas are first order in J2, so differences of order 1e-3 relative are the model, not a
defect; the numerical lineage additionally starts from osculating elements (semi-major axis off by up to ~10 km).
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
import star_j2 as sj  # noqa: E402

CONST = f"MU = {sj.MU!r}\nRE = {sj.RE!r}\nJ2 = {sj.J2!r}\n"
OREKIT = CONST + '''
import math
import orekit_jpype
orekit_jpype.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data
setup_orekit_data("/root/orekit-data.zip", from_pip_library=False)
from org.orekit.orbits import CircularOrbit, PositionAngleType
from org.orekit.frames import FramesFactory
from org.orekit.time import AbsoluteDate
from org.orekit.attitudes import FrameAlignedProvider
from org.orekit.propagation import PropagationType
from org.orekit.propagation.analytical import EcksteinHechlerPropagator
def f(a, e, inc, days):
    fr = FramesFactory.getEME2000()
    t0 = AbsoluteDate.J2000_EPOCH
    o = CircularOrbit(a * 1e3, e, 0.0, math.radians(inc), 0.5, 0.3, PositionAngleType.MEAN, fr, t0, MU * 1e9)
    p = EcksteinHechlerPropagator(o, FrameAlignedProvider(fr), 1000.0, RE * 1e3, MU * 1e9, -J2, 0.0, 0.0, 0.0, 0.0, PropagationType.MEAN)
    out = []
    n = int(days * 86400 / 600)
    for k in range(n + 1):
        s = CircularOrbit(p.propagate(t0.shiftedBy(600.0 * k)).getOrbit())
        out.append([600.0 * k, float(s.getRightAscensionOfAscendingNode()), None])
    return out
'''
NUMERICAL = CONST + '''
import math
import numpy as np
from scipy.integrate import solve_ivp
def rhs(t, y):
    x, yy, z, vx, vy, vz = y
    r2 = x * x + yy * yy + z * z
    r = math.sqrt(r2)
    k = 1.5 * J2 * MU * RE * RE / r2 ** 2.5
    q = 5.0 * z * z / r2
    return [vx, vy, vz, -MU * x / r ** 3 + k * x * (q - 1.0), -MU * yy / r ** 3 + k * yy * (q - 1.0), -MU * z / r ** 3 + k * z * (q - 3.0)]
def state(a, e, inc):
    i, raan, argp = math.radians(inc), 0.5, 0.3
    p = a * (1 - e * e)
    rp = [p / (1 + e), 0.0, 0.0]
    vp = [0.0, math.sqrt(MU / p) * (1 + e), 0.0]
    cO, sO, ci, si, cw, sw = math.cos(raan), math.sin(raan), math.cos(i), math.sin(i), math.cos(argp), math.sin(argp)
    R = [[cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci, sO * si], [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci, -cO * si], [sw * si, cw * si, ci]]
    return [sum(R[j][k] * rp[k] for k in range(3)) for j in range(3)] + [sum(R[j][k] * vp[k] for k in range(3)) for j in range(3)]
def f(a, e, inc, days):
    ts = np.arange(0.0, days * 86400.0 + 1.0, 600.0)
    sol = solve_ivp(rhs, (0.0, ts[-1]), state(a, e, inc), method="DOP853", t_eval=ts, rtol=1e-11, atol=1e-9)
    out = []
    for t, y in zip(sol.t, sol.y.T):
        r, v = y[:3], y[3:]
        h = np.cross(r, v)
        node = np.array([-h[1], h[0], 0.0])
        ev = np.cross(v, h) / MU - r / np.linalg.norm(r)
        raan = math.atan2(node[1], node[0])
        argp = math.atan2(float(np.dot(np.cross(node, ev), h)) / float(np.linalg.norm(h)), float(np.dot(node, ev)))
        out.append([float(t), raan, argp])
    return out
'''
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:120])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"orekit_eh": (["wsl", "-u", "root", "--", "/root/orekit_venv/bin/python", "-W", "ignore", "-c"], OREKIT, "circular"),
           "numerical": ([str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), "-W", "ignore", "-c"], NUMERICAL, "all")}
DAYS = 20.0
PROBE = [6778.137, 0.0, 51.6, DAYS]


def slope_deg_day(samples, column):
    """Least-squares slope (deg/day) of an angle sampled in time, after unwrapping."""
    ts, ys, prev, turns = [], [], None, 0.0
    for row in samples:
        y = row[column]
        if prev is not None:
            turns += -2 * math.pi if y - prev > math.pi else 2 * math.pi if y - prev < -math.pi else 0.0
        prev = y
        ts.append(row[0])
        ys.append(y + turns)
    n = len(ts)
    mt, my = sum(ts) / n, sum(ys) / n
    return math.degrees(sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / sum((t - mt) ** 2 for t in ts)) * 86400.0


def corpus():
    rnd = random.Random(20261006)
    circular = [[round(rnd.uniform(6650.0, 9000.0), 3), 0.0, round(rnd.uniform(1.0, 179.0), 3), DAYS] for _ in range(30)]
    eccentric = [[round(rnd.uniform(8000.0, 27000.0), 3), round(rnd.uniform(0.05, 0.25), 4), round(rnd.uniform(5.0, 175.0), 3), DAYS] for _ in range(20)]
    return [PROBE] + circular, [PROBE] + circular + eccentric


def main():
    circ, everything = corpus()
    out = {"days": DAYS, "seed": 20261006, "lineages": {}}
    for name, (cmd, driver, scope) in DRIVERS.items():
        cases = circ if scope == "circular" else everything
        r = subprocess.run(cmd + [driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-1200:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        probe = slope_deg_day(res[0], 1) if isinstance(res[0], list) else math.nan
        valid = abs(probe + 5.0) <= 0.05
        entry = {"cases": len(cases) - 1, "probe_valid": valid, "probe_raan_rate_deg_day": probe, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            raan_rel, raan_abs, argp_abs, argp_n = 0.0, 0.0, 0.0, 0
            for c, x in zip(cases[1:], res[1:]):
                if isinstance(x, str):
                    continue
                mine = sj.raan_rate_deg_day(c[0], c[1], c[2])
                got = slope_deg_day(x, 1)
                raan_abs = max(raan_abs, abs(mine - got))
                if abs(mine) > 0.5:
                    raan_rel = max(raan_rel, abs(got / mine - 1.0))
                if c[1] >= 0.05 and x[0][2] is not None:
                    argp_abs = max(argp_abs, abs(sj.argp_rate_deg_day(c[0], c[1], c[2]) - slope_deg_day(x, 2)))
                    argp_n += 1
            entry.update(raan_rate_max_relative_diff=raan_rel, raan_rate_max_abs_diff_deg_day=raan_abs,
                         argp_rate_max_abs_diff_deg_day=argp_abs if argp_n else None, argp_cases=argp_n)
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "probe %.4f deg/day" % probe, "errors", len(errors), errors[:1],
              {k: v for k, v in entry.items() if "diff" in k}, flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_j2_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("->", dest.name)


if __name__ == "__main__":
    main()
