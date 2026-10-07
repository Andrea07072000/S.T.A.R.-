"""Refusal contract for star_spline: hostile values, range edges, and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_spline as ss


BAD_SCALARS = [True, False, "x", None, 1j, float("nan"), float("inf"), float("-inf"), 1e101, -1e101]
BAD_CONTAINERS = ["abc", None, 3.0, (v for v in [1, 2])]
XS_OK = [0.0, 1.0, 2.0]
YS_OK = [1.0, 2.0, 0.0]


def test_pinned_constants_and_exports():
    assert ss.MAX_POINTS == 300
    assert ss.BIG == 1e100
    assert ss.__all__ == ["second_derivatives", "values", "derivatives", "integral"]


@pytest.mark.parametrize("f,args", [
    (ss.second_derivatives, (XS_OK, YS_OK)),
    (ss.values, (XS_OK, YS_OK, [0.5])),
    (ss.derivatives, (XS_OK, YS_OK, [0.5])),
    (ss.integral, (XS_OK, YS_OK, 0.5, 1.5)),
])
def test_refuse_non_list_tuple_table_args(f, args):
    for bad in BAD_CONTAINERS:
        a = list(args)
        a[0] = bad
        with pytest.raises(ValueError, match="2 to 300 numbers"):
            f(*a)
        a = list(args)
        a[1] = bad
        with pytest.raises(ValueError, match="2 to 300 numbers"):
            f(*a)


def test_refuse_length_mismatch_and_limits():
    with pytest.raises(ValueError, match="same length"):
        ss.second_derivatives([0, 1, 2], [0, 1])
    with pytest.raises(ValueError, match="2 to 300 numbers"):
        ss.second_derivatives([0], [0])
    with pytest.raises(ValueError, match="2 to 300 numbers"):
        ss.second_derivatives(list(range(301)), list(range(301)))
    ss.second_derivatives(list(range(300)), list(range(300)))


def test_refuse_bad_numbers_in_xs_ys_and_monotonicity():
    for bad in BAD_SCALARS:
        with pytest.raises(ValueError, match="finite real numbers within"):
            ss.second_derivatives([0, 1, bad], [0, 1, 2])
        with pytest.raises(ValueError, match="finite real numbers within"):
            ss.second_derivatives([0, 1, 2], [0, 1, bad])

    with pytest.raises(ValueError, match="strictly increasing"):
        ss.second_derivatives([0, 1, 1, 2], [0, 1, 2, 3])
    with pytest.raises(ValueError, match="strictly increasing"):
        ss.second_derivatives([0, 2, 1], [0, 1, 2])


def test_points_argument_and_point_hostiles():
    with pytest.raises(ValueError, match="points must be a list or tuple"):
        ss.values(XS_OK, YS_OK, "bad")
    with pytest.raises(ValueError, match="points must be a list or tuple"):
        ss.derivatives(XS_OK, YS_OK, None)

    for bad in BAD_SCALARS:
        with pytest.raises(ValueError):
            ss.values(XS_OK, YS_OK, [bad])
        with pytest.raises(ValueError):
            ss.derivatives(XS_OK, YS_OK, [bad])


def test_inside_range_limits_accepted_outside_refused():
    lo, hi = XS_OK[0], XS_OK[-1]
    just_below = math.nextafter(lo, -math.inf)
    just_above = math.nextafter(hi, math.inf)

    ss.values(XS_OK, YS_OK, [lo, hi])
    ss.derivatives(XS_OK, YS_OK, [lo, hi])
    ss.integral(XS_OK, YS_OK, lo, hi)

    with pytest.raises(ValueError, match="not extrapolated"):
        ss.values(XS_OK, YS_OK, [just_below])
    with pytest.raises(ValueError, match="not extrapolated"):
        ss.values(XS_OK, YS_OK, [just_above])
    with pytest.raises(ValueError, match="not extrapolated"):
        ss.integral(XS_OK, YS_OK, just_below, 1.0)
    with pytest.raises(ValueError, match="not extrapolated"):
        ss.integral(XS_OK, YS_OK, 1.0, just_above)


def test_too_large_result_branch():
    xs = [0, 1e-300, 2e-300]
    ys = [0, 1e100, 0]
    ss.values(xs, ys, [1e-300])  # documented as fine
    with pytest.raises(ValueError, match="too large"):
        ss.second_derivatives(xs, ys)
