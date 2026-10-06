"""star_wrap: the band just below -180 deg, left unguarded by the drafted tests (a surviving mutant showed it).
Verifies: R1 (README).
Written by the reviewer after the first mutation run (35/38)."""
import pytest

import star_wrap as sw


def test_just_below_minus_half_a_turn_comes_back_from_the_positive_side():
    # -180.5 is half a degree past -180: the same direction as +179.5
    assert sw.wrap180(-180.5) == 179.5
    assert sw.wrap180(-180.0000001) == pytest.approx(179.9999999, abs=1e-12)
    assert sw.wrap180(-540.5) == 179.5 and sw.wrap180(-181.0) == 179.0
    assert sw.difference(0.0, 180.5) == 179.5 and sw.difference(-180.5, 0.0) == 179.5
    for x in (-180.5, -180.999, -359.0, -181.0, 179.999, -179.999):
        assert -180.0 <= sw.wrap180(x) < 180.0
