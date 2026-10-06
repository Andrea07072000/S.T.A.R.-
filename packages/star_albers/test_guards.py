"""star_albers: the inverse on the sphere, the edges of the image, and the limits the drafted tests did not decide.
Verifies: R1, R4 (README).
Written by the reviewer after the first mutation run (144/178 = 0.81, below the gate): the survivors were in the
spherical branch of the inverse, in the test of the image and in the limits of the arguments."""
import math
import random

import pytest

import star_albers as sa

A = 6378137.0


def rho_sphere(lat, p):
    """Radius of a parallel on the tangent cone of a sphere (see FACTS.md): a sqrt(1 + sin^2 p - 2 sin p sin lat) / sin p."""
    s = math.sin(math.radians(p))
    return A * math.sqrt(1.0 + s * s - 2.0 * s * math.sin(math.radians(lat))) / s


def test_inverse_on_the_sphere_by_hand_and_round_trip():
    p = 40.0
    rho0 = A / math.tan(math.radians(p))
    # on the central meridian of the tangent cone y = rho0 - rho(lat): invert a hand-built point
    lat, lon = sa.albers_inverse(0.0, rho0 - rho_sphere(50.0, p), p, p, p, 5.0, A, 0.0)
    assert lat == pytest.approx(50.0, abs=1e-11) and lon == pytest.approx(5.0, abs=1e-12)
    # off the meridian: theta = n dlon, x = rho sin(theta), y = rho0 - rho cos(theta)
    n, r = math.sin(math.radians(p)), rho_sphere(-20.0, p)
    th = n * math.radians(33.0)
    lat, lon = sa.albers_inverse(r * math.sin(th), rho0 - r * math.cos(th), p, p, p, 5.0, A, 0.0)
    assert lat == pytest.approx(-20.0, abs=1e-11) and lon == pytest.approx(38.0, abs=1e-11)
    rnd = random.Random(3)
    for _ in range(100):
        s = rnd.choice((-1, 1))
        la, lo, lon0 = s * rnd.uniform(-60, 85), rnd.uniform(-60, 60), rnd.uniform(-100, 100)
        xy = sa.albers_forward(la, lon0 + lo, s * 30.0, s * 50.0, s * 10.0, lon0, A, 0.0)
        back = sa.albers_inverse(*xy, s * 30.0, s * 50.0, s * 10.0, lon0, A, 0.0)
        assert back[0] == pytest.approx(la, abs=1e-10) and back[1] == pytest.approx(lon0 + lo, abs=1e-9)


def test_the_edge_of_the_image():
    p = 40.0
    rho0 = A / math.tan(math.radians(p))
    for f in (0.0, sa.WGS84_F):
        for lat in (89.0, -89.0):                           # the limit latitude itself comes back
            xy = sa.albers_forward(lat, 12.0, 29.5, 45.5, 23.0, -96.0, A, f)
            assert sa.albers_inverse(*xy, 29.5, 45.5, 23.0, -96.0, A, f)[0] == pytest.approx(lat, abs=1e-7)
    # half a degree past the limit, built by hand on the sphere: refused
    for lat in (89.5, -89.5):
        with pytest.raises(ValueError, match="outside the image"):
            sa.albers_inverse(0.0, rho0 - rho_sphere(lat, p), p, p, p, 0.0, A, 0.0)
    # a legitimate radius (that of latitude 50) on the far side of the apex: the longitude would be 180 / n > 180 deg away
    with pytest.raises(ValueError, match="outside the image"):
        sa.albers_inverse(0.0, rho0 + rho_sphere(50.0, p), p, p, p, 0.0, A, 0.0)
    # just this side of it, 179 deg from the central meridian, the point exists
    n, r = math.sin(math.radians(p)), rho_sphere(50.0, p)
    th = n * math.radians(179.0)
    lat, lon = sa.albers_inverse(r * math.sin(th), rho0 - r * math.cos(th), p, p, p, 0.0, A, 0.0)
    assert lat == pytest.approx(50.0, abs=1e-10) and lon == pytest.approx(179.0, abs=1e-9)


def test_longitude_difference_close_to_half_a_turn():
    p = 40.0
    n, r, rho0 = math.sin(math.radians(p)), rho_sphere(10.0, p), A / math.tan(math.radians(p))
    for lon0, lon, d in ((0.0, 179.5, 179.5), (0.0, -179.5, -179.5), (170.0, -10.5, 179.5), (-170.0, 10.5, -179.5)):
        x, y = sa.albers_forward(10.0, lon, p, p, p, lon0, A, 0.0)
        th = n * math.radians(d)
        assert x == pytest.approx(r * math.sin(th), abs=1e-6) and y == pytest.approx(rho0 - r * math.cos(th), abs=1e-6)
        back = sa.albers_inverse(x, y, p, p, p, lon0, A, 0.0)
        assert -180.0 <= back[1] < 180.0 and abs((back[1] - lon + 180.0) % 360.0 - 180.0) < 1e-9


def test_limits_of_the_cone_and_of_the_arguments():
    ok = (35.0, -75.0, 29.5, 45.5, 23.0, -96.0)
    assert sa.albers_scale(10.0, 0.5, 1.5)[1] > 0.0 and sa.albers_scale(10.0, -0.5, -1.5)[1] > 0.0     # low parallels are a valid cone
    assert sa.albers_scale(10.0, sa.MIN_PARALLEL, 10.0)[1] > 0.0 and sa.albers_scale(-10.0, -sa.MIN_PARALLEL, -10.0)[1] > 0.0
    for p1, p2 in ((0.000999, 10.0), (10.0, 0.000999), (-0.000999, -10.0), (0.0, 10.0), (10.0, -10.0), (-1e-3, 1e-3)):
        with pytest.raises(ValueError, match="standard parallels"):
            sa.albers_scale(10.0, p1, p2)
    for lat0, lon0 in ((89.0, 180.0), (-89.0, -180.0)):
        assert all(math.isfinite(v) for v in sa.albers_forward(35.0, -75.0, 29.5, 45.5, lat0, lon0))
    for lat0, lon0, why in ((89.0000001, 0.0, "origin"), (-89.0000001, 0.0, "origin"), (0.0, 180.0000001, "central meridian"), (0.0, -180.0000001, "central meridian")):
        with pytest.raises(ValueError, match=why):
            sa.albers_forward(35.0, -75.0, 29.5, 45.5, lat0, lon0)
        with pytest.raises(ValueError, match=why):
            sa.albers_inverse(1e5, 1e5, 29.5, 45.5, lat0, lon0)
    for x, y, why in ((-10 * A - 1.0, 0.0, r"x \(m\)"), (0.0, 10 * A + 1.0, r"y \(m\)"), (10 * A + 1.0, 0.0, r"x \(m\)"), (0.0, -10 * A - 1.0, r"y \(m\)")):
        with pytest.raises(ValueError, match=why):
            sa.albers_inverse(x, y, *ok[2:])
    for x, y in ((-10.0 * A, 0.0), (0.0, 10.0 * A)):         # at the limit the argument passes and the point is then outside the image
        with pytest.raises(ValueError, match="outside the image"):
            sa.albers_inverse(x, y, *ok[2:])
