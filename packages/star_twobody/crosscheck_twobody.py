"""Cross-check of star_twobody against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_twobody.py  ->  12_EVIDENCE/crosscheck_twobody_20261006.json

Lineages, each in its own interpreter:
  spice    SPICE conics (state at periapsis and at apoapsis from the elements) and oscltx (semi-major axis and period
           from a state), C, for ANY mu: period, semi-major axis from period (inverted on its period), apsis radii and speeds;
  hapsira  hapsira.twobody.Orbit.from_classical on the Earth (its own mu, 398600.4418 km3/s2): period, mean motion,
           apsis radii, specific energy and the speed at periapsis.
Circular and escape speed are compared through their definitions on those libraries' numbers: the periapsis speed
of an orbit with e = 0 is the circular speed, and the energy at the escape speed is zero (v_esc^2 / 2 = mu / r).
Probe (published): a geostationary orbit has a period of one sidereal day, 86164.0905 s, and a radius of 42164.17 km
(e.g. Vallado, Fundamentals of Astrodynamics and Applications). A lineage whose period for a = 42164.17 km is further
than 0.01 s from that is excluded.
Corpus (seed 20261006): 600 orbits: semi-major axis 6600 to 400000 km, eccentricity 0 to 0.95 (one in six circular),
and for SPICE a gravitational parameter between the Moon's and the Sun's.
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
import star_twobody as tb  # noqa: E402

GEO = (42164.17, 86164.0905)
SPICE = ("import spiceypy as sp, math\ndef f(a, e, mu):\n"
         "    p = sp.conics([a * (1 - e), e, 0.3, 0.2, 0.1, 0.0, 0.0, mu], 0.0)\n"
         "    q = sp.conics([a * (1 - e), e, 0.3, 0.2, 0.1, math.pi, 0.0, mu], 0.0)\n"
         "    el = sp.oscltx(p, 0.0, mu)\n"
         "    return {'period': float(el[10]), 'a': float(el[9]), 'rp': math.hypot(*p[:3]), 'ra': math.hypot(*q[:3]), 'vp': math.hypot(*p[3:]), 'va': math.hypot(*q[3:])}\n")
HAPSIRA = ("from hapsira.twobody import Orbit\nfrom hapsira.bodies import Earth\nfrom astropy import units as u\nimport numpy as np\n"
           "def f(a, e, mu):\n"
           "    o = Orbit.from_classical(Earth, a * u.km, e * u.one, 10 * u.deg, 20 * u.deg, 30 * u.deg, 0 * u.deg)\n"
           "    return {'period': float(o.period.to_value(u.s)), 'n': float(o.n.to_value(u.rad / u.s)), 'rp': float(o.r_p.to_value(u.km)), 'ra': float(o.r_a.to_value(u.km)),\n"
           "            'energy': float(o.energy.to_value(u.km ** 2 / u.s ** 2)), 'vp': float(np.linalg.norm(o.v.to_value(u.km / u.s))), 'mu': float(Earth.k.to_value(u.km ** 3 / u.s ** 2))}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")


def venv(n):
    return str(ROOT / ".venvs" / n / "Scripts" / "python.exe")


DRIVERS = {"spice": (venv("spiceypy"), SPICE), "hapsira": (venv("hapsira"), HAPSIRA)}


def rel(a, b):
    return abs(a / b - 1.0)


def main():
    rnd = random.Random(20261006)
    cases = [[GEO[0], 0.0, tb.MU_EARTH]]
    for k in range(600):
        cases.append([rnd.uniform(6600, 400000), 0.0 if k % 6 == 0 else rnd.uniform(0, 0.95), 10 ** rnd.uniform(3.69, 11.12)])
    out = {"cases": len(cases) - 1, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        sent = cases if name == "spice" else [[c[0], c[1], tb.MU_EARTH] for c in cases]      # hapsira: the Earth only
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(sent), capture_output=True, text=True, timeout=1800)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(sent):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = isinstance(res[0], dict) and abs(res[0].get("period", 0.0) - GEO[1]) < 0.01 and (name == "spice" or abs(res[0].get("mu", 0.0) / tb.MU_EARTH - 1.0) < 1e-12)
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {}
            n = 0
            for c, x in zip(sent[1:], res[1:]):
                if isinstance(x, str):
                    continue
                n += 1
                a, e, mu = c
                rp, ra = tb.apsides(a, e)
                vp, va = tb.apsis_speeds(a, e, mu)
                pairs = {"period": rel(tb.period(a, mu), x["period"]), "periapsis_radius": rel(rp, x["rp"]), "apoapsis_radius": rel(ra, x["ra"]),
                         "periapsis_speed": rel(vp, x["vp"]), "semi_major_axis_from_period": rel(tb.semi_major_axis_from_period(x["period"], mu), a),
                         "elements_from_apsides": max(rel(tb.elements_from_apsides(x["rp"], x["ra"])[0], a), abs(tb.elements_from_apsides(x["rp"], x["ra"])[1] - e))}
                if "va" in x:
                    pairs["apoapsis_speed"] = rel(va, x["va"])
                    pairs["semi_major_axis"] = rel(a, x["a"])
                if "n" in x:
                    pairs["mean_motion"] = rel(tb.mean_motion(a, mu), x["n"])
                    pairs["specific_energy"] = rel(tb.specific_energy(a, mu), x["energy"])
                if e == 0.0:                                # the periapsis speed of a circle is the circular speed; escape is sqrt(2) times it
                    pairs["circular_speed"] = rel(tb.circular_speed(a, mu), x["vp"])
                    pairs["escape_speed"] = rel(tb.escape_speed(a, mu), math.sqrt(2.0) * x["vp"])
                for k2, v in pairs.items():
                    m[k2] = max(m.get(k2, 0.0), v)
            entry.update(compared=n, **{"max_" + k2 + "_rel": v for k2, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k[4:-4]: v for k, v in entry.items() if k.startswith("max_")}, flush=True)
    L = out["lineages"]
    S, H = L["spice"], L["hapsira"]
    mine = abs(tb.period(GEO[0]) - GEO[1])
    worst = {n: max((v for k, v in e.items() if k.startswith("max_")), default=1.0) for n, e in L.items()}
    need = ["period", "periapsis_radius", "apoapsis_radius", "periapsis_speed", "apoapsis_speed", "semi_major_axis_from_period", "circular_speed", "escape_speed", "elements_from_apsides"]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and mine < 0.01 \
        and all(("max_" + k + "_rel") in S for k in need) and "max_mean_motion_rel" in H and "max_specific_energy_rel" in H \
        and worst["spice"] < 1e-11 and worst["hapsira"] < 1e-11
    out["published"] = {"source": "geostationary orbit: one sidereal day, 86164.0905 s, at 42164.17 km (Vallado)", "star_twobody_abs_diff_s": mine}
    out["summary"] = {"ok": ok, "lineages": ["SPICE conics / oscltx (C, any mu)", "hapsira Orbit.from_classical (Earth)", "geostationary orbit: sidereal day at 42164.17 km"],
                      "claim": "star_twobody gives the period, the sizes and the speeds of a Keplerian ellipse as two independent libraries do",
                      "crosscheck": f"600 orbits (a 6600 to 400000 km, e 0 to 0.95, 100 circular): period, apsis radii and speeds, semi-major axis from period, circular and escape "
                                    f"speed within {worst['spice']:.1e} relative of SPICE for a gravitational parameter from the Moon's to the Sun's; period, mean motion, apsis "
                                    f"radii, periapsis speed and specific energy within {worst['hapsira']:.1e} of hapsira on the Earth; geostationary period within {mine:.4f} s "
                                    f"of the sidereal day",
                      "benchmark": f"largest relative difference: SPICE {worst['spice']:.1e}, hapsira {worst['hapsira']:.1e}"}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_twobody_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "GEO period diff %.4f s" % mine, "->", dest.name)


if __name__ == "__main__":
    main()
