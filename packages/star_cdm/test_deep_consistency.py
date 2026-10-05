"""deep_consistency on the official CCSDS 508.0-B examples, with the RTN projection checked against Orekit 13.1
(LOFType.QSW, orekit_rtn_probe.py, values frozen 2026-10-05) and on constructed messages whose truth is known."""
import copy
from pathlib import Path

import pytest

from star_cdm import deep_consistency, min_eigenvalue, parse_cdm, rtn_axes

C = Path(__file__).parent / "fixtures" / "corrected"
OREKIT_RTN = {"example_2.kvn": [27.363673490483507, -93.74605086000685, 709.0540139297735],
              "example_3.kvn": [-35599865.924851, -41899668.82915291, -4809869.596583522]}


def load(name):
    return parse_cdm((C / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(OREKIT_RTN))
def test_rtn_projection_matches_orekit(name):
    d = deep_consistency(load(name))["checks"]
    got = [d[f"RELATIVE_POSITION_{c}"]["computed"] for c in "RTN"]
    assert all(abs(a - b) < 1e-6 for a, b in zip(got, OREKIT_RTN[name])), (got, OREKIT_RTN[name])


def test_example_3_6_3_rtn_components_disagree_with_its_states_while_the_norms_agree():
    d = deep_consistency(load("example_2.kvn"))
    assert sorted(d["flags"]) == sorted(["RELATIVE_POSITION_T_INCONSISTENT_WITH_STATES",
                                         "RELATIVE_POSITION_N_INCONSISTENT_WITH_STATES",
                                         "RELATIVE_VELOCITY_T_INCONSISTENT_WITH_STATES",
                                         "RELATIVE_VELOCITY_N_INCONSISTENT_WITH_STATES"])
    c = d["checks"]
    norm = lambda k, which: sum(c[f"{k}_{x}"][which] ** 2 for x in "TN") ** 0.5
    assert abs(norm("RELATIVE_POSITION", "declared") - norm("RELATIVE_POSITION", "computed")) < 0.1
    assert abs(c["RELATIVE_SPEED"]["declared"] - c["RELATIVE_SPEED"]["computed"]) < 0.1


def test_example_3_6_4_states_are_inconsistent_everywhere():
    flags = deep_consistency(load("example_3.kvn"))["flags"]
    assert "RELATIVE_SPEED_INCONSISTENT_WITH_STATES" in flags and len([f for f in flags if "RELATIVE_" in f]) == 7


def test_published_covariances_pass_with_rounding_tolerance_and_fail_without():
    assert not [f for f in deep_consistency(load("example_1.kvn"))["flags"] if "COVARIANCE" in f]
    strict = deep_consistency(load("example_1.kvn"), psd_rel_tol=1e-9)["flags"]
    assert strict == ["OBJECT1_COVARIANCE_NOT_POSITIVE_SEMIDEFINITE"]


def consistent(cdm):
    """Rewrite the relative keywords from the states with an independent formula (explicit RTN basis)."""
    o1, o2, h = cdm["object1"], cdm["object2"], cdm["header"]
    R, T, N = rtn_axes([o1["X"], o1["Y"], o1["Z"]], [o1["X_DOT"], o1["Y_DOT"], o1["Z_DOT"]])
    dr = [1000 * (o2[k] - o1[k]) for k in ("X", "Y", "Z")]
    dv = [1000 * (o2[k] - o1[k]) for k in ("X_DOT", "Y_DOT", "Z_DOT")]
    for c, ax in zip("RTN", (R, T, N)):
        h[f"RELATIVE_POSITION_{c}"] = sum(a * b for a, b in zip(dr, ax))
        h[f"RELATIVE_VELOCITY_{c}"] = sum(a * b for a, b in zip(dv, ax))
    h["RELATIVE_SPEED"] = sum(x * x for x in dv) ** 0.5
    return cdm


def test_a_consistent_message_has_no_flags_and_each_perturbation_is_caught_alone():
    base = consistent(load("example_2.kvn"))
    assert deep_consistency(base)["flags"] == []
    for key, delta, tol_name in (("RELATIVE_POSITION_R", 1.5, "m"), ("RELATIVE_POSITION_T", -1.5, "m"),
                                 ("RELATIVE_POSITION_N", 1.5, "m"), ("RELATIVE_VELOCITY_R", 0.2, "ms"),
                                 ("RELATIVE_VELOCITY_T", -0.2, "ms"), ("RELATIVE_VELOCITY_N", 0.2, "ms"),
                                 ("RELATIVE_SPEED", 0.2, "ms")):
        m = copy.deepcopy(base)
        m["header"][key] += delta
        assert deep_consistency(m)["flags"] == [f"{key}_INCONSISTENT_WITH_STATES"], key
        m["header"][key] -= delta * 0.55                 # residual 0.45*delta: inside the tolerance (1 m / 0.1 m/s)
        assert deep_consistency(m)["flags"] == [], key


def test_rtn_axes_are_orthonormal_and_right_handed():
    R, T, N = rtn_axes([7000.0, 100.0, -50.0], [0.1, 7.5, 1.2])
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    assert abs(dot(R, R) - 1) < 1e-15 and abs(dot(T, T) - 1) < 1e-15 and abs(dot(N, N) - 1) < 1e-15
    assert abs(dot(R, T)) < 1e-15 and abs(dot(R, N)) < 1e-15 and abs(dot(T, N)) < 1e-15
    cross = [R[1] * T[2] - R[2] * T[1], R[2] * T[0] - R[0] * T[2], R[0] * T[1] - R[1] * T[0]]
    assert all(abs(a - b) < 1e-15 for a, b in zip(cross, N))
    assert R[0] > 0.99 and T[1] > 0.98                     # R along r, T roughly along v


def test_min_eigenvalue_known_matrices():
    assert abs(min_eigenvalue([[2.0, 1.0], [1.0, 2.0]]) - 1.0) < 1e-12
    assert abs(min_eigenvalue([[1.0, 2.0], [2.0, 1.0]]) + 1.0) < 1e-12
    m = [[4.0, 1.0, 0.5], [1.0, 3.0, 0.2], [0.5, 0.2, -0.7]]
    lam = min_eigenvalue(m)
    det = lambda a: (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
                     + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    shifted = [[m[i][j] - (lam if i == j else 0.0) for j in range(3)] for i in range(3)]
    assert lam < -0.7 and abs(det(shifted)) < 1e-9
    assert min_eigenvalue([[5.0, 0.0], [0.0, 3.0]]) == 3.0


def test_non_psd_covariance_is_flagged_for_the_right_object():
    m = load("example_1.kvn")
    m["object2"]["CT_R"] = 10.0 * (m["object2"]["CR_R"] * m["object2"]["CT_T"]) ** 0.5   # |rho| = 10: impossible
    flags = deep_consistency(m)["flags"]
    assert "OBJECT2_COVARIANCE_NOT_POSITIVE_SEMIDEFINITE" in flags
