"""star_j2 against textbook figures, exact identities of the formulas and a numerical integration.
Verifies: R1, R2, R3 (README).

Published / textbook: the critical inclination 63.4349 deg (and 116.5651 deg), where 5 cos^2 i = 1; the node of the
International Space Station regresses by about 5 deg/day; a sun-synchronous orbit at 800 km altitude needs about
98.6 deg and at 500 km about 97.4 deg; the Sun moves 360 deg in a tropical year of 365.2421897 days (0.985647 deg/day).
Independent method: the equations of motion with the J2 acceleration are integrated here with a fixed-step RK4 (no
secular formula) and the node drift is read from the angular momentum vector.
The comparison with Orekit's Eckstein-Hechler theory and SciPy DOP853 on 51 orbits is in crosscheck_j2.py."""
import math

import pytest

import star_j2 as j

ISS = (6778.137, 0.0, 51.6)


def test_textbook_figures():
    assert abs(j.CRITICAL_INCLINATION_DEG - 63.4349) < 5e-5 and abs(180 - j.CRITICAL_INCLINATION_DEG - 116.5651) < 5e-5
    assert abs(j.raan_rate_deg_day(*ISS) + 5.0) < 0.05
    assert abs(j.sun_synchronous_inclination_deg(6378.137 + 800) - 98.6) < 0.05
    assert abs(j.sun_synchronous_inclination_deg(6378.137 + 500) - 97.4) < 0.05
    assert abs(j.SUN_RATE_DEG_DAY - 0.985647) < 5e-7 and j.TROPICAL_YEAR_DAYS == 365.2421897


def test_perigee_does_not_rotate_at_the_critical_inclination_and_changes_sign_across_it():
    for a, e in ((26554.0, 0.72), (8000.0, 0.1), (7000.0, 0.0)):
        assert abs(j.argp_rate_deg_day(a, e, j.CRITICAL_INCLINATION_DEG)) < 1e-12
        assert abs(j.argp_rate_deg_day(a, e, 180 - j.CRITICAL_INCLINATION_DEG)) < 1e-12
        assert j.argp_rate_deg_day(a, e, 63.0) > 0 > j.argp_rate_deg_day(a, e, 64.0)
        assert j.argp_rate_deg_day(a, e, 0.0) > 0 and j.argp_rate_deg_day(a, e, 90.0) < 0
    # equatorial orbit: perigee advances twice as fast as the node regresses (4 : -2 in units of 0.75 k n)
    assert j.argp_rate_deg_day(8000.0, 0.1, 0.0) == pytest.approx(-2 * j.raan_rate_deg_day(8000.0, 0.1, 0.0), rel=1e-14)


def test_node_rate_signs_symmetry_and_polar_orbit():
    assert j.raan_rate_deg_day(7000, 0, 30) < 0 < j.raan_rate_deg_day(7000, 0, 150)          # prograde regresses, retrograde advances
    assert j.raan_rate_deg_day(7000, 0, 30) == pytest.approx(-j.raan_rate_deg_day(7000, 0, 150), rel=1e-14)
    assert abs(j.raan_rate_deg_day(7000, 0.01, 90.0)) < 1e-14
    assert j.raan_rate_deg_day(7000, 0, 0) == pytest.approx(-1.5 * j.J2 * (j.RE / 7000) ** 2 * math.degrees(math.sqrt(j.MU / 7000 ** 3)) * 86400, rel=1e-14)


def test_scaling_laws_of_the_formulas():
    base = j.raan_rate_deg_day(7000, 0.0, 40)
    assert j.raan_rate_deg_day(14000, 0.0, 40) == pytest.approx(base / 2 ** 3.5, rel=1e-13)       # a^-3.5
    assert j.raan_rate_deg_day(7000, 0.0, 40, j2=2 * j.J2) == pytest.approx(2 * base, rel=1e-13)
    assert j.raan_rate_deg_day(7000, 0.0, 40, re=2 * j.RE / 2) == base
    assert j.raan_rate_deg_day(7000, 0.0, 40, mu=4 * j.MU) == pytest.approx(2 * base, rel=1e-13)  # sqrt(mu)
    assert j.raan_rate_deg_day(20000, 0.5, 40) == pytest.approx(j.raan_rate_deg_day(20000, 0.0, 40) / (1 - 0.25) ** 2, rel=1e-13)
    assert j.argp_rate_deg_day(20000, 0.5, 40) == pytest.approx(j.argp_rate_deg_day(20000, 0.0, 40) / 0.75 ** 2, rel=1e-13)


def test_sun_synchronous_inclination_gives_the_sun_rate_and_grows_with_altitude():
    previous = 90.0
    for alt in (200, 400, 600, 800, 1000, 1500, 3000, 5000):
        a = j.RE + alt
        inc = j.sun_synchronous_inclination_deg(a)
        assert j.raan_rate_deg_day(a, 0.0, inc) == pytest.approx(j.SUN_RATE_DEG_DAY, rel=1e-12) and inc > previous
        previous = inc
    inc = j.sun_synchronous_inclination_deg(9000.0, 0.2)
    assert j.raan_rate_deg_day(9000.0, 0.2, inc) == pytest.approx(j.SUN_RATE_DEG_DAY, rel=1e-12)
    assert j.sun_synchronous_inclination_deg(7178.137) == j.sun_synchronous_inclination_deg(7178.137, 0.0)
    assert j.sun_synchronous_inclination_deg(12350.0) > 175 and j.sun_synchronous_inclination_deg(7178.137, j2=2 * j.J2) < 95


def test_mean_anomaly_rate_and_nodal_period():
    n = math.degrees(math.sqrt(j.MU / 7178.137 ** 3)) * 86400
    magic = math.degrees(math.acos(math.sqrt(1 / 3)))                    # 3 cos^2 i = 1: J2 does not change the mean motion
    assert j.mean_anomaly_rate_deg_day(7178.137, 0.0, magic) == pytest.approx(n, rel=1e-14)
    assert j.mean_anomaly_rate_deg_day(7178.137, 0.0, 0.0) > n > j.mean_anomaly_rate_deg_day(7178.137, 0.0, 90.0)
    k = j.J2 * (j.RE / 7178.137) ** 2
    assert j.mean_anomaly_rate_deg_day(7178.137, 0.0, 0.0) == pytest.approx(n * (1 + 1.5 * k), rel=1e-14)
    assert j.mean_anomaly_rate_deg_day(12000, 0.6 - 0.3, 0.0) == pytest.approx(
        math.degrees(math.sqrt(j.MU / 12000 ** 3)) * 86400 * (1 + 0.75 * j.J2 * (j.RE / (12000 * 0.91)) ** 2 * math.sqrt(0.91) * 2), rel=1e-13)
    kepler = 2 * math.pi * math.sqrt(7178.137 ** 3 / j.MU)
    t = j.nodal_period_s(7178.137, 0.0, 98.6)
    assert t == pytest.approx(360.0 / (j.mean_anomaly_rate_deg_day(7178.137, 0, 98.6) + j.argp_rate_deg_day(7178.137, 0, 98.6)) * 86400, rel=1e-14)
    assert 0 < t - kepler < 10 and j.nodal_period_s(7178.137, 0.0, 0.0) < kepler    # polar: longer; equatorial: shorter


def _node_drift_rk4(a, inc_deg, days, step=20.0):
    """RAAN drift (deg/day) of a circular orbit from a fixed-step RK4 integration of the J2 equations of motion."""
    mu, re, j2 = j.MU, j.RE, j.J2
    i = math.radians(inc_deg)
    v = math.sqrt(mu / a)
    y = [a, 0.0, 0.0, 0.0, v * math.cos(i), v * math.sin(i)]

    def f(s):
        x, yy, z = s[0], s[1], s[2]
        r2 = x * x + yy * yy + z * z
        r = math.sqrt(r2)
        k = 1.5 * j2 * mu * re * re / r2 ** 2.5
        q = 5 * z * z / r2
        return [s[3], s[4], s[5], -mu * x / r ** 3 + k * x * (q - 1), -mu * yy / r ** 3 + k * yy * (q - 1), -mu * z / r ** 3 + k * z * (q - 3)]

    def raan(s):
        hx, hy = s[1] * s[5] - s[2] * s[4], s[2] * s[3] - s[0] * s[5]
        return math.atan2(hx, -hy)

    start, total, prev = raan(y), 0.0, raan(y)
    for _ in range(int(days * 86400 / step)):
        k1 = f(y)
        k2 = f([a_ + 0.5 * step * b for a_, b in zip(y, k1)])
        k3 = f([a_ + 0.5 * step * b for a_, b in zip(y, k2)])
        k4 = f([a_ + step * b for a_, b in zip(y, k3)])
        y = [a_ + step / 6 * (b + 2 * c + 2 * d + e_) for a_, b, c, d, e_ in zip(y, k1, k2, k3, k4)]
        now = raan(y)
        total += (now - prev + math.pi) % (2 * math.pi) - math.pi
        prev = now
    assert start == 0.0
    return math.degrees(total) / days


@pytest.mark.parametrize("a, inc", [(6778.137, 51.6), (7178.137, 98.6), (8000.0, 20.0)])
def test_node_rate_agrees_with_a_numerical_integration_of_the_equations_of_motion(a, inc):
    # first-order formula against osculating motion over 3 days: the cross-check measures up to 0.029 deg/day
    assert _node_drift_rk4(a, inc, 3.0) == pytest.approx(j.raan_rate_deg_day(a, 0.0, inc), abs=0.03)
