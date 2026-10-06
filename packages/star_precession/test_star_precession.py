"""star_precession against the SOFA validation values and the classical precession constants.
Verifies: R1, R2, R3 (README).

Published: SOFA validation of pmat76 at (2400000.5, 50123.9999): first row 0.9999995504328350733,
0.8696632209480960785e-3, 0.3779153474959888345e-3; element [2][2] 0.9999999285899790119. Lieske (1979) / IAU 1976:
zeta = 2306.2181 T + 0.30188 T^2 + 0.017998 T^3, z = 2306.2181 T + 1.09468 T^2 + 0.018203 T^3,
theta = 2004.3109 T - 0.42665 T^2 - 0.041833 T^3 (arcseconds), i.e. the classical annual precession at J2000 of
46.124 arcsec in right ascension (m) and 20.043 arcsec in declination (n).
The comparison with ERFA and PyEphem is in crosscheck_precession.py."""
import math
import random

import pytest

import star_precession as p

SOFA = (2400000.5, 50123.9999)


def test_sofa_validation_values():
    m = p.precession_matrix(*SOFA)
    assert m[0][0] == pytest.approx(0.9999995504328350733, abs=1e-15) and m[0][1] == pytest.approx(0.8696632209480960785e-3, abs=1e-15)
    assert m[0][2] == pytest.approx(0.3779153474959888345e-3, abs=1e-15) and m[2][2] == pytest.approx(0.9999999285899790119, abs=1e-15)
    assert m[1][0] == pytest.approx(-m[0][1], abs=2e-10) and m[2][0] == pytest.approx(-m[0][2], abs=2e-10)      # nearly antisymmetric: a small rotation


def test_constants_and_angles():
    assert p.ZETA == (2306.2181, 0.30188, 0.017998) and p.Z == (2306.2181, 1.09468, 0.018203) and p.THETA == (2004.3109, -0.42665, -0.041833)
    assert p.precession_angles_arcsec(p.J2000) == (0.0, 0.0, 0.0)
    zeta, z, theta = p.precession_angles_arcsec(p.J2000 + 36525.0)                           # one century
    assert zeta == pytest.approx(2306.2181 + 0.30188 + 0.017998, abs=1e-9) and z == pytest.approx(2306.2181 + 1.09468 + 0.018203, abs=1e-9)
    assert theta == pytest.approx(2004.3109 - 0.42665 - 0.041833, abs=1e-9)
    assert p.precession_angles_arcsec(p.J2000 - 36525.0)[2] == pytest.approx(-2004.3109 - 0.42665 + 0.041833, abs=1e-9)


def test_identity_at_j2000_and_classical_annual_precession():
    assert p.precession_matrix(p.J2000) == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    x, y, z = p.mod_from_j2000((1.0, 0.0, 0.0), p.J2000 + 365.25)                            # the equinox direction, one year later
    assert math.degrees(math.atan2(y, x)) * 3600 == pytest.approx(46.124, abs=2e-3)          # m: its right ascension grows by 46.124 arcsec
    assert math.degrees(math.asin(z)) * 3600 == pytest.approx(20.043, abs=2e-3)              # n: its declination grows by 20.043 arcsec
    px, py, pz = p.mod_from_j2000((0.0, 0.0, 1.0), p.J2000 + 36525.0)                        # the J2000 pole seen from the pole of 2100
    assert math.degrees(math.acos(pz)) * 3600 == pytest.approx(2004.3109 - 0.42665 - 0.041833, abs=1e-6)


def test_every_matrix_is_a_rotation_and_the_two_directions_are_inverse():
    rnd = random.Random(8)
    for _ in range(200):
        jd = rnd.uniform(p.JD_MIN, p.JD_MAX)
        m = p.precession_matrix(jd)
        for i in range(3):
            for j in range(3):
                assert sum(m[k][i] * m[k][j] for k in range(3)) == pytest.approx(1.0 if i == j else 0.0, abs=1e-15)
        det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
               + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
        assert det == pytest.approx(1.0, abs=1e-15)
        v = [rnd.uniform(-4e5, 4e5) for _ in range(3)]
        w = p.mod_from_j2000(v, jd)
        assert w == pytest.approx(tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3)), rel=1e-15)
        assert math.hypot(*w) == pytest.approx(math.hypot(*v), rel=1e-14) and p.j2000_from_mod(w, jd) == pytest.approx(v, rel=1e-12, abs=1e-9)


def test_day_and_fraction_any_split():
    a = p.precession_matrix(2460000.5, 0.25)
    b = p.precession_matrix(2460000.75)
    assert all(abs(a[i][j] - b[i][j]) < 1e-15 for i in range(3) for j in range(3)) and p.precession_matrix(2460000.75, 0.0) == b
    assert p.mod_from_j2000((1, 2, 3), 2460000.5, 0.25) == pytest.approx(p.mod_from_j2000((1, 2, 3), 2460000.75), abs=1e-12)
    assert p.j2000_from_mod((1, 2, 3), 2460000.5, 0.25) == pytest.approx(p.j2000_from_mod((1, 2, 3), 2460000.75), abs=1e-12)
