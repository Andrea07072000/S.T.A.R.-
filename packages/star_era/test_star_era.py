"""star_era against the SOFA validation values and the definitions of the IERS Conventions.
Verifies: R1, R2, R3 (README).

Published: SOFA validation suite (t_sofa_c): era00(2400000.5, 54388.0) = 0.4022837240028158102 rad;
gmst06(2400000.5, 53736.0, 2400000.5, 53736.0) = 1.754174971870091203 rad. IERS Conventions (2010), eq. 5.15:
ERA = 2 pi (0.7790572732640 + 1.00273781191135448 Tu), Tu = UT1 days since J2000.0; eq. 5.32: GMST - ERA polynomial.
The comparison with ERFA and Skyfield on 1000 dates is in crosscheck_era.py."""
import math
from fractions import Fraction

import pytest

import star_era as s


def test_sofa_validation_values():
    assert math.radians(s.era_deg(2400000.5, 54388.0)) == pytest.approx(0.4022837240028158102, abs=1e-13)
    assert math.radians(s.gmst06_deg(2400000.5, 53736.0, 2400000.5, 53736.0)) == pytest.approx(1.754174971870091203, abs=1e-13)


def test_era_at_j2000_and_its_rate_from_the_definition():
    assert s.era_deg(2451545.0) == pytest.approx(360 * 0.7790572732640, abs=1e-12)                 # 280.4606 deg
    assert (s.ERA0, s.ERA_RATE, s.J2000) == (0.7790572732640, 0.00273781191135448, 2451545.0)
    one_day = (s.era_deg(2451546.0) - s.era_deg(2451545.0)) % 360
    assert one_day == pytest.approx(360 * 0.00273781191135448, abs=1e-11)                           # 0.9856 deg per UT1 day
    sidereal_day = 1 / 1.00273781191135448                                                         # one full turn of the Earth
    assert s.era_deg(2451545.0, sidereal_day) == pytest.approx(s.era_deg(2451545.0), abs=1e-10)
    assert abs(sidereal_day * 86400 - 86164.0989) < 1e-4                                            # the stellar day, in UT1 seconds


def test_exact_rational_evaluation_of_the_definition():
    for day, frac in ((2378496.5, 0.0), (2415020.5, 0.123456789), (2451545.0, 0.0), (2460000.5, 0.999999999), (2524593.0, 0.5)):
        t = Fraction(day) + Fraction(frac) - Fraction(2451545)
        turns = (Fraction("0.7790572732640") + Fraction("1.00273781191135448") * t) % 1
        assert s.era_deg(day, frac) == pytest.approx(float(turns * 360), abs=2e-11)


def test_any_split_of_the_date_gives_the_same_angle():
    base = s.era_deg(2460000.5, 0.25)
    for split in ((2460000.75, 0.0), (0.25, 2460000.5), (2460000.0, 0.75), (2400000.5, 60000.25), (2460001.5, -0.75)):
        assert s.era_deg(*split) == pytest.approx(base, abs=1e-9)
    assert s.era_deg(2460000.75) == s.era_deg(2460000.75, 0.0)
    g = s.gmst06_deg(2460000.5, 0.25, 2460000.5, 0.2508)
    assert s.gmst06_deg(2460000.75, 0.0, 2460000.0, 0.7508) == pytest.approx(g, abs=1e-9)


def test_a_nanosecond_of_ut1_is_visible_in_the_pair_form():
    a, b = s.era_deg(2460000.5, 0.5), s.era_deg(2460000.5, 0.5 + 1e-9 / 86400)
    assert (b - a) % 360 == pytest.approx(360 * 1.00273781191135448 * 1e-9 / 86400, rel=0.05)     # 1 ns = 1.5e-8 arcsec


def test_gmst_minus_era_is_the_iau_2006_polynomial():
    assert s.GMST_POLY == (0.014506, 4612.156534, 1.3915817, -0.00000044, -0.000029956, -0.0000000368)
    assert (s.gmst06_deg(2451545.0, 0.0, 2451545.0, 0.0) - s.era_deg(2451545.0)) * 3600 == pytest.approx(0.014506, abs=1e-7)
    for centuries in (-1.99, -1.0, 0.25, 1.0, 1.99):
        tt = 2451545.0 + 36525.0 * centuries
        expected = sum(c * centuries ** k for k, c in enumerate(s.GMST_POLY))
        got = ((s.gmst06_deg(tt, 0.0, tt, 0.0) - s.era_deg(tt, 0.0) + 180) % 360 - 180) * 3600
        assert got == pytest.approx(expected, abs=2e-6)
    # only TT enters the polynomial: one more day of TT at the same UT1 moves GMST by 4612.156534 / 36525 arcsec
    d = (s.gmst06_deg(2451545.0, 0.0, 2451546.0, 0.0) - s.gmst06_deg(2451545.0, 0.0, 2451545.0, 0.0)) * 3600
    assert d == pytest.approx(4612.156534 / 36525, rel=1e-5)


def test_angles_are_in_range_over_the_whole_span():
    for k in range(0, 1001):
        jd = s.JD_MIN + (s.JD_MAX - s.JD_MIN) * k / 1000
        assert 0.0 <= s.era_deg(jd) < 360.0 and 0.0 <= s.gmst06_deg(jd, 0.0, jd, 0.0) < 360.0
