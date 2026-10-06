"""star_coords refusals and range boundaries for every public function argument.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release."""

import math

import pytest

import star_coords as sc

HOSTILE = [
    float("nan"),
    float("inf"),
    float("-inf"),
    True,
    False,
    "1",
    None,
    1j,
    [1.0],
    (1.0,),
]


def test_pinned_constants_and_exports():
    assert sc.BIG == 1e300
    assert sc.__all__ == ["spherical_to_xyz", "xyz_to_spherical", "cylindrical_to_xyz", "xyz_to_cylindrical"]
    assert sc.__version__ == "0.1.0"


@pytest.mark.parametrize("bad", HOSTILE)
def test_spherical_to_xyz_refuses_hostile_on_each_argument(bad):
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(bad, 0.0, 1.0)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(0.0, bad, 1.0)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(0.0, 0.0, bad)


@pytest.mark.parametrize("bad", HOSTILE)
def test_xyz_to_spherical_refuses_hostile_on_each_argument(bad):
    with pytest.raises(ValueError):
        sc.xyz_to_spherical(bad, 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_spherical(0.0, bad, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_spherical(0.0, 0.0, bad)


@pytest.mark.parametrize("bad", HOSTILE)
def test_cylindrical_to_xyz_refuses_hostile_on_each_argument(bad):
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(bad, 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(1.0, bad, 0.0)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(1.0, 0.0, bad)


@pytest.mark.parametrize("bad", HOSTILE)
def test_xyz_to_cylindrical_refuses_hostile_on_each_argument(bad):
    with pytest.raises(ValueError):
        sc.xyz_to_cylindrical(bad, 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_cylindrical(0.0, bad, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_cylindrical(0.0, 0.0, bad)


def test_longitude_latitude_radius_rho_component_limits_inside_and_outside():
    eps = 1e-12

    sc.spherical_to_xyz(-360.0, 0.0, 1.0)
    sc.spherical_to_xyz(360.0, 0.0, 1.0)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(-360.0 - eps, 0.0, 1.0)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(360.0 + eps, 0.0, 1.0)

    sc.spherical_to_xyz(0.0, -90.0, 1.0)
    sc.spherical_to_xyz(0.0, 90.0, 1.0)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(0.0, -90.0 - eps, 1.0)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(0.0, 90.0 + eps, 1.0)

    sc.spherical_to_xyz(0.0, 0.0, 0.0)
    sc.spherical_to_xyz(0.0, 0.0, sc.BIG)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(0.0, 0.0, -eps)
    with pytest.raises(ValueError):
        sc.spherical_to_xyz(0.0, 0.0, sc.BIG * (1.0 + 1e-15))

    sc.cylindrical_to_xyz(0.0, 0.0, 0.0)
    sc.cylindrical_to_xyz(sc.BIG, 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(-eps, 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(sc.BIG * (1.0 + 1e-15), 0.0, 0.0)

    sc.xyz_to_spherical(-sc.BIG, 0.0, 0.0)
    sc.xyz_to_spherical(sc.BIG, 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_spherical(-sc.BIG * (1.0 + 1e-15), 0.0, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_spherical(sc.BIG * (1.0 + 1e-15), 0.0, 0.0)

    sc.xyz_to_cylindrical(0.0, -sc.BIG, 0.0)
    sc.xyz_to_cylindrical(0.0, sc.BIG, 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_cylindrical(0.0, -sc.BIG * (1.0 + 1e-15), 0.0)
    with pytest.raises(ValueError):
        sc.xyz_to_cylindrical(0.0, sc.BIG * (1.0 + 1e-15), 0.0)

    sc.cylindrical_to_xyz(1.0, -360.0, -sc.BIG)
    sc.cylindrical_to_xyz(1.0, 360.0, sc.BIG)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(1.0, -360.0 - eps, 0.0)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(1.0, 360.0 + eps, 0.0)
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(1.0, 0.0, -sc.BIG * (1.0 + 1e-15))
    with pytest.raises(ValueError):
        sc.cylindrical_to_xyz(1.0, 0.0, sc.BIG * (1.0 + 1e-15))


def test_return_ranges_and_types():
    lon, lat, r = sc.xyz_to_spherical(1.0, -1.0, 2.0)
    assert 0.0 <= lon < 360.0 and -90.0 <= lat <= 90.0 and 0.0 <= r <= math.hypot(math.hypot(1.0, 1.0), 2.0)
    assert type(lon) is float and type(lat) is float and type(r) is float

    rho, lon, z = sc.xyz_to_cylindrical(-1.0, -1.0, 2.0)
    assert rho >= 0.0 and 0.0 <= lon < 360.0 and z == 2.0
    assert type(rho) is float and type(lon) is float and type(z) is float
