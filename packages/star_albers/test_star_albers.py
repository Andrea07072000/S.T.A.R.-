"""star_albers against Snyder's published numerical example and hand-derivable identities/invariants.
Verifies: R1, R2, R3 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (the area identity now tests the module, not only itself)."""
import math
import random


import star_albers as sa


def test_snyder_published_example_forward_scale_inverse():
    a = 6378206.4
    f = 1 / 294.978698214
    x, y = sa.albers_forward(35, -75, 29.5, 45.5, 23, -96, a, f)
    assert abs(x - 1885472.7) < 0.06
    assert abs(y - 1535925.0) < 0.06
    h, k = sa.albers_scale(35, 29.5, 45.5, a, f)
    assert abs(h - 1.0085173) < 6e-8
    assert abs(k - 0.9915546) < 6e-8
    lat2, lon2 = sa.albers_inverse(x, y, 29.5, 45.5, 23, -96, a, f)
    assert abs(lat2 - 35.0) < 1e-9
    assert abs(((lon2 + 75.0 + 180.0) % 360.0) - 180.0) < 1e-9


def test_origin_maps_exactly_to_zero():
    assert sa.albers_forward(23, -96, 29.5, 45.5, 23, -96) == (0.0, 0.0)


def test_equal_area_and_standard_parallels():
    for lat in (29.5, 39.0, 45.5, 60.0, 20.0):
        h, k = sa.albers_scale(lat, 29.5, 45.5)
        assert abs(h * k - 1.0) < 1e-14
    for lat in (29.5, 45.5):
        h, k = sa.albers_scale(lat, 29.5, 45.5)
        assert abs(h - 1.0) < 1e-14 and abs(k - 1.0) < 1e-14
    h39, k39 = sa.albers_scale(39.0, 29.5, 45.5)
    h60, k60 = sa.albers_scale(60.0, 29.5, 45.5)
    h20, k20 = sa.albers_scale(20.0, 29.5, 45.5)
    assert k39 < 1.0 < h39
    assert k60 > 1.0 > h60
    assert k20 > 1.0 > h20


def test_symmetry_meridian_and_monotonic_y():
    d = 12.0
    x1, y1 = sa.albers_forward(35, -96 + d, 29.5, 45.5, 23, -96)
    x2, y2 = sa.albers_forward(35, -96 - d, 29.5, 45.5, 23, -96)
    assert abs(x1 + x2) < 1e-9 and abs(y1 - y2) < 1e-9
    xm, y_low = sa.albers_forward(25, -96, 29.5, 45.5, 23, -96)
    xm2, y_high = sa.albers_forward(40, -96, 29.5, 45.5, 23, -96)
    assert xm == 0.0 and xm2 == 0.0 and y_high > y_low


def test_parallel_order_south_mirror_and_linear_in_a():
    p = (35, -75, 29.5, 45.5, 23, -96)
    x12, y12 = sa.albers_forward(*p)
    x21, y21 = sa.albers_forward(35, -75, 45.5, 29.5, 23, -96)
    assert abs(x12 - x21) < 1e-8 and abs(y12 - y21) < 1e-8
    xs, ys = sa.albers_forward(-35, -75, -29.5, -45.5, -23, -96)
    assert abs(xs - x12) < 1e-8 and abs(ys + y12) < 1e-8
    x1, y1 = sa.albers_forward(35, -75, 29.5, 45.5, 23, -96, 1000.0, sa.WGS84_F)
    x2, y2 = sa.albers_forward(35, -75, 29.5, 45.5, 23, -96, 2000.0, sa.WGS84_F)
    assert abs(x2 - 2.0 * x1) < 1e-9 and abs(y2 - 2.0 * y1) < 1e-9


def test_sphere_tangent_cone_hand_formulas():
    # Derivation (sphere f=0, tangent cone lat1=lat2=p):
    # n=sin(p), rho(lat)=a*sqrt(1+sin^2(p)-2 sin(p) sin(lat))/sin(p),
    # central meridian: x=0, y=rho(lat0)-rho(lat), rho(p)=a/tan(p).
    a = 6378137.0
    p = 40.0
    lat0 = 40.0
    lat = 50.0
    n = math.sin(math.radians(p))
    rho0 = a * math.sqrt(1 + n * n - 2 * n * math.sin(math.radians(lat0))) / n
    rho = a * math.sqrt(1 + n * n - 2 * n * math.sin(math.radians(lat))) / n
    x, y = sa.albers_forward(lat, 0.0, p, p, lat0, 0.0, a, 0.0)
    assert abs(x) < 1e-12
    assert abs(y - (rho0 - rho)) < 1e-7
    assert abs((a / math.tan(math.radians(p))) - (a * math.sqrt(1 - n * n) / n)) < 1e-9
    dlon = 15.0
    xo, yo = sa.albers_forward(lat, dlon, p, p, lat0, 0.0, a, 0.0)
    theta = n * math.radians(dlon)
    assert abs(xo - rho * math.sin(theta)) < 1e-7
    assert abs(yo - (rho0 - rho * math.cos(theta))) < 1e-7


def test_sphere_small_cell_area_identity_exact_formula():
    # Sphere identity by hand:
    # cell area = a^2 dlon (sin(lat_b)-sin(lat_a))
    # image area (annular sector) = (n dlon / 2) (rho_a^2-rho_b^2)
    a = 6378137.0
    p = 40.0
    n = math.sin(math.radians(p))
    lat_a, lat_b = 10.0, 10.2
    dlon = math.radians(0.3)
    def rho(lat):
        return a * math.sqrt(1 + n * n - 2 * n * math.sin(math.radians(lat))) / n
    lhs = a * a * dlon * (math.sin(math.radians(lat_b)) - math.sin(math.radians(lat_a)))
    rhs = (n * dlon / 2.0) * (rho(lat_a) ** 2 - rho(lat_b) ** 2)
    assert abs(lhs - rhs) < 1e-12 * lhs                     # the identity itself (7e8 m2: an absolute bound is meaningless)
    # and the MODULE obeys it: the radii of the two parallels come from albers_forward on the central meridian of the tangent cone
    rho0 = a / math.tan(math.radians(p))
    ra = rho0 - sa.albers_forward(lat_a, 0.0, p, p, p, 0.0, a, 0.0)[1]
    rb = rho0 - sa.albers_forward(lat_b, 0.0, p, p, p, 0.0, a, 0.0)[1]
    assert abs((n * dlon / 2.0) * (ra ** 2 - rb ** 2) - lhs) < 1e-9 * lhs


def test_dateline_wrapping_equivalence_and_inverse_range():
    p1 = sa.albers_forward(10, -179, 29.5, 45.5, 23, 179)
    p2 = sa.albers_forward(10, 2, 29.5, 45.5, 23, 0)
    assert abs(p1[0] - p2[0]) < 1e-9 and abs(p1[1] - p2[1]) < 1e-9
    lat, lon = sa.albers_inverse(*p1, 29.5, 45.5, 23, 179)
    assert -180.0 <= lon < 180.0 and abs(lat - 10.0) < 1e-9


def test_forward_inverse_roundtrip_domain():
    rnd = random.Random(7)
    for _ in range(200):
        lat = rnd.uniform(-60, 85)
        dlon = rnd.uniform(-60, 60)
        lon0 = rnd.uniform(-180, 180)
        lon = ((lon0 + dlon + 180) % 360) - 180
        x, y = sa.albers_forward(lat, lon, 29.5, 45.5, 23, lon0)
        lat2, lon2 = sa.albers_inverse(x, y, 29.5, 45.5, 23, lon0)
        assert abs(lat2 - lat) < 1e-9
        assert abs(((lon2 - lon + 180) % 360) - 180) * math.cos(math.radians(lat)) < 1e-9
