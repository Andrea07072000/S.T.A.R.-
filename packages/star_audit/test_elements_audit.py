"""The elements auditor must itself be right: its own generator must round-trip through an exact inverse written here,
and synthetic implementations with KNOWN defects and conventions must be classified exactly as constructed.
Verifies: R10 (README).
"""
import math
import sys

import pytest

from elements_audit import (ELEMENTS, VALIDATION_TOL, VALLADO_COE, VALLADO_RV, audit, classify, coe_to_rv, corpus,
                            diff)

CMD = [sys.executable, "-c"]
# reference implementation written from the textbook (Curtis Alg. 4.2), with explicit conventions for the singular
# cases: argp := 0 when circular, raan := 0 when equatorial
REF = r'''
import math
def _d(a, b): return sum(x * y for x, y in zip(a, b))
def _c(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def elements(r, v, mu):
    R, V = math.sqrt(_d(r, r)), math.sqrt(_d(v, v))
    h = _c(r, v); H = math.sqrt(_d(h, h))
    i = math.degrees(math.acos(max(-1.0, min(1.0, h[2] / H))))
    n = [-h[1], h[0], 0.0]; N = math.sqrt(_d(n, n))
    ev = [((V*V - mu/R) * r[k] - _d(r, v) * v[k]) / mu for k in range(3)]; e = math.sqrt(_d(ev, ev))
    raan = 0.0 if N < 1e-6 * H else math.degrees(math.atan2(n[1], n[0])) % 360.0
    if e < 1e-9:
        argp = 0.0
        nu = math.degrees(math.atan2(_d(_c(n if N >= 1e-6 * H else [1.0, 0.0, 0.0], r), h) / H, _d(n if N >= 1e-6 * H else [1.0, 0.0, 0.0], r))) % 360.0
    else:
        ref = n if N >= 1e-6 * H else [1.0, 0.0, 0.0]
        argp = math.degrees(math.atan2(_d(_c(ref, ev), h) / H, _d(ref, ev))) % 360.0
        nu = math.degrees(math.atan2(_d(_c(ev, r), h) / H, _d(ev, r))) % 360.0
    return {"p": H * H / mu, "e": e, "i": i, "raan": raan, "argp": argp, "nu": nu}
'''


def impl(code, lineage="L"):
    return {"command": CMD, "driver": code, "lineage": lineage}


def test_generator_reproduces_vallado_example_2_5_backwards():
    r, v = coe_to_rv(**VALLADO_COE)
    # the book prints argp to 0.01 deg and i to 0.001 deg: at r ~ 11 000 km that alone is worth ~1 km
    assert math.dist(r, VALLADO_RV[0]) < 1.5 and math.dist(v, VALLADO_RV[1]) < 1e-3


def test_corpus_layout_and_determinism():
    c = corpus()
    assert c == corpus() and len(c) == 80
    assert [x["kind"] for x in c].count("regular") == 60 and {x["kind"] for x in c[60:]} == {"circular", "equatorial",
                                                                                           "circular_equatorial"}
    assert all(x["truth"]["e"] == 1e-12 for x in c[60:] if "circular" in x["kind"])
    assert all(x["truth"]["i"] == 1e-10 for x in c[60:] if "equatorial" in x["kind"])


def test_reference_implementation_is_exact_on_regular_cases_and_valid():
    a = audit({"ref": impl(REF)})
    assert a["validation"]["ref"]["valid"] and a["validated"] == ["ref"]
    assert max(a["regular_vs_truth"]["ref"]["max_dev"].values()) < 1e-7
    assert a["singular_conventions"]["ref"]["circular_equatorial"] == {"raan=0,argp=0": 8}


def test_defects_and_conventions_are_classified():
    wrong_i = REF.replace('"i": i,', '"i": i + 0.02,')                 # beyond the 0.01 deg validation tolerance
    sentinel = REF.replace("argp = 0.0\n", "argp = 999999.1 * 57.29577951308232\n")
    nan_conv = REF.replace("argp = 0.0\n", "argp = float('nan')\n")
    late = REF.replace('"nu": nu}', '"nu": nu + (1e-6 if e > 0.5 else 0.0)}')
    a = audit({"ref": impl(REF, "A"), "wrong_i": impl(wrong_i), "sentinel": impl(sentinel), "nan": impl(nan_conv),
               "late": impl(late, "A")})
    # deviation = injected 0.02 deg minus the book's own rounding of i (8.7e-4 deg)
    assert not a["validation"]["wrong_i"]["valid"] and 0.019 < a["validation"]["wrong_i"]["dev"]["i"] < 0.021
    assert a["singular_conventions"]["sentinel"]["circular"] == {"raan=value,argp=sentinel": 6}
    assert a["singular_conventions"]["nan"]["circular"] == {"raan=value,argp=nan": 6}
    p = a["pairs"]["late|ref"]
    assert p["same_lineage"] and abs(p["max_dev"]["nu"] - 1e-6) < 1e-9 and p["max_dev"]["p"] < 1e-9


def test_helpers():
    assert classify(float("nan")) == "nan" and classify(5.7e7) == "sentinel" and classify(0.0) == "0"
    assert classify(12.5) == "value" and classify(-1e-12) == "0"
    assert diff({"nu": 359.5}, {"nu": 0.5}, "nu") == 1.0 and diff({"p": 10.0}, {"p": 12.5}, "p") == 2.5
    assert set(VALIDATION_TOL) == set(ELEMENTS) and VALIDATION_TOL["e"] == 1e-5


def test_failures():
    msg = "A" * 50 + "B" * 400
    with pytest.raises(RuntimeError) as e:
        audit({"f": impl(f"import sys\nsys.stderr.write({msg!r})\nraise SystemExit(2)\n")})
    assert str(e.value).split("implementation run failed: ", 1)[1] == msg[-300:]
    a = audit({"x": impl("def elements(r, v, mu):\n    raise ValueError('no')\n")})
    assert not a["validation"]["x"]["valid"] and "ValueError" in a["validation"]["x"]["why"]


def test_corpus_is_pinned_by_fingerprint():
    # floats rounded to 9 decimals before hashing: the raw-float hash differed between Windows and Linux (last-bit
    # differences of the C math library), found by the cross-OS reproduction of star-audit 0.8.0 on 2026-10-05
    from corpus_fingerprint import fingerprint
    assert fingerprint(corpus()) == "f056a27c76ca8b9d570c837eb8e0a7c09f4b45cfd4aa3be925a975a47669ddb2"


def test_classify_and_tolerance_boundaries_are_exact():
    assert classify(1e5) == "value" and classify(1e5 + 1) == "sentinel" and classify(-2e5) == "sentinel"
    assert classify(1e-9) == "value" and classify(9.9e-10) == "0"
    assert VALIDATION_TOL == {"p": 0.01, "e": 1e-5, "i": 0.01, "raan": 0.01, "argp": 0.01, "nu": 0.01}
    assert diff({"i": 10.0}, {"i": 350.0}, "i") == 20.0 and diff({"e": 0.3}, {"e": 0.1}, "e") == pytest.approx(0.2)


def test_generator_geometry_is_independently_correct():
    # i = 90, raan = 30, argp = 0, nu = 0: periapsis on the node line, momentum perpendicular to it
    r, v = coe_to_rv(p=10000.0, e=0.25, i=90.0, raan=30.0, argp=0.0, nu=0.0)
    rp = 10000.0 / 1.25
    assert r == pytest.approx([rp * math.cos(math.radians(30)), rp * math.sin(math.radians(30)), 0.0], abs=1e-9)
    h = [r[1] * v[2] - r[2] * v[1], r[2] * v[0] - r[0] * v[2], r[0] * v[1] - r[1] * v[0]]
    assert math.sqrt(sum(x * x for x in h)) == pytest.approx(math.sqrt(398600.4418 * 10000.0), rel=1e-12)
    assert h[2] == pytest.approx(0.0, abs=1e-6)                         # polar orbit: no z momentum


def test_noise_and_partial_refusals_are_counted():
    noisy = "print('banner')\n" + REF
    picky = REF.replace("def elements(r, v, mu):\n", "def elements(r, v, mu):\n    if r[0] < 0: raise ValueError('west')\n")
    a = audit({"noisy": impl(noisy), "picky": impl(picky)})
    far = sum(1 for c in corpus()[:60] if c["r"][0] < 0)          # Vallado case has x > 0: validation unaffected
    assert a["validation"]["noisy"]["valid"] and a["validation"]["picky"]["valid"] and far >= 1
    assert a["regular_vs_truth"]["picky"]["refused"] == far and a["regular_vs_truth"]["noisy"]["refused"] == 0
