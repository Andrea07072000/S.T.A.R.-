"""Cross-check of star_sigma against two independent implementations (S.T.A.R., 2026-10-06).

  python crosscheck_sigma.py  ->  12_EVIDENCE/crosscheck_sigma_20261006.json

Lineages, each in its own interpreter:
  scipy   scipy.stats.norm (cdf, sf, ppf) and scipy.stats.chi2 (cdf, sf, ppf) in double precision (Cephes / Boost);
  mpmath  mpmath with 40 digits: ncdf, erfc and the regularised incomplete gamma function; for the inverses it
          evaluates the distribution at the value star_sigma returned (a residual, not a second root finder).
Probes (published; e.g. Abramowitz and Stegun, table 26.1, and any table of the normal distribution): the coverage of
1, 2 and 3 sigma on a line is 0.682689, 0.954500, 0.997300; Phi(1.959964) = 0.975. A lineage further than 2e-6 is excluded.
Corpus (seed 20261006): 600 cases: z in [-37, 37] (half of them within +-4), n sigma from 1e-4 to 12 in 1, 2 and 3
dimensions (a third of them below 1, where the three-dimensional closed form cancels), probabilities from 1e-12 to
1 - 1e-12.
Differences are RELATIVE, so that a tail of 1e-300 is held to the same standard as a coverage of 0.5.
"""
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import star_sigma as ss  # noqa: E402

SCIPY = ("from scipy import stats\ndef f(z, n, p, mine):\n"
         "    return {'cdf': float(stats.norm.cdf(z)), 'sf': float(stats.norm.sf(z)), 'q': float(stats.norm.ppf(p)),\n"
         "            'cov': [float(stats.chi2.cdf(n * n, d)) for d in (1, 2, 3)], 'tail': [float(stats.chi2.sf(n * n, d)) for d in (1, 2, 3)],\n"
         "            'inv': [float(stats.chi2.ppf(p, d)) ** 0.5 for d in (1, 2, 3)]}\n")
MPMATH = ("import mpmath as mp\nmp.mp.dps = 40\ndef f(z, n, p, mine):\n"
          "    t = mp.mpf(n) ** 2 / 2\n"
          "    cov = [mp.gammainc(mp.mpf(d) / 2, 0, t, regularized=True) for d in (1, 2, 3)]\n"
          "    tail = [mp.gammainc(mp.mpf(d) / 2, t, mp.inf, regularized=True) for d in (1, 2, 3)]\n"
          "    q, inv = mp.mpf(mine['q']), [mp.mpf(v) for v in mine['inv']]\n"
          "    return {'cdf': float(mp.ncdf(z)), 'sf': float(mp.ncdf(-mp.mpf(z))), 'cov': [float(v) for v in cov], 'tail': [float(v) for v in tail],\n"
          "            'q_lower': float(mp.ncdf(q)), 'q_upper': float(mp.ncdf(-q)),\n"
          "            'inv_cov': [float(mp.gammainc(mp.mpf(d) / 2, 0, inv[d - 1] ** 2 / 2, regularized=True)) for d in (1, 2, 3)],\n"
          "            'inv_tail': [float(mp.gammainc(mp.mpf(d) / 2, inv[d - 1] ** 2 / 2, mp.inf, regularized=True)) for d in (1, 2, 3)]}\n")
RUNNER = ("\nimport json, sys\nout = []\nfor c in json.load(sys.stdin):\n    try:\n        out.append(f(*c))\n"
          "    except Exception as e:\n        out.append('error:' + type(e).__name__ + ':' + str(e)[:60])\nprint('@@' + json.dumps(out))\n")
DRIVERS = {"scipy": (str(ROOT / ".venvs" / "scipy" / "Scripts" / "python.exe"), SCIPY), "mpmath": (str(ROOT / ".venvs" / "mpmath" / "Scripts" / "python.exe"), MPMATH)}
PUBLISHED = (0.682689, 0.954500, 0.997300, 0.975)


def rel(a, b):
    return abs(a - b) / abs(b) if b else abs(a)


def main():
    rnd = random.Random(20261006)

    def case(z, n, p):
        return [z, n, p, {"q": ss.normal_quantile(p), "inv": [ss.sigma_for_coverage(p, d) for d in (1, 2, 3)]}]

    cases = [case(1.959964, 1.0, 0.975), case(0.0, 2.0, 0.5), case(0.0, 3.0, 0.5)]
    for k in range(600):
        z = rnd.uniform(-4, 4) if k % 2 else rnd.uniform(-37, 37)
        n = 10 ** rnd.uniform(-4, 0) if k % 3 == 0 else rnd.uniform(1, 12)
        e = 10 ** rnd.uniform(-12, -0.31)
        cases.append(case(z, n, e if k % 2 else 1.0 - e))
    out = {"cases": len(cases) - 3, "seed": 20261006, "lineages": {}}
    for name, (py, driver) in DRIVERS.items():
        r = subprocess.run([py, "-W", "ignore", "-c", driver + RUNNER], input=json.dumps(cases), capture_output=True, text=True, timeout=1800)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("@@")]
        if r.returncode or not line:
            raise SystemExit(f"{name}: driver failed\n{r.stderr[-800:]}")
        res = json.loads(line[0][2:])
        if not isinstance(res, list) or len(res) != len(cases):
            raise SystemExit(f"{name}: wrong number of answers")
        errors = [x for x in res if isinstance(x, str)]
        valid = all(isinstance(x, dict) for x in res[:3]) and abs(res[0]["cov"][0] - PUBLISHED[0]) < 2e-6 and abs(res[1]["cov"][0] - PUBLISHED[1]) < 2e-6 \
            and abs(res[2]["cov"][0] - PUBLISHED[2]) < 2e-6 and abs(res[0]["cdf"] - PUBLISHED[3]) < 2e-6
        entry = {"probe_valid": valid, "errors": len(errors), "first_error": errors[:1]}
        if valid:
            m = {"cdf": 0.0, "sf": 0.0, "coverage": 0.0, "tail": 0.0, "quantile": 0.0, "sigma_for_coverage": 0.0}
            n_cases = 0
            for c, x in zip(cases[3:], res[3:]):
                if isinstance(x, str):
                    continue
                n_cases += 1
                z, n, p, mine = c
                m["cdf"] = max(m["cdf"], rel(ss.normal_cdf(z), x["cdf"]))
                m["sf"] = max(m["sf"], rel(ss.normal_sf(z), x["sf"]))
                for d in (1, 2, 3):
                    m["coverage"] = max(m["coverage"], rel(ss.sigma_coverage(n, d), x["cov"][d - 1]))
                    m["tail"] = max(m["tail"], rel(ss.sigma_tail(n, d), x["tail"][d - 1]))
                small = min(p, 1.0 - p)                     # the probability of the nearer tail: what the caller really specified
                if "q" in x:
                    m["quantile"] = max(m["quantile"], abs(mine["q"] - x["q"]) / max(1.0, abs(x["q"])))
                    for d in (1, 2, 3):
                        m["sigma_for_coverage"] = max(m["sigma_for_coverage"], abs(mine["inv"][d - 1] - x["inv"][d - 1]) / max(1.0, x["inv"][d - 1]))
                else:                                       # residual of the root in the nearer tail, relative
                    m["quantile"] = max(m["quantile"], rel(x["q_lower"] if p <= 0.5 else x["q_upper"], small))
                    for d in (1, 2, 3):
                        m["sigma_for_coverage"] = max(m["sigma_for_coverage"], rel(x["inv_cov"][d - 1] if p <= 0.5 else x["inv_tail"][d - 1], small))
            entry.update(compared=n_cases, **{"max_" + k + "_rel": v for k, v in m.items()})
        out["lineages"][name] = entry
        print(name, "valid" if valid else f"EXCLUDED {res[0]}", "errors", len(errors), errors[:1], {k[4:-4]: v for k, v in entry.items() if k.startswith("max_")}, flush=True)
    L = out["lineages"]
    S, M = L["scipy"], L["mpmath"]
    mine_ok = all(abs(ss.sigma_coverage(n, 1) - v) < 2e-6 for n, v in zip((1, 2, 3), PUBLISHED)) and abs(ss.normal_cdf(1.959964) - PUBLISHED[3]) < 2e-6
    direct = [M.get("max_" + k + "_rel") for k in ("cdf", "sf", "coverage", "tail")]
    ok = all(v["probe_valid"] and not v["errors"] and v.get("compared") == 600 for v in L.values()) and mine_ok and all(x is not None for x in direct) \
        and max(direct) < 5e-13 and max(M["max_quantile_rel"], M["max_sigma_for_coverage_rel"]) < 1e-10 \
        and max(S["max_cdf_rel"], S["max_sf_rel"], S["max_coverage_rel"], S["max_tail_rel"]) < 1e-10 and max(S["max_quantile_rel"], S["max_sigma_for_coverage_rel"]) < 1e-9
    out["published"] = {"source": "tables of the normal distribution (Abramowitz and Stegun 26.1): 1, 2, 3 sigma = 0.682689, 0.954500, 0.997300; Phi(1.959964) = 0.975",
                        "star_sigma_reproduces": mine_ok}
    if all(x is not None for x in direct):
        out["summary"] = {"ok": ok, "lineages": ["scipy.stats norm / chi2 (double precision)", "mpmath at 40 digits (ncdf, incomplete gamma)", "tables of the normal distribution"],
                          "claim": "star_sigma gives the coverage and the tail of n sigma in 1, 2 and 3 dimensions, and their inverses, to the accuracy of double precision, tails included",
                          "crosscheck": f"600 cases (z to +-37, n sigma from 1e-4 to 12, probabilities from 1e-12 to 1 - 1e-12), RELATIVE differences: cdf, sf, coverage and tail within "
                                        f"{max(direct):.1e} of mpmath at 40 digits and {max(S['max_cdf_rel'], S['max_sf_rel'], S['max_coverage_rel'], S['max_tail_rel']):.1e} of SciPy; "
                                        f"the inverses reproduce the requested tail probability within {max(M['max_quantile_rel'], M['max_sigma_for_coverage_rel']):.1e} (mpmath) and "
                                        f"agree with SciPy's within {max(S['max_quantile_rel'], S['max_sigma_for_coverage_rel']):.1e}",
                          "benchmark": f"mpmath: direct {max(direct):.1e}, inverse residual {max(M['max_quantile_rel'], M['max_sigma_for_coverage_rel']):.1e}"}
    else:
        out["summary"] = {"ok": False}
    dest = ROOT / "12_EVIDENCE" / "crosscheck_sigma_20261006.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("ok" if ok else "NOT OK", "published reproduced:", mine_ok, "->", dest.name)


if __name__ == "__main__":
    main()
