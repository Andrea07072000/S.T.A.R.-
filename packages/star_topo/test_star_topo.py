"""star_topo against a published example and against geometry that can be checked by hand.
Verifies: R1, R2, R3 (README).

Published: EPSG Guidance Note 7-2, "Geocentric/topocentric conversions" (EPSG method 9836): topocentric origin at
55 N, 5 E, h = 200 m, i.e. Xo = 3652755.3058, Yo = 319574.6799, Zo = 5201547.3536; the point X = 3771793.968,
Y = 140253.342, Z = 5124304.349 has U (east) = -189013.869, V (north) = -128642.040, W (up) = -4220.171.
The comparison with pymap3d, PROJ and PyGeodesy on 400 cases is in crosscheck_topo.py (each needs its own interpreter)."""
import math
import random

import pytest

import star_topo as t

SITE = (55.0, 5.0, 200.0)
POINT = (3771793.968, 140253.342, 5124304.349)
ENU = (-189013.869, -128642.040, -4220.171)


def close(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b)) and len(a) == len(b) == 3


def test_epsg_published_example_forward_and_reverse():
    assert close(t.ecef_to_enu(*POINT, *SITE), ENU, 1e-3)                 # printed to the millimetre
    assert close(t.enu_to_ecef(*ENU, *SITE), POINT, 1e-3)
    assert close(t.enu_to_ecef(0.0, 0.0, 0.0, *SITE), (3652755.3058, 319574.6799, 5201547.3536), 1e-4)


def test_look_angles_of_the_published_point_from_its_own_numbers():
    az, el, rng = t.ecef_to_aer(*POINT, *SITE)
    e, n, u = ENU
    assert abs(rng - math.sqrt(e * e + n * n + u * u)) < 1e-3
    assert abs(rng - math.dist(POINT, (3652755.3058, 319574.6799, 5201547.3536))) < 1e-3     # a rotation keeps lengths
    assert abs(math.sin(math.radians(el)) - u / rng) < 1e-9 and el < 0                       # below the horizon
    assert 180 < az < 270 and abs(math.tan(math.radians(az)) - e / n) < 1e-8                 # south-west quadrant


def test_axes_at_the_equator_and_at_the_poles_by_hand():
    a, b = 6378137.0, 6378137.0 * (1 - 1 / 298.257223563)
    assert close(t.ecef_to_enu(a + 7.0, 11.0, 13.0, 0.0, 0.0, 0.0), (11.0, 13.0, 7.0), 1e-9)      # E = +Y, N = +Z, U = +X
    assert close(t.ecef_to_enu(-17.0, a + 7.0, 13.0, 0.0, 90.0, 0.0), (17.0, 13.0, 7.0), 1e-8)    # E = -X, N = +Z, U = +Y
    assert close(t.ecef_to_enu(5.0, 3.0, b + 9.0, 90.0, 0.0, 0.0), (3.0, -5.0, 9.0), 1e-8)        # north pole: N = -X
    assert close(t.ecef_to_enu(5.0, 3.0, -b - 9.0, -90.0, 0.0, 0.0), (3.0, 5.0, 9.0), 1e-8)       # south pole: N = +X
    assert close(t.ecef_to_enu(a + 107.0, 0.0, 0.0, 0.0, 0.0, 100.0), (0.0, 0.0, 7.0), 1e-9)      # height moves the site up
    assert close(t.enu_to_ecef(11.0, 13.0, 7.0, 0.0, 0.0, 0.0), (a + 7.0, 11.0, 13.0), 1e-9)
    assert close(t.aer_to_ecef(0.0, 90.0, 1000.0, 0.0, 0.0, 0.0), (a + 1000.0, 0.0, 0.0), 1e-9)
    assert close(t.ecef_to_enu(a, 0.0, 0.0, 0.0, 360.0, 0.0), (0.0, 0.0, 0.0), 1e-8)              # 360 E is the prime meridian


@pytest.mark.parametrize("enu, aer", [((0, 1, 0), (0, 0, 1)), ((1, 0, 0), (90, 0, 1)), ((0, -1, 0), (180, 0, 1)),
                                      ((-1, 0, 0), (270, 0, 1)), ((0, 0, 2), (0, 90, 2)), ((0, 0, -5), (0, -90, 5)),
                                      ((3, 0, 4), (90, math.degrees(math.atan2(4, 3)), 5)),
                                      ((1, 1, 0), (45, 0, math.sqrt(2))), ((-2, 2, 0), (315, 0, math.sqrt(8))),
                                      ((1, 1, -math.sqrt(2)), (45, -45, 2))])
def test_azimuth_from_north_towards_east_elevation_from_the_horizon(enu, aer):
    assert close(t.enu_to_aer(*enu), aer, 1e-12)
    if abs(aer[1]) != 90:
        assert close(t.aer_to_enu(*aer), enu, 1e-12)


def test_azimuth_is_never_360_and_negative_azimuths_are_accepted():
    assert t.enu_to_aer(-1e-20, 1.0, 0.0) == (0.0, 0.0, 1.0)             # -1e-20 % 360 would be 360.0
    assert t.enu_to_aer(-1e-300, 1e-300, 0.0)[0] == 315.0
    assert close(t.aer_to_enu(-90.0, 0.0, 2.0), (-2.0, 0.0, 0.0), 1e-12) and close(t.aer_to_enu(360.0, 0.0, 2.0), (0.0, 2.0, 0.0), 1e-12)
    assert close(t.aer_to_enu(123.0, 90.0, 2.0), (0.0, 0.0, 2.0), 1e-12) and close(t.aer_to_enu(30.0, -90.0, 2.0), (0.0, 0.0, -2.0), 1e-12)


def test_round_trips_and_lengths_over_the_globe():
    rnd = random.Random(7)
    for _ in range(300):
        site = (rnd.uniform(-90, 90), rnd.uniform(-180, 180), rnd.uniform(-400, 9000))
        az, el, rng = rnd.uniform(0, 359.999), rnd.uniform(-89.9, 89.9), 10 ** rnd.uniform(0, 7.6)
        p = t.aer_to_ecef(az, el, rng, *site)
        s = t.enu_to_ecef(0.0, 0.0, 0.0, *site)
        assert abs(math.dist(p, s) - rng) <= 1e-9 * rng + 2e-9            # the frame change is a rigid rotation
        back = t.ecef_to_aer(*p, *site)
        assert abs(back[2] - rng) <= 1e-9 * rng + 2e-9 and abs(back[1] - el) <= 1e-7 / min(rng, 1e3) + 1e-9
        assert abs((back[0] - az + 180) % 360 - 180) * math.cos(math.radians(el)) <= 1e-7 / min(rng, 1e3) + 1e-9
        enu = t.ecef_to_enu(*p, *site)
        assert close(t.enu_to_ecef(*enu, *site), p, 1e-8)


def test_up_is_the_ellipsoid_normal_not_the_geocentric_radius():
    lat = 45.0
    x, y, z = t.enu_to_ecef(0.0, 0.0, 1000.0, lat, 0.0, 0.0)
    x0, y0, z0 = t.enu_to_ecef(0.0, 0.0, 0.0, lat, 0.0, 0.0)
    assert abs(math.degrees(math.atan2(z - z0, x - x0)) - lat) < 1e-9                  # direction of "up" = geodetic latitude
    assert abs(math.degrees(math.atan2(z0, x0)) - lat) > 0.19                          # geocentric latitude differs by ~0.19 deg
    assert close(t.ecef_to_enu(x, y, z, lat, 0.0, 1000.0), (0.0, 0.0, 0.0), 1e-8)      # which is what height means
