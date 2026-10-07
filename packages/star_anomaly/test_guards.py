"""Guard tests of star_anomaly written by the reviewer: an independent oracle (Kepler's equation by plain bisection and
the textbook half-angle relations: none of the module's formulas), Vallado's examples, the nearly parabolic corner,
the revolutions, and every refusal by name."""
import math
import random

import pytest

import star_anomaly as sa

PI, TWO_PI = math.pi, 2 * math.pi
CLOSED = (sa.eccentric_from_mean, sa.mean_from_eccentric, sa.true_from_eccentric, sa.eccentric_from_true, sa.true_from_mean, sa.mean_from_true)
OPEN = (sa.hyperbolic_from_mean, sa.mean_from_hyperbolic, sa.true_from_hyperbolic, sa.hyperbolic_from_true)


def bisect(fun, low, high):
    for _ in range(200):
        mid = 0.5 * (low + high)
        if mid in (low, high):
            break
        if fun(mid) > 0:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


def test_published_examples_of_vallado():
    assert math.degrees(sa.eccentric_from_mean(math.radians(235.4), 0.4)) == pytest.approx(220.512074767522, abs=1e-11)
    assert sa.hyperbolic_from_mean(math.radians(235.4), 2.4) == pytest.approx(1.6013761449, abs=1e-10)


def test_keplers_equation_against_bisection():
    rnd = random.Random(42)
    for _ in range(400):
        e, m = rnd.uniform(0.0, 0.99), rnd.uniform(0.0, PI)
        expected = bisect(lambda x: x - e * math.sin(x) - m, 0.0, PI)
        assert sa.eccentric_from_mean(m, e) == pytest.approx(expected, abs=1e-13)
        assert sa.eccentric_from_mean(-m, e) == -sa.eccentric_from_mean(m, e)
        eh, mh = rnd.uniform(1.01, 8.0), rnd.uniform(0.0, 40.0)
        expected = bisect(lambda x: eh * math.sinh(x) - x - mh, 0.0, 20.0)
        assert sa.hyperbolic_from_mean(mh, eh) == pytest.approx(expected, rel=1e-13, abs=1e-13)
        assert sa.hyperbolic_from_mean(-mh, eh) == -sa.hyperbolic_from_mean(mh, eh)


def test_the_direct_equations_by_hand():
    assert sa.mean_from_eccentric(PI / 2, 0.5) == pytest.approx(PI / 2 - 0.5, abs=1e-15)
    assert sa.mean_from_eccentric(1.2, 0.3) == pytest.approx(1.2 - 0.3 * math.sin(1.2), abs=1e-15)
    assert sa.mean_from_eccentric(0.1, 0.9) == pytest.approx(0.1 - 0.9 * math.sin(0.1), rel=1e-13, abs=0)       # inside the series branch
    assert sa.mean_from_eccentric(3.0, 0.9) == pytest.approx(3.0 - 0.9 * math.sin(3.0), rel=1e-15, abs=0)
    assert sa.mean_from_eccentric(TWO_PI * 5 + 0.1, 0.9) == pytest.approx(TWO_PI * 5 + 0.1 - 0.9 * math.sin(0.1), abs=1e-13)      # the series branch on another revolution
    assert sa.mean_from_hyperbolic(1.0, 2.0) == pytest.approx(2 * math.sinh(1.0) - 1.0, rel=1e-15, abs=0)
    assert sa.mean_from_hyperbolic(0.1, 1.5) == pytest.approx(1.5 * math.sinh(0.1) - 0.1, rel=1e-13, abs=0)
    assert sa.mean_from_hyperbolic(-3.0, 1.5) == pytest.approx(-(1.5 * math.sinh(3.0) - 3.0), rel=1e-15, abs=0)
    # small arguments, where x - sin x and sinh x - x are x^3 / 6: (1 - e) E + e E^3 / 6
    assert sa.mean_from_eccentric(1e-3, 0.999) == pytest.approx(1e-3 * 1e-3 + 0.999 * (1e-9 / 6 - 1e-15 / 120), rel=1e-12, abs=0)
    assert sa.mean_from_hyperbolic(1e-3, 1.001) == pytest.approx(1e-3 * 1e-3 + 1.001 * (1e-9 / 6 + 1e-15 / 120), rel=1e-12, abs=0)
    assert sa.mean_from_eccentric(0.49999, 0.5) == pytest.approx(sa.mean_from_eccentric(0.50001, 0.5) - 2e-5 * (1 - 0.5 * math.cos(0.5)), abs=1e-9)   # the two branches meet


def test_true_anomaly_against_the_half_angle_relations():
    rnd = random.Random(7)
    for _ in range(400):
        e, ecc = rnd.uniform(0.0, 0.99), rnd.uniform(-3.0, 3.0)
        nu = sa.true_from_eccentric(ecc, e)
        assert math.tan(nu / 2) == pytest.approx(math.sqrt((1 + e) / (1 - e)) * math.tan(ecc / 2), rel=1e-12, abs=1e-15)
        assert sa.eccentric_from_true(nu, e) == pytest.approx(ecc, abs=1e-12)
        assert math.cos(nu) == pytest.approx((math.cos(ecc) - e) / (1 - e * math.cos(ecc)), abs=1e-13)             # the other textbook form
        eh, f = rnd.uniform(1.01, 8.0), rnd.uniform(-5.0, 5.0)
        nuh = sa.true_from_hyperbolic(f, eh)
        assert math.tan(nuh / 2) == pytest.approx(math.sqrt((eh + 1) / (eh - 1)) * math.tanh(f / 2), rel=1e-13, abs=1e-15)
        assert abs(nuh) < math.acos(-1 / eh) and sa.hyperbolic_from_true(nuh, eh) == pytest.approx(f, abs=1e-8)
        assert math.cos(nuh) == pytest.approx((eh - math.cosh(f)) / (eh * math.cosh(f) - 1), abs=1e-12)
    assert sa.true_from_eccentric(PI / 2, 0.5) == pytest.approx(2 * PI / 3, abs=1e-15)                              # cos(nu) = -e at E = 90 deg
    assert sa.true_from_eccentric(PI / 2, 0.3) == pytest.approx(PI / 2 + math.asin(0.3), abs=1e-15)
    assert sa.true_from_mean(1, 0.5) == pytest.approx(2.030806214849156, abs=1e-14) and sa.eccentric_from_mean(1, 0.5) == pytest.approx(1.4987011335178484, abs=1e-14)
    assert sa.mean_from_true(2.030806214849156, 0.5) == pytest.approx(1.0, abs=1e-14)
    assert sa.true_from_hyperbolic(30, 2.0) == pytest.approx(2 * PI / 3, abs=1e-12) and sa.true_from_hyperbolic(-30, 2.0) == pytest.approx(-2 * PI / 3, abs=1e-12)


def test_fixed_points_symmetry_and_circular_orbits_are_exact():
    for fun in CLOSED:
        assert fun(0.0, 0.7) == 0.0 and fun(0.7, 0.0) == 0.7 and fun(-2.5, 0.0) == -2.5 and fun(123.456, 0) == 123.456
        assert fun(PI, 0.7) == pytest.approx(PI, abs=5e-16) and fun(-PI, 0.7) == pytest.approx(-PI, abs=5e-16)
        for x in (1e-9, 0.83, 2.9, 17.0):
            assert fun(-x, 0.4) == -fun(x, 0.4) and isinstance(fun(x, 0.4), float)
    for fun in OPEN:
        assert fun(0.0, 2.0) == 0.0 and fun(-0.83, 2.0) == -fun(0.83, 2.0) and isinstance(fun(1, 2), float)
    for e in (0.1, 0.5, 0.9, 0.99):
        for m in (0.3, 1.0, 2.0, 3.0):
            ecc = sa.eccentric_from_mean(m, e)
            nu = sa.true_from_eccentric(ecc, e)
            assert m < ecc < nu < PI and ecc - m <= e                                                              # from perigee to apogee
            assert ecc - e * math.sin(ecc) - m == pytest.approx(0.0, abs=2e-15)                                     # a few units in the last place of E


def test_the_revolution_is_kept():
    for k in (7, -3, 1000, -100000):
        turn = TWO_PI * k
        for x, e in ((1.0, 0.6), (-2.5, 0.3), (3.0, 0.95), (0.5, 0.9)):         # not near the periapsis of a nearly parabolic orbit: there dE/dM is 1000 and so is the error of the reduction
            assert sa.eccentric_from_mean(x + turn, e) == pytest.approx(sa.eccentric_from_mean(x, e) + turn, abs=1e-12 + 4e-15 * abs(turn))
            assert sa.true_from_eccentric(x + turn, e) == pytest.approx(sa.true_from_eccentric(x, e) + turn, abs=1e-12 + 4e-15 * abs(turn))
            assert sa.eccentric_from_true(x + turn, e) == pytest.approx(sa.eccentric_from_true(x, e) + turn, abs=1e-12 + 4e-15 * abs(turn))
            assert sa.mean_from_true(sa.true_from_mean(x + turn, e), e) == pytest.approx(x + turn, abs=(1e-11 + 4e-15 * abs(turn)) * (1000 if e > 0.9 else 1))
    series = [sa.true_from_mean(0.05 * j, 0.7) for j in range(-400, 400)]
    assert all(b > a for a, b in zip(series, series[1:]))                                                           # increasing through 6 revolutions: no jump of a turn
    assert abs(sa.true_from_mean(100.0, 0.7) - 100.0) < PI and abs(sa.eccentric_from_mean(100.0, 0.7) - 100.0) <= 0.7
    assert sa.eccentric_from_mean(1e9, 0.5) == pytest.approx(1e9, abs=0.5) and sa.true_from_eccentric(-1e9, 0.5) == pytest.approx(-1e9, abs=PI)


def test_nearly_parabolic_orbits_near_periapsis():
    e = 1 - 1e-12
    ecc = sa.eccentric_from_mean(1e-10, e)
    assert ecc == pytest.approx(8.434303040921716e-4, rel=1e-13, abs=0)
    assert ecc == pytest.approx((6e-10) ** (1 / 3), rel=1e-3, abs=0)                                                       # E^3 / 6 = M to first order
    assert (1 - e) * ecc + e * (ecc ** 3 / 6 - ecc ** 5 / 120 + ecc ** 7 / 5040) == pytest.approx(1e-10, rel=1e-12, abs=0)  # the residual, with the series by hand
    assert sa.mean_from_eccentric(ecc, e) == pytest.approx(1e-10, rel=1e-12, abs=0)
    for exponent in (-3, -6, -9, -12):
        for m in (1e-12, 1e-8, 1e-4, 0.1, 3.0):
            e = 1 - 10.0 ** exponent
            ecc = sa.eccentric_from_mean(m, e)
            assert sa.mean_from_eccentric(ecc, e) == pytest.approx(m, rel=1e-12, abs=0) and 0 < ecc <= PI
            eh = 1 + 10.0 ** exponent
            f = sa.hyperbolic_from_mean(m, eh)
            assert sa.mean_from_hyperbolic(f, eh) == pytest.approx(m, rel=1e-12, abs=0) and f > 0
    limit = math.nextafter(1.0, 0.0)
    assert sa.mean_from_eccentric(sa.eccentric_from_mean(1.0, limit), limit) == pytest.approx(1.0, rel=1e-13, abs=0)
    above = math.nextafter(1.0, 2.0)
    assert sa.mean_from_hyperbolic(sa.hyperbolic_from_mean(1.0, above), above) == pytest.approx(1.0, rel=1e-13, abs=0)
    # the true anomaly of a nearly parabolic orbit near periapsis: tan(nu/2) = sqrt((1+e)/(1-e)) tan(E/2), no digit lost
    for ecc in (1e-9, 1e-6, 1e-3):
        e = 1 - 1e-10
        assert math.tan(sa.true_from_eccentric(ecc, e) / 2) == pytest.approx(math.sqrt((1 + e) / (1 - e)) * math.tan(ecc / 2), rel=1e-12, abs=0)


def test_limits_of_the_open_orbit_functions():
    assert sa.hyperbolic_from_mean(1e-9, 3.0) == pytest.approx(5e-10, rel=1e-15, abs=0)                                    # F -> M / (e - 1)
    assert sa.hyperbolic_from_mean(1e100, 2.0) == pytest.approx(math.log(1e100), abs=1e-3)                          # F -> ln(2 M / e)
    assert sa.hyperbolic_from_mean(1e150, 1.5) == pytest.approx(math.log(2e150 / 1.5), abs=1e-3) and sa.hyperbolic_from_mean(-1e150, 1.5) < -340
    assert sa.mean_from_hyperbolic(700, 1.5) == pytest.approx(1.5 * math.sinh(700), rel=1e-12, abs=0)
    assert sa.hyperbolic_from_true(2.0, 2.0) == pytest.approx(2 * math.atanh(math.tan(1.0) / math.sqrt(3)), rel=1e-14, abs=0)
    for nu in (2.2, PI, -2.2, -PI, 2 * PI / 3 + 1e-9):
        with pytest.raises(ValueError, match="asymptote"):
            sa.hyperbolic_from_true(nu, 2.0)
    with pytest.raises(ValueError, match="too large for a float"):
        sa.mean_from_hyperbolic(700, 1e150)
    assert (sa.MAX_ANGLE, sa.MAX_HYPERBOLIC, sa.MAX_MEAN, sa.__version__) == (1e9, 700.0, 1e150, "0.1.0")


def test_refusals_name_the_argument():
    for bad in (True, False, "1", None, 1 + 0j, float("nan"), float("inf"), float("-inf"), 10 ** 400):
        for fun in CLOSED + OPEN:
            with pytest.raises(ValueError, match="must be a finite real number"):
                fun(bad, 0.5 if fun in CLOSED else 2.0)
            with pytest.raises(ValueError, match="e must be a finite real number"):
                fun(0.5, bad)
    for fun in CLOSED:
        for e in (1.0, 1.5, -0.1, -5e-324, 1e9):
            with pytest.raises(ValueError, match="e must be in .0, 1. for a closed orbit"):
                fun(0.5, e)
        assert math.isfinite(fun(0.5, math.nextafter(1.0, 0.0)))
        for angle in (1.0000001e9, -1.0000001e9):
            with pytest.raises(ValueError, match="must be a finite real number within"):
                fun(angle, 0.5)
        assert math.isfinite(fun(1e9, 0.5)) and math.isfinite(fun(-1e9, 0.5))
    for fun in OPEN:
        for e in (1.0, 0.5, 0.0, -2.0):
            with pytest.raises(ValueError, match="e must be greater than 1 for an open orbit"):
                fun(0.5, e)
        assert math.isfinite(fun(0.5, math.nextafter(1.0, 2.0)))
    for bad in (700.0000001, -701.0):
        with pytest.raises(ValueError, match="F must be a finite real number within"):
            sa.mean_from_hyperbolic(bad, 2.0)
        with pytest.raises(ValueError, match="F must be a finite real number within"):
            sa.true_from_hyperbolic(bad, 2.0)
    for bad in (1.0000001e150, -1.0000001e150):
        with pytest.raises(ValueError, match="M must be a finite real number within"):
            sa.hyperbolic_from_mean(bad, 2.0)
    for bad in (3.2, -3.2, 100.0):
        with pytest.raises(ValueError, match="nu must be a finite real number within"):
            sa.hyperbolic_from_true(bad, 2.0)
    with pytest.raises(ValueError, match="M must be"):
        sa.eccentric_from_mean("x", 0.5)
    with pytest.raises(ValueError, match="E must be"):
        sa.mean_from_eccentric(None, 0.5)
    with pytest.raises(ValueError, match="nu must be"):
        sa.eccentric_from_true(None, 0.5)


def test_near_periapsis_the_direct_equations_keep_their_digits():
    """(1 - e) x + e (x - sin x) with x - sin x = x^3/6 - x^5/120 + x^7/5040 - ..., written out by hand. Computed as
    x - e sin x the result would be right to 1e-19 only, i.e. to 6e-10 of a value of 1.7e-10."""
    for x in (1e-3, 0.01, 0.1, 0.3, 0.49):
        series = x ** 3 / 6 - x ** 5 / 120 + x ** 7 / 5040 - x ** 9 / 362880 + x ** 11 / 39916800 - x ** 13 / 6227020800
        hyper = x ** 3 / 6 + x ** 5 / 120 + x ** 7 / 5040 + x ** 9 / 362880 + x ** 11 / 39916800 + x ** 13 / 6227020800
        for gap in (1e-12, 1e-9, 1e-6):
            e = 1 - gap
            assert sa.mean_from_eccentric(x, e) == pytest.approx((1 - e) * x + e * series, rel=3e-15, abs=0)
            assert sa.mean_from_eccentric(-x, e) == pytest.approx(-((1 - e) * x + e * series), rel=3e-15, abs=0)
            eh = 1 + gap
            assert sa.mean_from_hyperbolic(x, eh) == pytest.approx((eh - 1) * x + eh * hyper, rel=3e-15, abs=0)
            assert sa.eccentric_from_mean((1 - e) * x + e * series, e) == pytest.approx(x, rel=1e-13, abs=0)
            assert sa.hyperbolic_from_mean((eh - 1) * x + eh * hyper, eh) == pytest.approx(x, rel=1e-13, abs=0)
    # and away from periapsis the plain expression: at x = 0.5 and above nothing cancels
    for x in (0.5, 0.75, 2.0, 3.1):
        assert sa.mean_from_eccentric(x, 0.9) == pytest.approx(x - 0.9 * math.sin(x), rel=2e-16, abs=0) and sa.mean_from_hyperbolic(x, 1.5) == pytest.approx(1.5 * math.sinh(x) - x, rel=4e-16, abs=0)


def test_the_solver_converges_quadratically_on_ordinary_orbits(monkeypatch):
    """The residual is evaluated a handful of times: Newton's method with the right slope. A wrong slope would still end
    at the root (the bracket guarantees it) but only after dozens of bisections."""
    calls = []
    plain, hyper = sa._x_minus_sin, sa._sinh_minus_x
    monkeypatch.setattr(sa, "_x_minus_sin", lambda x: calls.append(x) or plain(x))
    monkeypatch.setattr(sa, "_sinh_minus_x", lambda x: calls.append(x) or hyper(x))
    for m, e in ((1.0, 0.5), (3.0, 0.9), (0.1, 0.3), (2.0, 0.1), (0.5, 0.7)):
        calls.clear()
        root = sa.eccentric_from_mean(m, e)
        assert 2 <= len(calls) <= 8 and root - e * math.sin(root) == pytest.approx(m, abs=1e-15)
    for m, e in ((4.1, 2.4), (1.0, 1.5), (0.2, 3.0), (10.0, 5.0)):
        calls.clear()
        root = sa.hyperbolic_from_mean(m, e)
        assert 2 <= len(calls) <= 9 and e * math.sinh(root) - root == pytest.approx(m, rel=1e-14, abs=0)
    calls.clear()
    assert sa.eccentric_from_mean(0.7, 0.0) == 0.7 and len(calls) == 1                     # a circular orbit: the first guess is the answer
    calls.clear()
    assert sa.eccentric_from_mean(0.0, 0.5) == 0.0 and sa.hyperbolic_from_mean(0.0, 2.0) == 0.0 and not calls
