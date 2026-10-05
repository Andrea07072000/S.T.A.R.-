"""References: Vallado (4th ed.) Example 3-3 (ECEF -> geodetic, printed: 34.352496 deg, 46.4464 deg, 5085.22 km);
WGS-84 defining constants (equator point = a, pole = b = 6356752.314245 m); round trips.
Verifies: R1, R2, R3 (README)."""
import math
import random

import pytest

from star_geodesy import B, ecef_to_geodetic, geodetic_to_ecef


def test_vallado_example_3_3():
    lat, lon, h = ecef_to_geodetic(6524834.0, 6862875.0, 6448296.0)
    # Vallado prints 34.352496; the exact solution (closes the forward transform to 0 m) is 34.3524952: the printed
    # value carries ~1e-6 deg (PROJ 9.8.1 gives 34.3524954, pymap3d 3.2.0 gives 34.3524989), hence 1e-6 here.
    assert abs(lat - 34.352496) <= 1e-6 and abs(lon - 46.4464) <= 5e-5 and abs(h - 5085220.0) <= 5.0
    x, y, z = geodetic_to_ecef(lat, lon, h)
    assert max(abs(x - 6524834.0), abs(y - 6862875.0), abs(z - 6448296.0)) < 1e-6  # exact closure


def test_defining_points():
    x, y, z = geodetic_to_ecef(0, 0, 0)
    assert abs(x - 6378137.0) < 1e-9 and abs(y) < 1e-9 and abs(z) < 1e-9
    x, y, z = geodetic_to_ecef(90, 0, 0)
    assert abs(z - 6356752.314245) < 1e-6 and abs(B - 6356752.314245) < 1e-6
    assert ecef_to_geodetic(0, 0, -B - 100)[0] == -90.0


def test_round_trip_including_near_pole_and_high_altitude():
    rnd = random.Random(42)
    for _ in range(3000):
        lat = rnd.choice([rnd.uniform(-90, 90), rnd.uniform(89.99, 90), rnd.uniform(-90, -89.99)])
        lon, h = rnd.uniform(-180, 180), rnd.choice([rnd.uniform(-500, 9000), rnd.uniform(1e5, 4e7)])
        lat2, lon2, h2 = ecef_to_geodetic(*geodetic_to_ecef(lat, lon, h))
        assert abs(lat2 - lat) < 1e-9 and abs(h2 - h) < 1e-4
        if abs(lat) < 89.9999:
            assert abs(math.remainder(lon2 - lon, 360)) < 1e-9


def test_invalid_inputs():
    with pytest.raises(ValueError):
        geodetic_to_ecef(91, 0, 0)
    with pytest.raises(ValueError):
        ecef_to_geodetic(0, 0, 0)
