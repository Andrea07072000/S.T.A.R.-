"""star_quadrature against published Gaussian tables, hand-derivable values, inverses and invariants.
Verifies public behaviour and numerical identities with tight tolerances.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_quadrature as sq


def test_published_gauss_legendre_tables_n2_to_n5():
    # Published FACTS (A&S table 25.4), absolute tolerance 1e-15.
    pub = {
        2: ((-0.577350269189626, 0.577350269189626), (1.0, 1.0)),
        3: ((-0.774596669241483, 0.0, 0.774596669241483), (0.555555555555556, 0.888888888888889, 0.555555555555556)),
        4: ((-0.861136311594053, -0.339981043584856, 0.339981043584856, 0.861136311594053),
            (0.347854845137454, 0.652145154862546, 0.652145154862546, 0.347854845137454)),
        5: ((-0.906179845938664, -0.538469310105683, 0.0, 0.538469310105683, 0.906179845938664),
            (0.236926885056189, 0.478628670499366, 0.568888888888889, 0.478628670499366, 0.236926885056189)),
    }
    for n, (xn, wn) in pub.items():
        x, w = sq.gauss_legendre(n)
        assert x == pytest.approx(xn, abs=1e-15)
        assert w == pytest.approx(wn, abs=1e-15)


def test_hand_closed_forms_legendre_and_rule_small_n():
    x1, w1 = sq.gauss_legendre(1)
    assert x1 == (0.0,) and w1 == (2.0,)  # exact
    x2, w2 = sq.gauss_legendre(2)
    # n=2 roots are ±1/sqrt(3), weights both 1.
    assert x2 == pytest.approx((-1 / math.sqrt(3), 1 / math.sqrt(3)), abs=2e-16)
    assert w2 == (1.0, 1.0)
    x3, w3 = sq.gauss_legendre(3)
    # n=3 roots are ±sqrt(3/5),0 and weights 5/9,8/9,5/9.
    assert x3 == pytest.approx((-math.sqrt(3 / 5), 0.0, math.sqrt(3 / 5)), abs=2e-16)
    assert w3 == pytest.approx((5 / 9, 8 / 9, 5 / 9), abs=2e-16)
    assert x3[1] == 0.0
    # n=5 centre weight = 128/225.
    assert sq.gauss_legendre(5)[1][2] == pytest.approx(128 / 225, abs=2e-16)


def test_rule_structure_invariants_1_to_32():
    for n in range(1, 33):
        x, w = sq.gauss_legendre(n)
        x2, w2 = sq.gauss_legendre(n)
        assert x == x2 and w == w2
        assert len(x) == n and len(w) == n
        assert all(type(v) is float for v in x + w)
        assert all(x[i] < x[i + 1] for i in range(n - 1))
        assert all(-1.0 < xi < 1.0 for xi in x)
        assert all(wi > 0.0 for wi in w)
        assert math.fsum(w) == pytest.approx(2.0, abs=4e-16)
        for i in range(n):
            assert x[i] == -x[n - 1 - i]
            assert w[i] == w[n - 1 - i]
        if n % 2:
            assert x[n // 2] == 0.0


def test_exactness_and_not_exact_at_2n():
    for n in range(1, 9):
        x, w = sq.gauss_legendre(n)
        for k in range(2 * n):
            s = math.fsum(wi * (xi ** k) for xi, wi in zip(x, w))
            target = 0.0 if (k % 2) else 2.0 / (k + 1)
            assert s == pytest.approx(target, abs=1e-14)
    x2, w2 = sq.gauss_legendre(2)
    assert math.fsum(wi * (xi ** 4) for xi, wi in zip(x2, w2)) == pytest.approx(2 / 9, abs=1e-15)
    assert math.fsum(wi * (xi ** 4) for xi, wi in zip(x2, w2)) != pytest.approx(2 / 5, abs=1e-15)
    x1, w1 = sq.gauss_legendre(1)
    assert math.fsum(wi * (xi ** 2) for xi, wi in zip(x1, w1)) == 0.0
    assert 0.0 != pytest.approx(2 / 3, abs=1e-15)


def test_integrate_examples_and_sign_limit_cases():
    assert sq.integrate(lambda t: 1.0, 2, 5, 1) == 3.0
    assert sq.integrate(lambda t: t, 0, 4, 1) == 8.0
    assert sq.integrate(lambda t: t * t, 0, 3, 2) == pytest.approx(9.0, abs=1e-14)
    # ∫(t^5+t^4)dt from -1 to 2 = [t^6/6 + t^5/5]_-1^2 = 63/6 + 33/5 = 17.1
    assert sq.integrate(lambda t: t**5 + t**4, -1, 2, 3) == pytest.approx(17.1, abs=1e-13)
    assert sq.integrate(lambda t: t * t, 3, 1, 2) == pytest.approx(-26 / 3, abs=1e-14)
    assert sq.integrate(lambda t: t * t, 3, 3, 2) == 0.0
    assert sq.integrate(math.sin, 0, math.pi, 10) == pytest.approx(2.0, abs=1e-14)
    assert sq.integrate(math.exp, 0, 1, 6) == pytest.approx(math.e - 1.0, abs=1e-14)
    v8 = sq.integrate(lambda t: 1 / t, 1, 2, 8)
    assert abs(v8 - math.log(2.0)) <= 1e-11
    assert abs(v8 - math.log(2.0)) > 1e-13
    assert sq.integrate(lambda t: 1 / t, 1, 2, 1) == pytest.approx(2 / 3, abs=1e-15)
    assert sq.integrate(lambda t: 7, 0, 2, 3) == pytest.approx(14.0, abs=1e-14)


def test_integrate_calls_f_exactly_n_times_increasing_inside_interval():
    pts = []
    def f(t):
        pts.append(t)
        return t * t + 2 * t + 3
    out = sq.integrate(f, -2.0, 5.0, 6)
    assert isinstance(out, float)
    assert len(pts) == 6
    assert all(-2.0 < p < 5.0 for p in pts)
    assert all(pts[i] < pts[i + 1] for i in range(len(pts) - 1))


def test_legendre_values_parity_endpoints_roots_and_integer_x():
    assert sq.legendre(0, 0.3) == (1.0, 0.0)
    assert sq.legendre(1, 0.3) == (0.3, 1.0)
    assert sq.legendre(2, 0.5) == pytest.approx((-0.125, 1.5), abs=1e-15)
    assert sq.legendre(3, 0.5) == pytest.approx((-0.4375, 0.375), abs=1e-15)
    assert sq.legendre(4, 0.5) == pytest.approx((-0.2890625, -1.5625), abs=1e-15)
    for n in range(0, 33):
        p1, d1 = sq.legendre(n, 1.0)
        pm1, dm1 = sq.legendre(n, -1.0)
        assert p1 == 1.0 and d1 == n * (n + 1) / 2
        assert pm1 == ((-1) ** n)
        assert dm1 == ((-1) ** (n + 1)) * n * (n + 1) / 2
    assert sq.legendre(32, 1.0) == (1.0, 528.0)
    for n in range(0, 10):
        x = 0.37
        p, _ = sq.legendre(n, x)
        pm, _ = sq.legendre(n, -x)
        assert pm == ((-1) ** n) * p
    assert sq.legendre(2, 0.0) == (-0.5, 0.0)
    assert sq.legendre(4, 0.0)[0] == 0.375
    for n in range(1, 33):
        nodes, _ = sq.gauss_legendre(n)
        assert max(abs(sq.legendre(n, xi)[0]) for xi in nodes) <= 1e-13
    assert all(type(sq.legendre(3, x)[0]) is float for x in (0, 1, -1))
