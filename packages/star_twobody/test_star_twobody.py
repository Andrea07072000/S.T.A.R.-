"""star_twobody against published values and hand-derivable identities/invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_twobody as st


def test_published_geostationary_values_and_mu_constant():
    assert st.MU_EARTH == 398600.4418
    a_geo = 42164.17
    t_sid = 86164.0905
    assert abs(st.period(a_geo) - t_sid) <= 0.01
    assert abs(st.semi_major_axis_from_period(t_sid) - a_geo) <= 0.01
    # published relation for GEO mean motion: n = 2*pi / sidereal day
    assert abs(st.mean_motion(a_geo) - (2.0 * math.pi / t_sid)) <= 5e-12


def test_kepler_scalings_inverse_and_n_times_t():
    # T = 2*pi*sqrt(a^3/mu); with mu=4*pi^2 and a=1 => T=1 exactly.
    mu = 4.0 * math.pi**2
    assert st.period(1.0, mu) == pytest.approx(1.0, abs=1e-15)

    a = 7.0
    # T scales as a^(3/2): period(4a)=8*period(a)
    assert st.period(4.0 * a, mu) == pytest.approx(8.0 * st.period(a, mu), rel=1e-14)
    # T scales as mu^(-1/2): doubling mu halves sqrt factor by sqrt(2)
    assert st.period(a, 2.0 * mu) == pytest.approx(st.period(a, mu) / math.sqrt(2.0), rel=1e-14)

    n = st.mean_motion(a, mu)
    t = st.period(a, mu)
    assert n * t == pytest.approx(2.0 * math.pi, rel=1e-15)

    t2 = st.period(12345.6789, st.MU_EARTH)
    assert st.semi_major_axis_from_period(t2, st.MU_EARTH) == pytest.approx(12345.6789, rel=1e-14)


def test_speeds_energy_apsides_and_conservation():
    assert st.circular_speed(4.0, 1.0) == pytest.approx(0.5, abs=1e-15)
    assert st.escape_speed(4.0, 1.0) == pytest.approx(0.7071067811865476, abs=1e-16)
    assert st.escape_speed(4.0, 1.0) == pytest.approx(math.sqrt(2.0) * st.circular_speed(4.0, 1.0), rel=4e-16)

    assert st.escape_speed(6378.137) == pytest.approx(11.179875, abs=1e-6)

    rp, ra = st.apsides(10000.0, 0.2)
    assert (rp, ra) == pytest.approx((8000.0, 12000.0), abs=0.0)
    assert st.apsides(10000.0, 0.0) == pytest.approx((10000.0, 10000.0), abs=0.0)

    a, e = st.elements_from_apsides(8000.0, 12000.0)
    assert a == pytest.approx(10000.0, abs=1e-15)
    assert e == pytest.approx(0.2, abs=1e-15)
    rr = 4321.0
    assert st.elements_from_apsides(rr, rr) == pytest.approx((rr, 0.0), abs=0.0)

    vp, va = st.apsis_speeds(10000.0, 0.2)
    assert vp == pytest.approx(7.732404, abs=1e-6)
    assert va == pytest.approx(5.154936, abs=1e-6)

    vp0, va0 = st.apsis_speeds(12000.0, 0.0)
    vc = st.circular_speed(12000.0)
    assert vp0 == pytest.approx(vc, rel=1e-15)
    assert va0 == pytest.approx(vc, rel=1e-15)

    rp, ra = st.apsides(10000.0, 0.2)
    vp, va = st.apsis_speeds(10000.0, 0.2)
    assert rp * vp == pytest.approx(ra * va, rel=1e-14)
    ep = vp * vp / 2.0 - st.MU_EARTH / rp
    ea = va * va / 2.0 - st.MU_EARTH / ra
    es = st.specific_energy(10000.0)
    assert ep == pytest.approx(es, rel=1e-12)
    assert ea == pytest.approx(es, rel=1e-12)

    assert st.specific_energy(10000.0) == pytest.approx(-19.93002209, abs=1e-8)
    assert st.specific_energy(10000.0) < 0.0
    r = 7000.0
    vesc = st.escape_speed(r)
    assert (vesc * vesc / 2.0 - st.MU_EARTH / r) == pytest.approx(0.0, abs=1e-12 * st.MU_EARTH / r)


def test_defaults_use_mu_earth_and_other_mu_changes_result():
    a = 9000.0
    r = 8000.0
    t = 5000.0
    e = 0.3

    assert st.period(a) == st.period(a, st.MU_EARTH)
    assert st.semi_major_axis_from_period(t) == st.semi_major_axis_from_period(t, st.MU_EARTH)
    assert st.mean_motion(a) == st.mean_motion(a, st.MU_EARTH)
    assert st.circular_speed(r) == st.circular_speed(r, st.MU_EARTH)
    assert st.escape_speed(r) == st.escape_speed(r, st.MU_EARTH)
    assert st.apsis_speeds(a, e) == st.apsis_speeds(a, e, st.MU_EARTH)
    assert st.specific_energy(a) == st.specific_energy(a, st.MU_EARTH)

    mu2 = st.MU_EARTH * 1.1
    assert st.period(a, mu2) != st.period(a)
    assert st.semi_major_axis_from_period(t, mu2) != st.semi_major_axis_from_period(t)
    assert st.mean_motion(a, mu2) != st.mean_motion(a)
    assert st.circular_speed(r, mu2) != st.circular_speed(r)
    assert st.escape_speed(r, mu2) != st.escape_speed(r)
    assert st.apsis_speeds(a, e, mu2) != st.apsis_speeds(a, e)
    assert st.specific_energy(a, mu2) != st.specific_energy(a)
