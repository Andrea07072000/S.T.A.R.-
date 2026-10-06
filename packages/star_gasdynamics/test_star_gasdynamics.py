"""star_gasdynamics against NACA Report 1135, hand-derived values and conservation laws.

Published: NACA Report 1135 (1953), gamma = 1.4 tables. Their four-significant-figure
entries are compared at the stipulated relative tolerance of 5e-4. All other numerical
expectations below follow from the equations shown in the accompanying comments.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release. One of its tests exposed an underflow of p02/p01 for gamma near 1, fixed in the module."""
import math

import pytest

import star_gasdynamics as sg


@pytest.mark.parametrize(
    "mach, expected",
    [
        (0.5, (0.9524, 0.8430, 0.8852, 1.340)),
        (2.0, (0.5556, 0.1278, 0.2300, 1.688)),
        (3.0, (0.3571, 0.02722, 0.07623, 4.235)),
        (5.0, (0.1667, 0.001890, 0.01134, 25.00)),
    ],
)
def test_naca_isentropic_table(mach, expected):
    for actual, published in zip(sg.isentropic(mach), expected):
        assert actual == pytest.approx(published, rel=5e-4, abs=0)


@pytest.mark.parametrize(
    "mach, expected",
    [
        (2.0, (0.5774, 4.500, 2.667, 1.687, 0.7209)),
        (3.0, (0.4752, 10.33, 3.857, 2.679, 0.3283)),
        (5.0, (0.4152, 29.00, 5.000, 5.800, 0.06172)),
    ],
)
def test_naca_normal_shock_table(mach, expected):
    for actual, published in zip(sg.normal_shock(mach), expected):
        assert actual == pytest.approx(published, rel=5e-4, abs=0)


def test_isentropic_values_derived_for_gamma_seven_fifths():
    # g = 7/5 gives t = 1/(1 + M²/5), p = t^(7/2), rho = t^(5/2),
    # and A/A* = ((5 + M²)/6)^3/M.
    for mach, temperature, area in (
        (1.0, 5 / 6, 1.0),
        (2.0, 5 / 9, 27 / 16),
        (3.0, 5 / 14, 343 / 81),
        (5.0, 1 / 6, 25.0),
    ):
        assert sg.isentropic(mach) == pytest.approx(
            (temperature, temperature ** (7 / 2),
             temperature ** (5 / 2), area),
            rel=1e-13, abs=1e-14,
        )
    # At zero speed all static/stagnation ratios are one; area diverges.
    assert sg.isentropic(0.0) == (1.0, 1.0, 1.0, math.inf)


def test_shock_values_derived_for_gamma_seven_fifths():
    # p = (7M²-1)/6, rho = 6M²/(M²+5), M2² = (M²+5)/(7M²-1).
    # T = p/rho and p02/p01 = rho^(7/2) / p^(5/2).
    for mach, pressure, density in (
        (2.0, 9 / 2, 8 / 3),
        (3.0, 31 / 3, 27 / 7),
        (5.0, 29.0, 5.0),
    ):
        downstream = math.sqrt((mach * mach + 5) / (7 * mach * mach - 1))
        expected = (
            downstream, pressure, density, pressure / density,
            density ** (7 / 2) / pressure ** (5 / 2),
        )
        assert sg.normal_shock(mach) == pytest.approx(
            expected, rel=1e-13, abs=1e-14
        )
    assert sg.normal_shock(1.0) == pytest.approx(
        (1.0,) * 5, rel=0, abs=1e-15
    )
    # At M=2, M2²=1/3 and T2/T1=(9/2)/(8/3)=27/16.
    assert sg.normal_shock(2.0)[0] == pytest.approx(
        1 / math.sqrt(3), rel=1e-14
    )
    assert sg.normal_shock(2.0)[3] == pytest.approx(27 / 16, rel=1e-14)


def test_different_gamma_exposes_each_exponent_and_coefficient():
    # At g=3, M=2: t=1/(1+M²)=1/5, p=t^(3/2),
    # rho=t^(1/2), and A=((1+M²)/2)/M=5/4.
    t = 1 / 5
    assert sg.isentropic(2.0, 3.0) == pytest.approx(
        (t, t ** (3 / 2), math.sqrt(t), 5 / 4),
        rel=1e-13, abs=1e-14,
    )
    # At g=2, M=2: p=1+(4/3)(4-1)=5, rho=3*4/(4+2)=2,
    # M2²=(4+2)/(4*4-1)=2/5, T=5/2, p02/p01=rho²/p=4/5.
    assert sg.normal_shock(2.0, 2.0) == pytest.approx(
        (math.sqrt(2 / 5), 5.0, 2.0, 5 / 2, 4 / 5),
        rel=1e-13, abs=1e-14,
    )
    # For g=2, t=1/(1+M²/2) and the area exponent is 3/2:
    # at M=2, A=(2)^(3/2)/2=sqrt(2).
    assert sg.isentropic(2.0, 2.0) == pytest.approx(
        (1 / 3, 1 / 9, 1 / 3, math.sqrt(2)),
        rel=1e-13, abs=1e-14,
    )


@pytest.mark.parametrize("gamma", [1.01, 1.4, 2.0, 3.0])
def test_isentropic_thermodynamics_monotonicity_and_throat(gamma):
    machs = (0.0, 0.2, 0.75, 0.999, 1.0, 1.001, 2.0, 10.0, 50.0)
    values = [sg.isentropic(m, gamma) for m in machs]
    for t, p, rho, area in values:
        assert rho == pytest.approx(p / t, rel=1e-13, abs=0)
        assert p == pytest.approx(rho ** gamma, rel=1e-13, abs=0)
        assert t > 0 and p > 0 and rho > 0
        assert area >= 1.0
    for before, after in zip(values, values[1:]):
        assert all(before[i] > after[i] for i in range(3))
    assert values[4][3] == pytest.approx(1.0, rel=0, abs=1e-14)
    assert values[3][3] > values[4][3] < values[5][3]
    assert values[0][3] > values[1][3] > values[2][3] > values[3][3]
    assert values[5][3] < values[6][3] < values[7][3] < values[8][3]


@pytest.mark.parametrize("gamma", [1.01, 1.4, 2.0, 3.0])
@pytest.mark.parametrize("mach", [1.0, 1.01, 1.5, 2.0, 5.0, 50.0])
def test_shock_conserves_mass_momentum_energy_and_loses_stagnation_pressure(
    gamma, mach
):
    downstream, pressure, density, temperature, stagnation = sg.normal_shock(
        mach, gamma
    )
    # u is proportional to M*sqrt(T). Divide the momentum and total-energy
    # equations through by upstream pressure and upstream temperature.
    assert mach == pytest.approx(
        density * downstream * math.sqrt(temperature), rel=2e-12, abs=0
    )
    assert 1 + gamma * mach * mach == pytest.approx(
        pressure * (1 + gamma * downstream * downstream),
        rel=2e-12, abs=0,
    )
    assert 1 + (gamma - 1) * mach * mach / 2 == pytest.approx(
        temperature * (1 + (gamma - 1) * downstream * downstream / 2),
        rel=2e-12, abs=0,
    )
    upstream_p_over_p0 = sg.isentropic(mach, gamma)[1]
    downstream_p_over_p0 = sg.isentropic(downstream, gamma)[1]
    assert stagnation == pytest.approx(
        pressure * upstream_p_over_p0 / downstream_p_over_p0,
        rel=1e-12, abs=0,
    )
    assert 0 < stagnation <= 1.0
    if mach == 1.0:
        assert downstream == pytest.approx(1.0, rel=0, abs=1e-14)
        assert stagnation == pytest.approx(1.0, rel=0, abs=1e-14)
    else:
        assert downstream < 1.0 < mach
        assert stagnation < 1.0
        assert pressure > 1.0 and density > 1.0 and temperature > 1.0


def test_strong_shock_approaches_hand_derived_limits():
    # As M grows, rho tends to (g+1)/(g-1)=6 and M2 tends
    # to sqrt((g-1)/(2g))=1/sqrt(7), for g=7/5.
    downstream, _, density, _, _ = sg.normal_shock(50.0)
    assert density == pytest.approx(6.0 / (1.0 + 5.0 / 2500.0), rel=1e-13)       # 6 M^2 / (M^2 + 5) at Mach 50: 1.2e-2 short of the limit 6
    assert 5.98 < density < 6.0
    assert downstream == pytest.approx(1 / math.sqrt(7), abs=1e-3)


@pytest.mark.parametrize("gamma", [1.01, 1.4, 2.0, 3.0])
@pytest.mark.parametrize("mach", [1.001, 1.01, 1.2, 2.0, 5.0, 50.0])
def test_inverse_supersonic_branch(gamma, mach):
    area = sg.isentropic(mach, gamma)[3]
    assert sg.mach_from_area_ratio(area, gamma, True) == pytest.approx(
        mach, rel=0, abs=1e-6 if mach == 1.001 else 2e-11
    )


@pytest.mark.parametrize("gamma", [1.01, 1.4, 2.0, 3.0])
@pytest.mark.parametrize("mach", [1e-6, 0.001, 0.2, 0.5, 0.999])
def test_inverse_subsonic_branch(gamma, mach):
    area = sg.isentropic(mach, gamma)[3]
    assert sg.mach_from_area_ratio(area, gamma, False) == pytest.approx(
        mach, rel=1e-9 if mach != 0.999 else 0,
        abs=1e-6 if mach == 0.999 else 0,
    )


def test_both_inverse_branches_and_exact_throat():
    # At g=7/5, A(2)=((5+4)/6)^3/2=27/16.
    # Substitution in ((5+M²)/6)^3/M bounds its other root between
    # 0.37 and 0.38; monotonicity makes it distinct from M=2.
    assert sg.mach_from_area_ratio(27 / 16, 1.4, True) == pytest.approx(
        2.0, rel=0, abs=2e-12
    )
    subsonic = sg.mach_from_area_ratio(27 / 16, 1.4, False)
    assert 0.37 < subsonic < 0.38
    assert sg.isentropic(subsonic)[3] == pytest.approx(
        27 / 16, rel=1e-12
    )
    for gamma in (1.01, 1.4, 3.0):
        assert sg.mach_from_area_ratio(1.0, gamma, True) == 1.0
        assert sg.mach_from_area_ratio(1.0, gamma, False) == 1.0


def test_documented_default_gamma():
    assert sg.isentropic(2.0) == sg.isentropic(2.0, 1.4)
    assert sg.normal_shock(2.0) == sg.normal_shock(2.0, 1.4)
    assert sg.mach_from_area_ratio(27 / 16) == sg.mach_from_area_ratio(
        27 / 16, 1.4, True
    )
