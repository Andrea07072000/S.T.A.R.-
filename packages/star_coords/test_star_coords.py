"""star_coords behaviour from hand-derivable values, inverses, invariants and edge cases.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed before release."""

import math
import random

import pytest

import star_coords as sc


def test_hand_derived_spherical_to_xyz_values():
    # lon=0, lat=0, r=1 -> x=cos0*cos0=1, y=cos0*sin0=0, z=sin0=0
    assert sc.spherical_to_xyz(0, 0) == (1.0, 0.0, 0.0)

    # lon=60, lat=0, r=2 -> x=2*(1)*(1/2)=1, y=2*(1)*(sqrt(3)/2)=sqrt(3), z=2*0=0
    x, y, z = sc.spherical_to_xyz(60, 0, 2)
    assert x == pytest.approx(1.0, abs=2e-15)
    assert y == pytest.approx(math.sqrt(3.0), abs=2e-15)
    assert z == pytest.approx(0.0, abs=2e-15)

    # lon=90, lat=0 -> (0,1,0), with finite-precision cos(90 deg) residue allowed
    x, y, z = sc.spherical_to_xyz(90, 0)
    assert abs(x) <= 1e-16 and abs(y - 1.0) <= 1e-16 and abs(z) <= 1e-16

    # lon=0, lat=90 -> (0,0,1)
    x, y, z = sc.spherical_to_xyz(0, 90)
    assert abs(x) <= 1e-16 and abs(y) <= 1e-16 and abs(z - 1.0) <= 1e-16

    # lon=45, lat=asin(1/sqrt(3)), r=sqrt(3):
    # cos(lat)=sqrt(1-1/3)=sqrt(2/3), sin(lat)=1/sqrt(3), cos45=sin45=sqrt(2)/2
    # x=r*cos(lat)*cos45 = sqrt3*sqrt(2/3)*sqrt2/2 = 1 (same for y), z=r*sin(lat)=1
    lat = math.degrees(math.asin(1 / math.sqrt(3.0)))
    x, y, z = sc.spherical_to_xyz(45, lat, math.sqrt(3.0))
    assert x == pytest.approx(1.0, abs=1e-15)
    assert y == pytest.approx(1.0, abs=1e-15)
    assert z == pytest.approx(1.0, abs=1e-15)


def test_hand_derived_xyz_to_spherical_values_and_axis_rules():
    lon, lat, r = sc.xyz_to_spherical(1, 1, 1)
    # lat = atan(1/sqrt(2)) in degrees, lon=45, r=sqrt(3)
    assert lon == pytest.approx(45.0, abs=1e-13)
    assert lat == pytest.approx(35.264389682754654, abs=1e-13)
    assert r == pytest.approx(math.sqrt(3.0), abs=1e-13)

    assert sc.xyz_to_spherical(0, -2, 0) == (270.0, 0.0, 2.0)
    assert sc.xyz_to_spherical(-3, 0, 0) == (180.0, 0.0, 3.0)
    assert sc.xyz_to_spherical(3, 4, 0)[2] == 5.0
    assert sc.xyz_to_spherical(1, 2, 2)[2] == 3.0

    assert sc.xyz_to_spherical(0, 0, 5) == (0.0, 90.0, 5.0)
    assert sc.xyz_to_spherical(0, 0, -5) == (0.0, -90.0, 5.0)
    assert sc.xyz_to_spherical(0, 0, 0) == (0.0, 0.0, 0.0)
    assert sc.xyz_to_spherical(-0.0, -0.0, 1.0)[0] == 0.0
    assert sc.xyz_to_spherical(1.0, -1e-300, 0.0)[0] == 0.0


def test_hand_derived_cylindrical_values():
    x, y, z = sc.cylindrical_to_xyz(2, 90, 5)
    assert abs(x) <= 2e-16 and abs(y - 2.0) <= 2e-16 and z == 5.0

    assert sc.xyz_to_cylindrical(0, -2, 5) == (2.0, 270.0, 5.0)
    rho, lon, z = sc.xyz_to_cylindrical(3, 4, -1)
    assert rho == pytest.approx(5.0, abs=1e-13)
    assert lon == pytest.approx(53.13010235415598, abs=1e-13)
    assert z == -1.0
    assert sc.xyz_to_cylindrical(0, 0, -7) == (0.0, 0.0, -7.0)


def test_hypot_scaling_large_small_and_zero_radius_negative_longitude():
    assert sc.xyz_to_spherical(3e200, 4e200, 0)[2] == pytest.approx(5e200, rel=1e-15)
    assert sc.xyz_to_spherical(3e-200, 4e-200, 0)[2] == pytest.approx(5e-200, rel=1e-15)

    # r=0 annihilates all direction terms
    assert sc.spherical_to_xyz(123.0, -45.0, 0.0) == (0.0, 0.0, 0.0)

    # negative longitude accepted: lon=-90, lat=0 -> (0,-1,0)
    x, y, z = sc.spherical_to_xyz(-90, 0)
    assert abs(x) <= 1e-16 and abs(y + 1.0) <= 1e-16 and abs(z) <= 1e-16


def test_inverse_properties_with_well_conditioned_longitude_comparison():
    rnd = random.Random(7)
    for _ in range(400):
        lon = rnd.uniform(-360.0, 360.0)
        lat = rnd.uniform(-89.0, 89.0)
        r = rnd.uniform(0.0, 1e6)

        x, y, z = sc.spherical_to_xyz(lon, lat, r)
        lon2, lat2, r2 = sc.xyz_to_spherical(x, y, z)

        # longitude compared as displacement on the parallel: dlon*cos(lat)
        dlon = ((lon2 - lon + 180.0) % 360.0) - 180.0
        assert abs(dlon) * abs(math.cos(math.radians(lat))) < 1e-12
        assert abs(lat2 - lat) < 1e-12
        assert abs(r2 - r) <= max(1e-12, 1e-12 * max(1.0, r))

        rho, lonc, zc = sc.xyz_to_cylindrical(x, y, z)
        x2, y2, z2 = sc.cylindrical_to_xyz(rho, lonc, zc)
        assert abs(x2 - x) <= max(1e-12, 1e-12 * max(1.0, abs(x)))
        assert abs(y2 - y) <= max(1e-12, 1e-12 * max(1.0, abs(y)))
        assert abs(z2 - z) <= max(1e-12, 1e-12 * max(1.0, abs(z)))
