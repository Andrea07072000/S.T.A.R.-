"""Vis-viva and Hohmann transfer: published values and invalid radii.
Verifies: R1, R3 (README)."""
import pytest
import math
from star_maneuver import vis_viva, hohmann

def test_hohmann_leo_to_geo():
    result = hohmann(6678, 42164)
    assert math.isclose(result["dv_total"], 3.893, abs_tol=0.005)

def test_hohmann_symmetry():
    result1 = hohmann(6678, 42164)
    result2 = hohmann(42164, 6678)
    assert math.isclose(result1["dv_total"], result2["dv_total"], abs_tol=0.005)

def test_hohmann_same_radius():
    result = hohmann(6678, 6678)
    assert math.isclose(result["dv_total"], 0, abs_tol=0.005)

def test_hohmann_negative_input():
    with pytest.raises(ValueError):
        hohmann(-6678, 42164)
