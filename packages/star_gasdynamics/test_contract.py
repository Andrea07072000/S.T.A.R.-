"""Refusals and inclusive limits of every public star_gasdynamics argument.

The hostile values are pinned here: non-finite numbers, overflowing integers,
out-of-range finite numbers, booleans and non-real objects must raise ValueError.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release. One of its tests exposed an underflow of p02/p01 for gamma near 1, fixed in the module."""
import math
from fractions import Fraction

import pytest

import star_gasdynamics as sg

BAD = [
    float("nan"), float("inf"), float("-inf"),
    10 ** 400, -(10 ** 400), 1e300, -1e300,
    True, False, "10", None, 1j, [10.0], (1.0,),
]


def test_pinned_hostile_set_public_names_version_and_limits():
    assert len(BAD) == 14
    assert sg.__version__ == "0.1.0"
    assert sg.__all__ == [
        "isentropic", "mach_from_area_ratio", "normal_shock"
    ]
    assert (
        sg.MACH_MAX, sg.MACH_MIN_SUBSONIC, sg.GAMMA_MIN, sg.GAMMA_MAX
    ) == (50.0, 1e-6, 1.01, 3.0)
    assert sg.isentropic(2.0) == sg.isentropic(2.0, 1.4)
    assert sg.normal_shock(2.0) == sg.normal_shock(2.0, 1.4)
    # For g=7/5, A(2)=((5+2²)/6)^3/2=27/16.
    assert sg.mach_from_area_ratio(27 / 16) == sg.mach_from_area_ratio(
        27 / 16, 1.4, True
    )


@pytest.mark.parametrize(
    "function, good",
    [
        (sg.isentropic, (2.0, 1.4)),
        (sg.normal_shock, (2.0, 1.4)),
        (sg.mach_from_area_ratio, (27 / 16, 1.4, True)),
    ],
    ids=lambda item: getattr(item, "__name__", str(item)),
)
def test_every_numeric_argument_refuses_every_hostile_value(function, good):
    assert function(*good)
    count = 2 if function is sg.mach_from_area_ratio else len(good)
    for index in range(count):
        for bad in BAD:
            args = list(good)
            args[index] = bad
            with pytest.raises(ValueError):
                function(*args)


@pytest.mark.parametrize(
    "bad", [b for b in BAD if not isinstance(b, bool)] + [1, 0, "yes"],          # True and False are the two valid values
)
def test_supersonic_requires_an_actual_boolean(bad):
    with pytest.raises(ValueError, match="supersonic"):
        sg.mach_from_area_ratio(27 / 16, 1.4, bad)


@pytest.mark.parametrize(
    "function, accepted, refused, label",
    [
        (
            sg.isentropic,
            (0.0, 1e-7, 50.0 - 1e-7, 50.0),
            (-1e-7, 50.0 + 1e-7),
            "Mach number",
        ),
        (
            sg.normal_shock,
            (1.0, 1.0 + 1e-7, 50.0 - 1e-7, 50.0),
            (1.0 - 1e-7, 50.0 + 1e-7),
            "upstream Mach number",
        ),
    ],
)
def test_both_mach_limits_inside_and_outside(
    function, accepted, refused, label
):
    for mach in accepted:
        result = function(mach)
        assert all(
            isinstance(value, float)
            and (math.isfinite(value) or
                 (function is sg.isentropic and mach == 0.0
                  and value == math.inf))
            for value in result
        )
    for mach in refused:
        with pytest.raises(ValueError, match=label):
            function(mach)


@pytest.mark.parametrize(
    "function, first",
    [
        (sg.isentropic, 2.0),
        (sg.normal_shock, 2.0),
        (sg.mach_from_area_ratio, 1.0),
    ],
)
def test_both_gamma_limits_inside_and_outside(function, first):
    for gamma in (1.01, 1.01 + 1e-7, 3.0 - 1e-7, 3.0):
        result = function(first, gamma)
        if function is sg.mach_from_area_ratio:
            assert result == 1.0
        else:
            assert all(math.isfinite(value) for value in result)
    for gamma in (1.0099999, 3.0000001):
        with pytest.raises(ValueError, match="gamma"):
            function(first, gamma)


@pytest.mark.parametrize("gamma", [1.01, 1.4, 3.0])
@pytest.mark.parametrize("supersonic", [False, True])
def test_area_limits_on_each_branch_inside_and_outside(gamma, supersonic):
    far_mach = 50.0 if supersonic else 1e-6
    inner_mach = 50.0 - 1e-6 if supersonic else 1e-6 + 1e-9
    far = sg.isentropic(far_mach, gamma)[3]
    inner = sg.isentropic(inner_mach, gamma)[3]

    # The area minimum is one at M=1. Each far endpoint is the area's
    # maximum on its selected branch, obtained from the forward function.
    assert sg.mach_from_area_ratio(1.0, gamma, supersonic) == 1.0
    assert sg.mach_from_area_ratio(1.0 + 1e-7, gamma, supersonic) != 1.0
    assert sg.mach_from_area_ratio(inner, gamma, supersonic) == pytest.approx(
        inner_mach, rel=1e-8, abs=1e-10
    )
    assert sg.mach_from_area_ratio(far, gamma, supersonic) == pytest.approx(
        far_mach, rel=1e-9, abs=1e-11
    )
    for outside in (1.0 - 1e-7, far * (1.0 + 1e-7)):
        with pytest.raises(ValueError, match="area ratio"):
            sg.mach_from_area_ratio(outside, gamma, supersonic)


def test_real_non_boolean_fraction_inputs_are_accepted():
    # 1/2 is a real number, unlike every non-real member of BAD.
    assert sg.isentropic(Fraction(1, 2)) == sg.isentropic(0.5)
    assert sg.normal_shock(Fraction(2, 1)) == sg.normal_shock(2.0)
    assert sg.mach_from_area_ratio(Fraction(27, 16)) == pytest.approx(
        2.0, rel=0, abs=2e-12
    )
