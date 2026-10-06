"""Cross-check of star_atmosphere.ussa1976 against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_atmosphere.py  ->  12_EVIDENCE/crosscheck_atmosphere_20261006.json

Lineages, each in its own interpreter:
  fluids    fluids.ATMOSPHERE_1976 (C. Bell's chemical-engineering library, own implementation);
  hapsira   hapsira.earth.atmosphere.COESA76 (astrodynamics library, table-driven implementation).
Every lineage is first PROBED on values printed in "U.S. Standard Atmosphere, 1976": sea level (288.15 K, 101325 Pa)
and the base of the stratosphere, geopotential 11 km (216.65 K, 22632.06 Pa): within 1e-5 relative, or excluded.
Corpus (seed 20261006): 300 geometric altitudes uniform in [0, 86 km] plus the seven layer boundaries.
Measured: relative difference of temperature, pressure and density, per layer.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_atmosphere as sa  # noqa: E402

V = ROOT / ".venvs"
DRIVERS = {
    "fluids": (V / "thermo", "import fluids\ndef f(z):\n    a = fluids.ATMOSPHERE_1976(z)\n    return [float(a.T), float(a.P), float(a.rho)]\n"),
    "hapsira": (V / "hapsira", "from astropy import units as u\nfrom hapsira.earth.atmosphere import COESA76\nc = COESA76()\n"
                "def f(z):\n    T, p, rho = c.properties(z * u.m)\n    return [float(T.to_value(u.K)), float(p.to_value(u.Pa)), float(rho.to_value(u.kg / u.m**3))]\n"),
}
RUNNER = ("\nimport json, sys\nout = []\nfor z in json.load(sys.stdin):\n    try:\n        out.append(f(z))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
PROBES = [(0.0, 288.15, 101325.0), (sa.geometric_m(11000.0), 216.65, 22632.06)]
NAMES = ["0-11 km", "11-20 km", "20-32 km", "32-47 km", "47-51 km", "51-71 km", "71-84.852 km"]


def layer(z):
    h = sa.geopotential_m(z)
    return NAMES[max(i for i, (hb, _) in enumerate(sa.LAYERS) if h >= hb - 1e-9)]


def main():
    rnd = random.Random(20261006)
    zs = [p[0] for p in PROBES] + [sa.geometric_m(hb) for hb, _ in sa.LAYERS[1:]] + [round(rnd.uniform(0.0, 86000.0), 3) for _ in range(300)]
    mine = [sa.ussa1976(z) for z in zs]
    out = {"altitudes": len(zs), "seed": 20261006, "lineages": {}}
    for name, (venv, driver) in DRIVERS.items():
        r = subprocess.run([str(venv / "Scripts" / "python.exe"), "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(zs),
                           capture_output=True, text=True, timeout=900)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(zs):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = all(isinstance(x, list) and abs(x[0] / t - 1) <= 1e-5 and abs(x[1] / p - 1) <= 1e-5 for x, (_, t, p) in zip(res, PROBES))
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            worst = {}
            for z, m, x in zip(zs, mine, res):
                if isinstance(x, list):
                    k = layer(z)
                    old = worst.get(k, [0.0, 0.0, 0.0])
                    worst[k] = [max(o, abs(a / b - 1)) for o, a, b in zip(old, m[:3], x)]
            entry["max_relative_diff_T_P_rho_by_layer"] = {k: worst[k] for k in NAMES if k in worst}
            entry["max_relative_diff_T_P_rho"] = [max(v[i] for v in worst.values()) for i in range(3)]
        out["lineages"][name] = entry
        print(name, "valid" if valid else "EXCLUDED", "errors", len(errors), errors[:1],
              ["%.1e" % v for v in entry["max_relative_diff_T_P_rho"]] if valid else res[:2], flush=True)
    dest = ROOT / "12_EVIDENCE" / "crosscheck_atmosphere_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("->", dest.name)


if __name__ == "__main__":
    main()
