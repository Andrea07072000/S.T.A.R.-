"""Guard tests of star_era added by the reviewer on 2026-10-07 (version 0.1.1), after the mutation runner was corrected and
the package re-measured at 0.83, below the present 0.85 gate: the reduction to [0, 360) is now one function and is
tested at its edges, and the two-part date is tested in both orders."""
import math

import pytest

import star_era as s


def test_reduction_to_one_turn_at_its_edges():
    assert s._wrap360(0.0) == 0.0 and s._wrap360(360.0) == 0.0 and s._wrap360(720.0) == 0.0 and s._wrap360(-360.0) == 0.0
    assert s._wrap360(-1e-20) == 0.0                         # Python: -1e-20 % 360.0 == 360.0, which must not be returned
    assert (-1e-20) % 360.0 == 360.0                         # the fact the function exists for
    assert s._wrap360(-1e-300) == 0.0 and s._wrap360(-5e-324) == 0.0
    below = math.nextafter(360.0, 0.0)
    assert s._wrap360(below) == below and s._wrap360(below + 360.0) < 360.0
    assert s._wrap360(-90.0) == 270.0 and s._wrap360(725.5) == 5.5 and s._wrap360(359.5) == 359.5 and s._wrap360(1.0) == 1.0
    assert s._wrap360(-1.0) == 359.0 and s._wrap360(361.0) == 1.0 and s._wrap360(-0.0) == 0.0
    for x in (-1e9, -725.25, -1e-9, 0.0, 1e-9, 359.9999999, 360.0000001, 1e9):
        assert 0.0 <= s._wrap360(x) < 360.0


def test_results_are_always_inside_one_turn():
    for k in range(400):
        day = 2378496.5 + k * 365.25                         # from 1800 to 2200
        for frac in (0.0, 0.25, 0.5, 0.999999):
            if day + frac > 2524593.5:
                continue
            e = s.era_deg(day, frac)
            g = s.gmst06_deg(day, frac, day, frac + 0.0008)
            assert 0.0 <= e < 360.0 and 0.0 <= g < 360.0 and type(e) is float and type(g) is float


def test_the_two_parts_of_a_date_may_be_given_in_either_order_or_split():
    for day, frac in ((2451545.0, 0.0), (2460000.5, 0.25), (2400000.5, 54388.0), (2415020.0, 0.3125)):
        a = s.era_deg(day, frac)
        assert s.era_deg(frac, day) == pytest.approx(a, abs=1e-9)                     # the larger part is found, not assumed first
        assert s.era_deg(day + frac) == pytest.approx(a, abs=1e-6)                    # one float loses digits: that is why two parts exist
        assert s.era_deg(day - 0.5, frac + 0.5) == pytest.approx(a, abs=1e-9)
        whole = s.era_deg(day + 1.0, frac)                                            # one day later: 0.00273781191135448 turn further
        assert (whole - a) % 360.0 == pytest.approx(360.0 * 0.00273781191135448, abs=1e-9)
    half = 2451545.0 / 2
    assert s.era_deg(half, half) == pytest.approx(s.era_deg(2451545.0, 0.0), abs=1e-9)   # two equal parts: either may be taken as the large one


def test_version_and_exports():
    assert s.__version__ == "0.1.1" and s.__all__ == ["era_deg", "gmst06_deg"]
