"""Contract tests for star_twobody: hostile values, range edges, and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md and reviewed before release."""
import math

import pytest

import star_twobody as st

HOSTILE = [float("nan"), float("inf"), float("-inf"), True, False, "10", None, 1 + 2j, [1.0]]
POS_BAD = [0.0, -1.0, -1e-9, st.TINY * 0.999999, 1e-300, 5e-324, st.BIG * 1.0000000001]
POS_GOOD = [st.TINY, 1.0, st.BIG]


def test_pinned_constants_and_exports():
    assert st.MU_EARTH == 398600.4418
    assert st.BIG == 1e30
    assert st.__all__ == [
        "period", "semi_major_axis_from_period", "mean_motion", "circular_speed", "escape_speed",
        "apsides", "elements_from_apsides", "apsis_speeds", "specific_energy", "MU_EARTH",
    ]


@pytest.mark.parametrize("f,args_idx", [
    (st.period, [0, 1]),
    (st.semi_major_axis_from_period, [0, 1]),
    (st.mean_motion, [0, 1]),
    (st.circular_speed, [0, 1]),
    (st.escape_speed, [0, 1]),
    (st.apsides, [0]),
    (st.elements_from_apsides, [0, 1]),
    (st.apsis_speeds, [0, 2]),
    (st.specific_energy, [0, 1]),
])
def test_positive_arguments_refuse_hostiles_and_bad_ranges(f, args_idx):
    base = {
        st.period: [7000.0, st.MU_EARTH],
        st.semi_major_axis_from_period: [6000.0, st.MU_EARTH],
        st.mean_motion: [7000.0, st.MU_EARTH],
        st.circular_speed: [7000.0, st.MU_EARTH],
        st.escape_speed: [7000.0, st.MU_EARTH],
        st.apsides: [10000.0, 0.2],
        st.elements_from_apsides: [8000.0, 12000.0],
        st.apsis_speeds: [10000.0, 0.2, st.MU_EARTH],
        st.specific_energy: [10000.0, st.MU_EARTH],
    }[f]
    for i in args_idx:
        for bad in HOSTILE + POS_BAD:
            args = list(base)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)


@pytest.mark.parametrize("f,args_idx", [
    (st.period, [0, 1]),
    (st.semi_major_axis_from_period, [0, 1]),
    (st.mean_motion, [0, 1]),
    (st.circular_speed, [0, 1]),
    (st.escape_speed, [0, 1]),
    (st.apsides, [0]),
    (st.elements_from_apsides, [0, 1]),
    (st.apsis_speeds, [0, 2]),
    (st.specific_energy, [0, 1]),
])
def test_positive_arguments_accept_limits(f, args_idx):
    base = {
        st.period: [7000.0, st.MU_EARTH],
        st.semi_major_axis_from_period: [6000.0, st.MU_EARTH],
        st.mean_motion: [7000.0, st.MU_EARTH],
        st.circular_speed: [7000.0, st.MU_EARTH],
        st.escape_speed: [7000.0, st.MU_EARTH],
        st.apsides: [10000.0, 0.2],
        st.elements_from_apsides: [8000.0, 12000.0],
        st.apsis_speeds: [10000.0, 0.2, st.MU_EARTH],
        st.specific_energy: [10000.0, st.MU_EARTH],
    }[f]
    for i in args_idx:
        for good in POS_GOOD:
            args = list(base)
            args[i] = good
            if f is st.elements_from_apsides:               # the two radii are ordered: put both at the limit (a circle)
                args = [good, good]
            out = f(*args)
            values = out if isinstance(out, tuple) else (out,)
            assert all(type(v) is float and v == v and abs(v) != float("inf") for v in values)
            assert all(v != 0.0 for v in values) or f is st.elements_from_apsides          # nothing underflows (a circle has e == 0)


def test_eccentricity_range_and_ellipses_only_message():
    for bad_e in [-1e-12, -0.1, 1.0, 1.0000001, float("nan"), True]:
        with pytest.raises(ValueError, match="ellipses only"):
            st.apsides(10000.0, bad_e)
        with pytest.raises(ValueError, match="ellipses only"):
            st.apsis_speeds(10000.0, bad_e, st.MU_EARTH)

    assert st.apsides(10000.0, 0.0) == pytest.approx((10000.0, 10000.0), abs=0.0)
    rp, ra = st.apsides(10000.0, 1.0 - 1e-15)
    assert rp > 0.0 and ra > rp


def test_elements_from_apsides_rounding_tolerance_branches():
    rp = 10000.0
    ra_inside = rp * (1.0 - 5e-13)   # inside tolerated rounding
    a, e = st.elements_from_apsides(rp, ra_inside)
    assert a == pytest.approx(0.5 * (rp + ra_inside), rel=1e-15)
    assert e == 0.0

    ra_outside = rp * (1.0 - 1e-9)   # outside tolerance, must refuse
    with pytest.raises(ValueError, match="apoapsis"):
        st.elements_from_apsides(rp, ra_outside)


def test_exact_limit_big_accepted_just_above_refused():
    assert math.isfinite(st.period(st.BIG, st.BIG))
    with pytest.raises(ValueError):
        st.period(st.BIG * (1.0 + 1e-15), st.BIG)
    with pytest.raises(ValueError):
        st.period(st.BIG, st.BIG * (1.0 + 1e-15))
