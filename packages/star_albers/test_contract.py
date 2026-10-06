"""Refusals and range limits for every public argument of star_albers, and pinned constants.
Verifies: R4 (README).
Drafted from FACTS.md (2026-10-06) and reviewed and corrected before release (the area identity now tests the module, not only itself)."""
import math

import pytest

import star_albers as sa

BAD = [float("nan"), float("inf"), float("-inf"), 10 ** 400, -10 ** 400, True, False, "1", None, 1j, [1.0], (1.0,)]


def test_pinned_constants_and_exports():
    assert sa.WGS84_A == 6378137.0
    assert sa.WGS84_F == 1 / 298.257223563
    assert sa.MAX_LAT == 89.0
    assert sa.MIN_PARALLEL == 1e-3
    assert sa.__all__ == ["albers_forward", "albers_inverse", "albers_scale", "WGS84_A", "WGS84_F"]


@pytest.mark.parametrize("bad", BAD)
def test_all_public_arguments_refuse_hostile_values(bad):
    with pytest.raises(ValueError):
        sa.albers_forward(bad, 0, 29.5, 45.5, 23, 0)
    with pytest.raises(ValueError):
        sa.albers_forward(10, bad, 29.5, 45.5, 23, 0)
    with pytest.raises(ValueError):
        sa.albers_forward(10, 0, bad, 45.5, 23, 0)
    with pytest.raises(ValueError):
        sa.albers_forward(10, 0, 29.5, bad, 23, 0)
    with pytest.raises(ValueError):
        sa.albers_forward(10, 0, 29.5, 45.5, bad, 0)
    with pytest.raises(ValueError):
        sa.albers_forward(10, 0, 29.5, 45.5, 23, bad)
    with pytest.raises(ValueError):
        sa.albers_forward(10, 0, 29.5, 45.5, 23, 0, bad, sa.WGS84_F)
    with pytest.raises(ValueError):
        sa.albers_forward(10, 0, 29.5, 45.5, 23, 0, sa.WGS84_A, bad)
    with pytest.raises(ValueError):
        sa.albers_inverse(bad, 0, 29.5, 45.5, 23, 0)
    with pytest.raises(ValueError):
        sa.albers_inverse(0, bad, 29.5, 45.5, 23, 0)
    with pytest.raises(ValueError):
        sa.albers_scale(bad, 29.5, 45.5)


def test_standard_parallel_refusals_and_message():
    with pytest.raises(ValueError, match="standard parallels"):
        sa.albers_forward(10, 0, 29.5, -45.5, 23, 0)
    with pytest.raises(ValueError, match="standard parallels"):
        sa.albers_forward(10, 0, 0.0, 0.0, 23, 0)
    with pytest.raises(ValueError, match="standard parallels"):
        sa.albers_forward(10, 0, 0.0005, 10.0, 23, 0)


@pytest.mark.parametrize("lat", [89.0, -89.0, 89.0000001, -89.0000001])
def test_latitude_limits(lat):
    if abs(lat) <= 89.0:
        sa.albers_forward(lat, 0, 29.5, 45.5, 23, 0)
    else:
        with pytest.raises(ValueError):
            sa.albers_forward(lat, 0, 29.5, 45.5, 23, 0)


@pytest.mark.parametrize("lon", [180.0, -180.0, 180.0000001, -180.0000001])
def test_longitude_limits(lon):
    if abs(lon) <= 180.0:
        sa.albers_forward(10, lon, 29.5, 45.5, 23, 0)
    else:
        with pytest.raises(ValueError):
            sa.albers_forward(10, lon, 29.5, 45.5, 23, 0)


def test_a_and_f_limits():
    sa.albers_forward(10, 0, 29.5, 45.5, 23, 0, 1e3, 0.0)
    sa.albers_forward(10, 0, 29.5, 45.5, 23, 0, 1e9, 0.1)
    for a in (999.999999, 1e9 + 1):
        with pytest.raises(ValueError):
            sa.albers_forward(10, 0, 29.5, 45.5, 23, 0, a, sa.WGS84_F)
    for f in (-1e-15, 0.1000000001):
        with pytest.raises(ValueError):
            sa.albers_forward(10, 0, 29.5, 45.5, 23, 0, sa.WGS84_A, f)


def test_inverse_refuses_outside_image_and_xy_bounds():
    with pytest.raises(ValueError, match="outside the image"):
        sa.albers_inverse(0, 5e7, 29.5, 45.5, 23, -96)
    a = sa.WGS84_A
    # at the limit of the plane the argument is accepted and the point is then refused as outside the image of the cone;
    # one metre beyond, the argument itself is refused
    with pytest.raises(ValueError, match="outside the image"):
        sa.albers_inverse(10 * a, 0.0, 29.5, 45.5, 23, -96)
    with pytest.raises(ValueError, match="outside the image"):
        sa.albers_inverse(0.0, -10 * a, 29.5, 45.5, 23, -96)
    with pytest.raises(ValueError, match="x"):
        sa.albers_inverse(10 * a + 1.0, 0.0, 29.5, 45.5, 23, -96)
    with pytest.raises(ValueError, match="y"):
        sa.albers_inverse(0.0, -10 * a - 1.0, 29.5, 45.5, 23, -96)


def test_tangent_and_secant_branches_and_n_sign():
    x_t, y_t = sa.albers_forward(30, 10, 30, 30, 20, 0)
    x_s, y_s = sa.albers_forward(30, 10, 29.5, 45.5, 23, 0)
    assert math.isfinite(x_t) and math.isfinite(y_t) and math.isfinite(x_s) and math.isfinite(y_s)
    xn, yn = sa.albers_forward(35, 10, 29.5, 45.5, 23, 0)
    xs, ys = sa.albers_forward(-35, 10, -29.5, -45.5, -23, 0)
    assert xn * xs > 0 and yn * ys < 0
