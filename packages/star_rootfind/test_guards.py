"""Guard tests of star_rootfind written by the reviewer: the order of the floats, the two branches of the
bisection, the choice of the end returned and the edges of the scan. Expected values are derived by hand."""
import math

import pytest

import star_rootfind as sr


def counted(g):
    calls = []

    def h(x):
        calls.append(x)
        return g(x)
    return h, calls


def test_rank_orders_the_floats_and_unrank_inverts_it():
    xs = [-1e300, -2.5, -1.0, -5e-324, 0.0, 5e-324, 1.0, 1.5, 1e300]
    ranks = [sr._rank(x) for x in xs]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
    assert sr._rank(0.0) == 0 and sr._rank(-0.0) == 0 and sr._rank(5e-324) == 1 and sr._rank(-5e-324) == -1
    assert sr._rank(1.0) == 0x3FF0000000000000 and sr._rank(-1.0) == -0x3FF0000000000000
    for x in xs:
        assert sr._unrank(sr._rank(x)) == x
        assert sr._rank(math.nextafter(x, math.inf)) == sr._rank(x) + 1
    assert sr._unrank(1) == 5e-324 and sr._unrank(-1) == -5e-324 and sr._unrank(0) == 0.0 and sr._unrank(-2) == -1e-323


def test_the_end_returned_is_the_one_with_the_smaller_value():
    third = 1.0 / 3.0                                       # the float below 1/3
    up = math.nextafter(third, 1.0)
    # g changes sign between `third` and `up`; the sizes on the two sides are chosen by hand
    assert sr.find_root(lambda x: -1.0 if x <= third else 5.0, 0.0, 1.0) == third       # |-1| < |5|: the lower end
    assert sr.find_root(lambda x: -5.0 if x <= third else 1.0, 0.0, 1.0) == up          # |1| < |-5|: the upper end
    assert sr.find_root(lambda x: -2.0 if x <= third else 2.0, 0.0, 1.0) == third       # a tie: the lower end
    assert sr.find_root(lambda x: 1.0 if x <= third else -5.0, 0.0, 1.0) == third       # decreasing
    assert sr.find_root(lambda x: 5.0 if x <= third else -1.0, 0.0, 1.0) == up
    assert sr.find_root(lambda x: 2.0 if x <= third else -2.0, 0.0, 1.0) == third
    # the values compared are those at the FINAL ends, not those at a and b: large at the ends, small next to the jump
    assert sr.find_root(lambda x: (-9.0 if x < 0.2 else -1.0) if x <= third else (5.0 if x < 0.9 else 0.5), 0.0, 1.0) == third
    assert sr.find_root(lambda x: (-0.5 if x < 0.2 else -5.0) if x <= third else (1.0 if x < 0.9 else 9.0), 0.0, 1.0) == up


def test_jump_located_on_both_sides_of_zero_and_across_it():
    for edge in (-123.456, -1e-200, -5e-324, 0.0, 5e-324, 1e-310, 0.3, 7e150):
        got = sr.find_root(lambda x, e=edge: -1.0 if x <= e else 1.0, -1e300, 1e300)
        assert got == edge and math.copysign(1.0, got) == (1.0 if edge >= 0.0 else -1.0)
        got = sr.find_root(lambda x, e=edge: 3.0 if x <= e else -3.0, -1e300, 1e300)
        assert got == edge


def test_number_of_evaluations():
    f, calls = counted(lambda x: x - 3.0)
    assert sr.find_root(f, 3.0, 5.0) == 3.0 and calls == [3.0]                          # a root at a: one evaluation
    f, calls = counted(lambda x: x - 5.0)
    assert sr.find_root(f, 3.0, 5.0) == 5.0 and calls == [3.0, 5.0]
    f, calls = counted(lambda x: x - 1.5)
    assert sr.find_root(f, 1.0, 2.0) == 1.5 and calls == [1.0, 2.0, 1.5]                # the middle float of [1, 2] is 1.5
    f, calls = counted(lambda x: x - 1.25)
    assert sr.find_root(f, 1.0, 2.0) == 1.25 and calls == [1.0, 2.0, 1.5, 1.25]
    f, calls = counted(lambda x: x - 1.75)
    assert sr.find_root(f, 1.0, 2.0) == 1.75 and calls == [1.0, 2.0, 1.5, 1.75]
    f, calls = counted(lambda x: 1.0 if x > 1.0 else -1.0)                              # between 1 and 2 there are 2^52 floats
    assert sr.find_root(f, 1.0, 2.0) == 1.0 and len(calls) == 2 + 52
    f, calls = counted(lambda x: 1.0 if x >= 2.0 else -1.0)
    assert sr.find_root(f, 1.0, 2.0) == math.nextafter(2.0, 0.0) and len(calls) == 2 + 52
    f, calls = counted(lambda x: x)
    lo, hi = 1.0, math.nextafter(1.0, 2.0)
    with pytest.raises(ValueError, match="same sign"):
        sr.find_root(f, lo, hi)
    assert calls == [lo, hi]
    f, calls = counted(lambda x: x - 1.0000000000000001)                                # the constant rounds to 1.0: f(1.0) == 0
    assert sr.find_root(f, 0.5, hi) == 1.0
    f, calls = counted(lambda x: -1.0 if x <= 1.0 else 1.0)                             # two neighbouring floats: no further evaluation
    assert sr.find_root(f, lo, hi) == lo and calls == [lo, hi]


def test_refusal_in_the_middle_of_the_search():
    with pytest.raises(ValueError, match="finite real"):
        sr.find_root(lambda x: math.nan if 1.2 < x < 1.8 else x - 1.5, 1.0, 2.0)
    with pytest.raises(ValueError, match="finite real"):
        sr.find_root(lambda x: "0" if x == 1.5 else x - 1.6, 1.0, 2.0)
    with pytest.raises(ValueError, match="finite real"):
        sr.find_root(lambda x: math.inf, 1.0, 2.0)
    with pytest.raises(ValueError, match="finite real"):
        sr.find_root(lambda x: x - 1.5 if x < 2.0 else -math.inf, 1.0, 2.0)             # only f(b) is refused
    with pytest.raises(ValueError, match="same sign"):
        sr.find_root(lambda x: -1.0 - x, 1.0, 2.0)                                      # both negative
    with pytest.raises(ValueError, match="same sign"):
        sr.find_root(lambda x: 1.0 + x, 1.0, 2.0)                                       # both positive
    assert sr.find_root(lambda x: int(x) - 1 if x < 1.5 else 2, 1.0, 2.0) == 1.0        # integers returned by f are accepted


def test_scan_edges_and_pieces():
    f, calls = counted(lambda x: x - 2.5)
    assert sr.find_roots(f, 0.0, 4.0, 4) == (2.5,)
    assert calls[:5] == [0.0, 1.0, 2.0, 3.0, 4.0] and all(2.0 < x < 3.0 for x in calls[5:])   # the edges first, then only the piece that changes sign
    f, calls = counted(lambda x: x * x + 1.0)
    assert sr.find_roots(f, -1.0, 1.0, 8) == () and calls == [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
    assert sr.find_roots(lambda x: (x - 1) * (x - 2) * (x - 3), 0.0, 4.0, 8) == (1.0, 2.0, 3.0)       # roots on the edges, each reported once
    assert sr.find_roots(lambda x: (x - 0.5) * (x - 1.5) * (x - 3.5), 0.0, 4.0, 4) == (0.5, 1.5, 3.5)  # roots inside three pieces
    assert sr.find_roots(lambda x: (x - 0.5) * (x - 1.5) * (x - 3.5), 0.0, 4.0, 2) == (3.5,)           # two roots in the first piece are missed
    assert sr.find_roots(lambda x: x, 0.0, 4.0, 4) == (0.0,) and sr.find_roots(lambda x: x - 4.0, 0.0, 4.0, 4) == (4.0,)
    assert sr.find_roots(lambda x: x, -4.0, 0.0, 4) == (0.0,) and math.copysign(1.0, sr.find_roots(lambda x: x, -4.0, -0.0, 4)[0]) == 1.0
    assert sr.find_roots(lambda x: x - 1.0, 0.0, 4.0, 4) == (1.0,)                      # a zero edge next to a change of sign: once, not twice
    assert sr.find_roots(lambda x: 1.0 - x, 0.0, 4.0, 4) == (1.0,)
    assert sr.find_roots(lambda x: -1.0 if x <= 2.2 else 1.0, 0.0, 4.0, 4) == (2.2,)
    assert sr.find_roots(lambda x: x - 3.9, 0.0, 4.0, 4) == (3.9,)                      # the last piece is scanned too
    assert sr.find_roots(lambda x: x - 0.1, 0.0, 4.0, 4) == (0.1,)                      # and the first
    two = math.nextafter(1.0, 2.0)
    assert sr.find_roots(lambda x: -1.0 if x <= 1.0 else 1.0, 1.0, two, 9) == (1.0,)    # more pieces than floats
    assert sr.find_roots(lambda x: x - 1.0, 1.0, two, 9) == (1.0,) and sr.find_roots(lambda x: x - two, 1.0, two, 9) == (two,)
    with pytest.raises(ValueError, match="finite real"):
        sr.find_roots(lambda x: math.nan if x == 3.0 else 1.0, 0.0, 4.0, 4)             # a refusal at an edge


def test_zero_is_returned_as_positive_zero_from_every_path():
    for got in (sr.find_root(lambda x: x, -0.0, 1.0), sr.find_root(lambda x: x, -1.0, -0.0), sr.find_root(lambda x: x, -1.0, 1.0),
                sr.find_root(lambda x: x, -3.0, 1.0),
                sr.find_roots(lambda x: x, -0.0, 1.0, 2)[0], sr.find_roots(lambda x: x, -1.0, -0.0, 2)[0], sr.find_roots(lambda x: x, -3.0, 1.0, 1)[0]):
        assert got == 0.0 and math.copysign(1.0, got) == 1.0
    assert sr.find_root(lambda x: -1.0 if x < 0.0 else 1.0, -1.0, 1.0) == -5e-324      # the jump at 0: the tie goes to the lower end
    assert sr.find_root(lambda x: -1.0 if x < 0.0 else 0.5, -1.0, 1.0) == 0.0 and sr.find_root(lambda x: -0.5 if x < 0.0 else 1.0, -1.0, 1.0) == -5e-324
    assert sr._positive(5e-324) is True and sr._positive(0.0) is False and sr._positive(-5e-324) is False and sr._positive(1.0) is True


def test_scan_passes_the_values_of_its_own_piece_to_the_search():
    below = math.nextafter(3.0, 0.0)
    # the jump is in the last float of the piece [2, 3]: the upper end of the search never moves, so the value at 3 decides
    assert sr.find_roots(lambda x: -5.0 if x < 3.0 else 1.0, 0.0, 4.0, 4) == (3.0,)     # values -5, -5, -5, 1, 1: |1| < |-5|
    assert sr.find_roots(lambda x: -1.0 if x < 3.0 else 5.0, 0.0, 4.0, 4) == (below,)
    assert sr.find_roots(lambda x: (-9.0 if x < 1.5 else -1.0) if x < 3.0 else (5.0 if x < 3.5 else 0.25), 0.0, 4.0, 4) == (below,)
    # the jump just above the lower edge 2: the lower end never moves, so the value at 2 decides
    above = math.nextafter(2.0, 3.0)
    assert sr.find_roots(lambda x: -1.0 if x <= 2.0 else 5.0, 0.0, 4.0, 4) == (2.0,)
    assert sr.find_roots(lambda x: -5.0 if x <= 2.0 else 1.0, 0.0, 4.0, 4) == (above,)
    assert sr.find_roots(lambda x: (-0.25 if x < 1.5 else -5.0) if x <= 2.0 else (1.0 if x < 3.5 else 9.0), 0.0, 4.0, 4) == (above,)


def test_limits_at_their_exact_values():
    assert sr.BIG == 1e300 and sr.MAX_PIECES == 100000
    assert sr.find_root(lambda x: x, -1e300, 1e300) == 0.0
    for bad in (math.nextafter(1e300, math.inf), -math.nextafter(1e300, math.inf)):
        with pytest.raises(ValueError, match="within"):
            sr.find_root(lambda x: x, bad, 0.0) if bad < 0 else sr.find_root(lambda x: x, 0.0, bad)
    assert len(sr.find_roots(lambda x: x - 0.123, -1.0, 1.0, 100000)) == 1
    with pytest.raises(ValueError, match="pieces"):
        sr.find_roots(lambda x: x, -1.0, 1.0, 100001)
    assert sr.find_roots(lambda x: x - 0.123, -1.0, 1.0, 1) == (0.123,)
