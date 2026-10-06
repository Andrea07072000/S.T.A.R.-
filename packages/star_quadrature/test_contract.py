"""Contract tests for star_quadrature: hostile values, range edges, pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import pytest

import star_quadrature as sq


HOSTILE = [0, 33, -1, 2.0, "2", None, True, False]


def test_pinned_constants_and_exports():
    assert sq.MAX_POINTS == 32
    assert sq.BIG == 1e150
    assert sq.__all__ == ["gauss_legendre", "integrate", "legendre"]


@pytest.mark.parametrize("n", HOSTILE)
def test_gauss_legendre_n_refusals(n):
    if n in (1, 32) and not isinstance(n, bool):
        sq.gauss_legendre(n)
    else:
        with pytest.raises(ValueError, match="n must be an integer from 1 to 32"):
            sq.gauss_legendre(n)


@pytest.mark.parametrize("n", HOSTILE)
def test_integrate_n_refusals(n):
    if n in (1, 32) and not isinstance(n, bool):
        assert isinstance(sq.integrate(lambda t: 0.0, 0.0, 1.0, n), float)
    else:
        with pytest.raises(ValueError, match="n must be an integer from 1 to 32"):
            sq.integrate(lambda t: 0.0, 0.0, 1.0, n)


@pytest.mark.parametrize("n", [-1, 33, 1.5, True, None])
def test_legendre_n_refusals(n):
    with pytest.raises(ValueError, match="from 0 to 32"):
        sq.legendre(n, 0.0)


def test_legendre_n_edges_accepted():
    assert sq.legendre(0, 0.0) == (1.0, 0.0)
    assert isinstance(sq.legendre(32, 0.1)[0], float)


@pytest.mark.parametrize("x", [1.0000001, -1.0000001, float("nan"), float("inf"), True, "x", None, 1 + 0j])
def test_legendre_x_refusals(x):
    with pytest.raises(ValueError):
        sq.legendre(3, x)


def test_legendre_x_edges_accepted():
    assert sq.legendre(3, 1.0)[0] == 1.0
    assert sq.legendre(3, -1.0)[0] == -1.0


@pytest.mark.parametrize("f", [3, None, "f"])
def test_integrate_f_not_callable(f):
    with pytest.raises(ValueError, match="f must be callable"):
        sq.integrate(f, 0.0, 1.0, 2)


@pytest.mark.parametrize("bad", [True, "0", None, float("nan"), float("inf"), 1 + 0j, 1.0000001e150, -1.0000001e150])
def test_integrate_a_b_refusals(bad):
    with pytest.raises(ValueError):
        sq.integrate(lambda t: 0.0, bad, 1.0, 2)
    with pytest.raises(ValueError):
        sq.integrate(lambda t: 0.0, 0.0, bad, 2)


def test_integrate_a_b_edges_accepted():
    assert sq.integrate(lambda t: 0.0, -1e150, 1e150, 2) == 0.0


@pytest.mark.parametrize("ret", ["x", None, True, 1 + 0j, float("nan"), float("inf")])
def test_integrate_f_return_refusals(ret):
    with pytest.raises(ValueError, match="must return a finite real number"):
        sq.integrate(lambda t: ret, 0.0, 1.0, 2)


def test_integrate_overflow_refusal():
    with pytest.raises(ValueError, match="overflows"):
        sq.integrate(lambda t: 1e300, -1e150, 1e150, 2)
