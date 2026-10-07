"""Guard tests of star_elements added by the reviewer on 2026-10-07, after the corrected mutation runner measured the
package at 0.82, below the present 0.85 gate. Expected values come from the rotation written out here as three
elementary rotations, from closed-form conic geometry, and from the stated ranges of the angles."""
import math

import pytest

import star_elements as se

TWO_PI = 2 * math.pi


def rz(a, v):
    c, s = math.cos(a), math.sin(a)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


def rx(a, v):
    c, s = math.cos(a), math.sin(a)
    return (v[0], c * v[1] - s * v[2], s * v[1] + c * v[2])


def by_rotations(h, e, i, raan, argp, nu, mu):
    """Perifocal state turned by argp about z, by i about x, by raan about z: three elementary rotations, not one matrix."""
    p = h * h / mu
    r = p / (1 + e * math.cos(nu))
    rp = (r * math.cos(nu), r * math.sin(nu), 0.0)
    vp = (-mu / h * math.sin(nu), mu / h * (e + math.cos(nu)), 0.0)
    return tuple(rz(raan, rx(i, rz(argp, x))) for x in (rp, vp))


CASES = [(52000.0, 0.3, 0.9, 1.1, 2.3, 0.7, 398600.4418), (60000.0, 0.01, 2.5, 4.0, 5.5, 3.9, 398600.4418), (1.3, 0.6, 1.2, 5.9, 0.4, 5.1, 1.0),
         (0.5, 0.2, 0.3, 2.2, 4.4, 1.9, 0.5), (0.9, 0.85, 2.9, 0.6, 3.3, 2.8, 0.7), (80000.0, 1.5, 0.8, 3.0, 1.0, 2.0, 398600.4418),
         (75000.0, 2.5, 1.9, 0.2, 6.0, -1.5, 398600.4418), (2.0, 1.0, 1.0, 1.0, 1.0, 2.5, 1.0)]


@pytest.mark.parametrize("case", CASES)
def test_state_from_elements_equals_three_elementary_rotations(case):
    h, e, i, raan, argp, nu, mu = case
    r, v = se.coe_to_rv(h, e, i, raan, argp, nu, mu)
    er, ev = by_rotations(h, e, i, raan, argp, nu, mu)
    nr, nv = math.sqrt(sum(x * x for x in er)), math.sqrt(sum(x * x for x in ev))
    assert max(abs(a - b) for a, b in zip(r, er)) <= 1e-13 * nr and max(abs(a - b) for a, b in zip(v, ev)) <= 1e-13 * nv


@pytest.mark.parametrize("case", [c for c in CASES if c[1] != 1.0])
def test_round_trip_and_ranges_of_the_angles(case):
    h, e, i, raan, argp, nu, mu = case
    r, v = se.coe_to_rv(h, e, i, raan, argp, nu, mu)
    got = se.rv_to_coe(r, v, mu)
    assert got[0] == pytest.approx(h, rel=1e-12) and got[1] == pytest.approx(e, rel=1e-11) and got[2] == pytest.approx(i, abs=1e-11)
    for value, expected in zip(got[3:], (raan, argp, nu)):
        assert 0.0 <= value < TWO_PI                          # every angle is returned in one turn, never negative
        assert value == pytest.approx(expected % TWO_PI, abs=1e-9)
    assert 0.0 <= got[2] <= math.pi


def test_canonical_units_are_valid_inputs():
    """Nothing in the definition depends on the size of the numbers: mu below 1, |r| = 1, |v| = 1 and h below 1 are valid."""
    r, v = (1.0, 0.0, 0.0), (0.0, 0.6, 0.8)                  # |r| = 1 and |v| = 1
    h, e, i, raan, argp, nu = se.rv_to_coe(r, v, 0.8)        # mu = 0.8: v^2 > mu / r, so not circular
    assert h == pytest.approx(1.0) and i == pytest.approx(math.atan2(0.8, 0.6)) and e == pytest.approx(0.25)   # e = v^2 r / mu - 1 at periapsis
    assert raan == pytest.approx(0.0, abs=1e-12) and nu == pytest.approx(0.0, abs=1e-7) and argp == pytest.approx(0.0, abs=1e-7)
    assert se.rv_to_coe((1.0, 0.0, 0.0), (0.0, 0.9, 1.2), 2.0)[0] == pytest.approx(1.5)          # |r| = 1, |v| = 1.5
    assert se.rv_to_coe((2.0, 0.0, 0.0), (0.0, 0.6, 0.8), 1.5)[0] == pytest.approx(2.0)          # |r| = 2, |v| = 1
    r2, v2 = se.coe_to_rv(0.5, 0.2, 0.3, 2.2, 4.4, 1.9, 0.5)                                    # h = 0.5 and mu = 0.5
    assert se.rv_to_coe(r2, v2, 0.5)[0] == pytest.approx(0.5, rel=1e-12)
    circular = se.coe_to_rv(1.0, 0.0, 0.5, 1.0, 0.0, 2.0, 1.0)                                   # e = 0 is a valid INPUT of coe_to_rv
    assert math.sqrt(sum(x * x for x in circular[0])) == pytest.approx(1.0, rel=1e-14) and math.sqrt(sum(x * x for x in circular[1])) == pytest.approx(1.0, rel=1e-14)


def test_elements_that_cannot_be_a_state_are_refused():
    good = (52000.0, 0.3, 0.9, 1.1, 2.3, 0.7)
    for h in (0.0, -1.0, -5e-324):
        with pytest.raises(ValueError, match="positive"):
            se.coe_to_rv(h, *good[1:])
    for e in (-0.1, -5e-324):
        with pytest.raises(ValueError, match="non-negative"):
            se.coe_to_rv(good[0], e, *good[2:])
    for mu in (0.0, -1.0):
        with pytest.raises(ValueError, match="positive"):
            se.coe_to_rv(*good, mu)
        with pytest.raises(ValueError, match="mu must be positive"):
            se.rv_to_coe((7000.0, 0.0, 0.0), (0.0, 5.0, 5.0), mu)
    for bad in (float("nan"), float("inf")):
        for k in range(6):
            args = list(good)
            args[k] = bad
            with pytest.raises(ValueError, match="finite"):
                se.coe_to_rv(*args)


def test_open_orbits_are_accepted_inside_their_asymptotes_and_refused_outside():
    h, mu = 80000.0, 398600.4418
    # parabola (e = 1): every true anomaly except exactly 180 degrees, where 1 + cos(nu) is exactly zero
    assert math.isfinite(se.coe_to_rv(h, 1.0, 0.5, 0.0, 0.0, 0.0, mu)[0][0]) and math.isfinite(se.coe_to_rv(h, 1.0, 0.5, 0.0, 0.0, 3.0, mu)[0][0])
    assert 1 + math.cos(math.pi) == 0.0
    with pytest.raises(ValueError, match="asymptotes"):
        se.coe_to_rv(h, 1.0, 0.5, 0.0, 0.0, math.pi, mu)
    # hyperbola with e = 1.5: the asymptote is at acos(-1/1.5) = 2.3005 rad
    for nu in (0.0, 1.0, 2.0, 2.29, -2.29):                  # 1 + e cos(nu) between 0 and 1 for nu = 2.0: still a valid point
        r, v = se.coe_to_rv(h, 1.5, 0.5, 0.0, 0.0, nu, mu)
        radius = math.sqrt(sum(x * x for x in r))
        assert radius == pytest.approx(h * h / mu / (1 + 1.5 * math.cos(nu)), rel=1e-13) and radius > 0.0
    for nu in (2.31, 2.5, math.pi, -2.5, 3.5):               # 4.0 rad would be inside again (it is -2.28 rad)
        with pytest.raises(ValueError, match="asymptotes"):
            se.coe_to_rv(h, 1.5, 0.5, 0.0, 0.0, nu, mu)
    for e in (1.0000001, 1.2, 2.0, 5.0):                     # just open orbits too
        with pytest.raises(ValueError, match="asymptotes"):
            se.coe_to_rv(h, e, 0.5, 0.0, 0.0, math.pi, mu)
    assert math.isfinite(se.coe_to_rv(h, 0.999999, 0.5, 0.0, 0.0, math.pi, mu)[0][0])            # an ellipse reaches 180 degrees


def test_states_at_the_apsides_and_at_the_nodes_do_not_break_the_inverse_cosine():
    """At periapsis, apoapsis and with the periapsis on the line of nodes, the cosine computed from rounded vectors can leave
    [-1, 1] by one unit in the last place: the result must still be the angle, to the accuracy an inverse cosine allows."""
    mu = 398600.4418
    for k in range(300):
        h = 50000.0 + 37.0 * k
        e = 0.05 + 0.003 * k
        i = 0.2 + 0.009 * k
        raan = 0.1 + 0.02 * k
        for argp, nu in ((0.7 + 0.01 * k, 0.0), (0.7 + 0.01 * k, math.pi), (0.0, 0.9 + 0.01 * k), (math.pi, 0.9 + 0.01 * k)):
            r, v = se.coe_to_rv(h, e, i, raan, argp, nu, mu)
            got = se.rv_to_coe(r, v, mu)
            for value, expected in zip(got[3:], (raan, argp, nu)):
                d = abs(value - expected % TWO_PI)
                assert min(d, TWO_PI - d) < 1e-6 and 0.0 <= value < TWO_PI
