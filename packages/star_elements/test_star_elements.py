"""Published references: Curtis (3rd ed.) Example 4.3 (r, v -> elements) and Example 4.7 (elements -> r, v),
printed to 4 significant figures; round-trip and singular-case contracts."""
import math
import random

import pytest

from star_elements import coe_to_rv, rv_to_coe

D = math.degrees


def test_curtis_example_4_3():
    h, e, i, raan, argp, nu = rv_to_coe([-6045, -3490, 2500], [-3.457, 6.618, 2.533])
    # half a unit of the last printed digit (4 significant figures)
    assert abs(h - 58310) <= 5 and abs(e - 0.1712) <= 5e-5
    assert abs(D(i) - 153.2) <= 0.05 and abs(D(raan) - 255.3) <= 0.05
    assert abs(D(argp) - 20.07) <= 0.005 and abs(D(nu) - 28.45) <= 0.005


def test_curtis_example_4_7():
    r, v = coe_to_rv(80000, 1.4, math.radians(30), math.radians(40), math.radians(60), math.radians(30))
    for got, exp in zip(r, (-4040, 4815, 3629)):
        assert abs(got - exp) < 1.0
    for got, exp in zip(v, (-10.39, -4.772, 1.744)):
        assert abs(got - exp) < 0.005


def test_round_trip_random_elliptic():
    rnd = random.Random(20261003)
    for _ in range(500):
        el = (rnd.uniform(4e4, 1.5e5), rnd.uniform(0.01, 0.9), rnd.uniform(0.05, 3.0), rnd.uniform(0, 6.28),
              rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))
        back = rv_to_coe(*coe_to_rv(*el))
        assert abs(back[0] - el[0]) / el[0] < 1e-12 and abs(back[1] - el[1]) < 1e-10
        for a, b in zip(back[2:], el[2:]):
            assert abs(math.remainder(a - b, 2 * math.pi)) < 1e-8


@pytest.mark.parametrize("r,v", [([7000, 0, 0], [0, 7.5, 0.0]),            # equatorial
                                 ([7000, 0, 0], [0, 7.546049, 0.5])])       # near-circular? (inclined, e>0: valid)
def test_equatorial_raises_but_inclined_does_not(r, v):
    if v[2] == 0.0:
        with pytest.raises(ValueError):
            rv_to_coe(r, v)
    else:
        rv_to_coe(r, v)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        rv_to_coe([7000, 0, 0], [7.5, 0, 0])            # rectilinear
    with pytest.raises(ValueError):
        coe_to_rv(-1, 0.1, 0.5, 0, 0, 0)
    with pytest.raises(ValueError):
        coe_to_rv(80000, 1.4, 0.5, 0, 0, math.radians(150))  # beyond asymptote (cos nu < -1/e)
