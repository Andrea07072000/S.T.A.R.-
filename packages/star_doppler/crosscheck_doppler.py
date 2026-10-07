"""Cross-check of star_doppler against four independent implementations (S.T.A.R., 2026-10-07).

  python crosscheck_doppler.py  ->  12_EVIDENCE/crosscheck_doppler_20261007.json

Lineages, each in its own interpreter; each returns [range, range rate, relativistic frequency, first-order frequency],
with None where it has no such result:
  spice    NAIF SPICE on the relative state: vnorm (the range) and dvnorm (the derivative of the norm: the range rate);
  astropy  astropy.units Doppler equivalencies for the two frequencies (doppler_relativistic, doppler_radio);
  numpy    numpy.linalg.norm and numpy.dot for range and range rate;
  mpmath   all four quantities at 40 digits: the truth for the rounding error.
Probe (by hand): a source receding at 0.6 c is received at half its frequency, sqrt(0.4 / 1.6) = 0.5 exactly, and at
0.4 of it by the first-order formula; relative position (3, 4, 0) with relative velocity (1, 0, 0) is at range 5 and
range rate 0.6.
Corpus (seed 20261007): 600 pairs of states: a ground site and a low orbit in km and km/s, states of mixed magnitude,
relative velocities nearly perpendicular to the line of sight (where the range rate cancels); frequencies from 1e6 to
1e11 Hz and, for the frequency formulas, range rates up to 0.9 c of either sign. The range is compared relative to
itself, the range rate relative to the relative speed, the frequencies relative to themselves.
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
import star_doppler as sd  # noqa: E402

SPICE = """import spiceypy as sp
def f(ro, vo, rt, vt, freq, rate):
    state = [rt[i] - ro[i] for i in range(3)] + [vt[i] - vo[i] for i in range(3)]
    return [float(sp.vnorm(state[:3])), float(sp.dvnorm(state)), None, None]
"""
ASTROPY = """import astropy.units as u
def f(ro, vo, rt, vt, freq, rate):
    f0 = freq * u.Hz
    v = rate * u.km / u.s
    return [None, None, float(v.to(u.Hz, u.doppler_relativistic(f0)).value), float(v.to(u.Hz, u.doppler_radio(f0)).value)]
"""
NUMPY = """import numpy as np
def f(ro, vo, rt, vt, freq, rate):
    dr = np.array(rt) - np.array(ro); dv = np.array(vt) - np.array(vo)
    n = float(np.linalg.norm(dr))
    return [n, float(np.dot(dr, dv) / n), None, None]
"""
MPMATH = """import mpmath as mp
mp.mp.dps = 40
C = mp.mpf('299792.458')
def f(ro, vo, rt, vt, freq, rate):
    dr = [mp.mpf(rt[i]) - mp.mpf(ro[i]) for i in range(3)]; dv = [mp.mpf(vt[i]) - mp.mpf(vo[i]) for i in range(3)]
    n = mp.sqrt(mp.fsum(c * c for c in dr))
    b = mp.mpf(rate) / C
    return [float(n), float(mp.fsum(a * c for a, c in zip(dr, dv)) / n), float(mp.mpf(freq) * mp.sqrt((1 - b) / (1 + b))), float(mp.mpf(freq) * (1 - b))]
"""
RUNNER = """
import json, sys
out = []
for c in json.load(sys.stdin):
    try:
        out.append(f(*c))
    except Exception as e:
        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])
print('@@' + json.dumps(out))
"""
PROBE = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [3.0, 4.0, 0.0], [1.0, 0.0, 0.0], 1000.0, 0.6 * sd.C_KM_S]
EXPECTED = [5.0, 0.6, 500.0, 400.0]
LIMIT = {"range": 1e-14, "rate": 1e-13, "relativistic": 1e-14, "first_order": 1e-14}
NAMES = ("range", "rate", "relativistic", "first_order")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"spice": (venv("spiceypy"), SPICE), "astropy": (venv("astropy"), ASTROPY), "numpy": (venv("scipy"), NUMPY), "mpmath": (venv("mpmath"), MPMATH)}


def mine(ro, vo, rt, vt, freq, rate):
    return list(sd.range_and_rate(ro, vo, rt, vt)) + [sd.received_frequency(freq, rate), sd.received_frequency(freq, rate, False)]


def main():
    rnd = random.Random(20261007)
    cases = [PROBE]

    def direction():
        v = [rnd.gauss(0, 1) for _ in range(3)]
        n = math.sqrt(sum(c * c for c in v))
        return [c / n for c in v]

    for k in range(600):
        kind = k % 3
        if kind == 0:                                        # a ground site and a low orbit, km and km/s
            ro = [6378.0 * c for c in direction()]
            vo = [0.465 * c for c in direction()]
            rt = [rnd.uniform(6700.0, 7400.0) * c for c in direction()]
            vt = [rnd.uniform(7.2, 7.8) * c for c in direction()]
        elif kind == 1:                                      # mixed magnitudes
            size, speed = 10 ** rnd.uniform(-3, 9), 10 ** rnd.uniform(-6, 4)
            ro, rt = [size * rnd.gauss(0, 1) for _ in range(3)], [size * rnd.gauss(0, 1) for _ in range(3)]
            vo, vt = [speed * rnd.gauss(0, 1) for _ in range(3)], [speed * rnd.gauss(0, 1) for _ in range(3)]
        else:                                                # relative velocity nearly perpendicular to the line of sight
            ro, vo = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
            line = direction()
            across = direction()
            dot = sum(a * b for a, b in zip(line, across))
            across = [a - dot * b for a, b in zip(across, line)]
            rt = [1000.0 * c for c in line]
            vt = [7.5 * a + rnd.uniform(-1e-6, 1e-6) * b for a, b in zip(across, line)]
        rate = rnd.uniform(-8.0, 8.0) if k % 4 else rnd.uniform(-0.9, 0.9) * sd.C_KM_S
        cases.append([ro, vo, rt, vt, 10 ** rnd.uniform(6, 11), rate])
    total = len(cases) - 1
    ours = [mine(*c) for c in cases]
    out = {"cases": total, "seed": 20261007, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=3000)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = not isinstance(res[0], str) and all(v is None or abs(v - e) <= 1e-12 * abs(e) for v, e in zip(res[0], EXPECTED)) and any(v is not None for v in res[0])
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst = {}
            n = 0
            for c, got, ref in zip(cases[1:], ours[1:], res[1:]):
                if isinstance(ref, str):
                    continue
                n += 1
                speed = math.sqrt(sum((c[3][i] - c[1][i]) ** 2 for i in range(3))) or 1.0
                scales = (abs(got[0]), speed, abs(got[2]), abs(got[3]))
                for stat, a, b, s in zip(NAMES, got, ref, scales):
                    if b is not None:
                        worst[stat] = max(worst.get(stat, 0.0), abs(a - b) / s)
            entry.update(compared=n, max_scaled_diff=worst, within=all(v <= LIMIT[k] for k, v in worst.items()))
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {str(res[0])[:120]}", "errors", len(errors), errors[:1], entry.get("max_scaled_diff"), flush=True)
    L = out["lineages"]
    mine_ok = ours[0] == EXPECTED
    ok = mine_ok and all(v["probe_valid"] and not v["errors"] and v.get("compared") == total and v.get("within") for v in L.values())
    worst = max(max((v.get("max_scaled_diff") or {"": 0.0}).values()) for v in L.values())
    out["published"] = {"source": "by hand: at 0.6 c the relativistic factor is sqrt(0.4 / 1.6) = 0.5 and the first-order factor 0.4; relative position (3, 4, 0) and velocity (1, 0, 0) give range 5, "
                                  "range rate 0.6; speed of light 299792.458 km/s (SI definition)", "star_doppler_observed": ours[0], "star_doppler_reproduces": mine_ok}
    out["summary"] = {"ok": ok, "lineages": ["NAIF SPICE vnorm / dvnorm", "astropy Doppler equivalencies", "numpy", "mpmath at 40 digits"],
                      "claim": "star_doppler returns the range and range rate between two states and the frequency received over that link, relativistic or first order",
                      "crosscheck": f"{total} pairs of states (ground site and low orbit, mixed magnitudes, velocities nearly perpendicular to the line of sight) and range rates up to 0.9 c: range, range "
                                    f"rate and both frequencies agree with SPICE, astropy, NumPy and mpmath at 40 digits within {worst:.1e} of their natural scale",
                      "benchmark": f"largest scaled difference from mpmath at 40 digits: {max((L['mpmath'].get('max_scaled_diff') or {'': 0.0}).values()):.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_doppler_20261007.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, ours[0], "->", dest.name)


if __name__ == "__main__":
    main()
