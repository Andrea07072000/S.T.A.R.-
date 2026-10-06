"""star_mercator: the default arguments, left undecided by the drafted tests (two surviving mutants changed them).
Verifies: R1, R2 (README).
Written by the reviewer after the mutation run (153/163)."""
import star_mercator as sm


def test_defaults_are_the_equatorial_projection_on_wgs84_about_greenwich():
    explicit = sm.mercator_forward(30.0, 40.0, 0.0, 0.0, sm.WGS84_A, sm.WGS84_F)
    assert sm.mercator_forward(30.0, 40.0) == explicit
    assert sm.mercator_forward(30.0, 40.0, 0.0, 1.0) != explicit            # one degree of true scale shrinks the map by 1.5e-4
    assert sm.mercator_inverse(*explicit) == sm.mercator_inverse(*explicit, 0.0, 0.0, sm.WGS84_A, sm.WGS84_F)
    assert sm.mercator_scale(30.0) == sm.mercator_scale(30.0, 0.0, sm.WGS84_F) != sm.mercator_scale(30.0, 1.0)
    assert sm.mercator_scale(0.0) == 1.0
