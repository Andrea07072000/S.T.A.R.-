"""star_epoch against published epochs and arithmetic that can be done by hand.
Verifies: R1, R2, R3 (README).

Published (Lieske 1979; Meeus, Astronomical Algorithms, ch. 21): J2000.0 = JD 2451545.0, J1950.0 = JD 2433282.5,
J1900.0 = JD 2415020.0, B1900.0 = JD 2415020.31352, B1950.0 = JD 2433282.4235, and the Besselian epoch of J2000.0 is
B2000.0012775. The comparison with ERFA, skyfield and SPICE is in crosscheck_epoch.py."""
import random

import pytest

import star_epoch as ep


def total(parts):
    return parts[0] + parts[1]


@pytest.mark.parametrize("epoch, jd", [(2000.0, 2451545.0), (1950.0, 2433282.5), (1900.0, 2415020.0), (2100.0, 2488070.0), (2000.5, 2451727.625)])
def test_published_julian_epochs(epoch, jd):
    assert total(ep.jd_from_julian_epoch(epoch)) == jd
    assert ep.julian_epoch(jd) == epoch and ep.julian_epoch(jd - 0.5, 0.5) == epoch


def test_published_besselian_epochs():
    assert total(ep.jd_from_besselian_epoch(1900.0)) == pytest.approx(2415020.31352, abs=1e-9)
    assert abs(total(ep.jd_from_besselian_epoch(1950.0)) - 2433282.4235) < 5e-5                   # printed to 4 decimals
    assert ep.besselian_epoch(2415020.0, 0.31352) == pytest.approx(1900.0, abs=1e-12)
    assert abs(ep.besselian_epoch(2451545.0) - 2000.0012775) < 5e-8                                # J2000.0 = B2000.0012775
    assert ep.besselian_epoch(2433282.0, 0.42345905) == pytest.approx(1950.0, abs=1e-10)


def test_year_lengths_by_hand():
    assert ep.julian_epoch(2451545.0 + 365.25) == 2001.0 and ep.julian_epoch(2451545.0 - 36525.0) == 1900.0
    assert ep.julian_epoch(2451545.0, 0.25) - ep.julian_epoch(2451545.0) == pytest.approx(0.25 / 365.25, abs=1e-13)
    a, b = ep.besselian_epoch(2451545.0), ep.besselian_epoch(2451545.0 + 365.0, 0.242198781)
    assert b - a == pytest.approx(1.0, abs=1e-12)                                                  # one tropical year of Lieske
    assert total(ep.jd_from_besselian_epoch(1951.0)) - total(ep.jd_from_besselian_epoch(1950.0)) == pytest.approx(365.242198781, abs=1e-8)
    assert total(ep.jd_from_julian_epoch(1951.0)) - total(ep.jd_from_julian_epoch(1950.0)) == 365.25
    assert ep.besselian_epoch(2451545.0) - ep.julian_epoch(2451545.0) == pytest.approx(0.0012775136652, abs=1e-12)   # the two differ by 11 hours in 2000


def test_the_two_parts_of_a_date():
    for f in (ep.jd_from_julian_epoch, ep.jd_from_besselian_epoch):
        for epoch in (1000.0, 1234.5678, 1899.9999999, 1950.0, 2000.0, 2026.76, 3000.0):
            day, frac = f(epoch)
            assert day % 1.0 == 0.5 and 0.0 <= frac < 1.0 and type(day) is float and type(frac) is float
    assert ep.jd_from_julian_epoch(2000.0) == (2451544.5, 0.5)
    assert ep.jd_from_julian_epoch(1950.0) == (2433282.5, 0.0)
    day, frac = ep.jd_from_besselian_epoch(1950.0)
    assert day == 2433281.5 and frac == pytest.approx(0.92345905, abs=1e-9)
    assert ep.julian_epoch(2451545.0, 0.5) == ep.julian_epoch(2451545.5) and ep.julian_epoch(2451545.0, -0.5) == ep.julian_epoch(2451544.5)
    assert ep.besselian_epoch(2451545.0, 0.5) == pytest.approx(ep.besselian_epoch(2451545.5), abs=1e-12)


def test_round_trips():
    rnd = random.Random(21)
    for _ in range(400):
        epoch = rnd.uniform(1000.0, 3000.0)
        assert ep.julian_epoch(*ep.jd_from_julian_epoch(epoch)) == pytest.approx(epoch, abs=5e-13)
        assert ep.besselian_epoch(*ep.jd_from_besselian_epoch(epoch)) == pytest.approx(epoch, abs=5e-13)
        day, frac = float(rnd.randint(2086303, 2816786)) + 0.5, rnd.random()
        for fwd, back in ((ep.julian_epoch, ep.jd_from_julian_epoch), (ep.besselian_epoch, ep.jd_from_besselian_epoch)):
            d2, f2 = back(fwd(day, frac))
            assert abs((d2 - day) + (f2 - frac)) < 2e-10                                           # 17 microseconds: one float holds the epoch
