# SPDX-License-Identifier: Apache-2.0
"""Tests written from mutation survivors (12_EVIDENCE/mutation/star_orbit_20261004.json, score 0.64): GMST, Sun direction,
the J2 acceleration, the physical constants and the state properties were never checked against an independent value.
Oracles: ERFA gmst82 and astropy get_sun frozen in fixtures/reference.json (generator: fixtures/make_reference.py), the
J2 acceleration against a numerical gradient of the J2 potential, constants against their published values.
Verifies: R1 (README)."""
import json
import math
from datetime import datetime
from pathlib import Path

import pytest

from star_orbit import core

REF = json.loads((Path(__file__).parent / "fixtures" / "reference.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("c", REF["cases"], ids=[c["utc"][:10] for c in REF["cases"]])
def test_gmst_matches_erfa_gmst82(c):
    # core uses the linear IAU formula (no T^2, T^3 terms): agreement with full gmst82 within 1e-4 deg over 1990..2035
    g = math.degrees(core.compute_gmst_rad(datetime.fromisoformat(c["utc"])))
    d = (g - c["gmst82_deg"] + 180.0) % 360.0 - 180.0
    assert abs(d) < 1e-4, (c["utc"], g, c["gmst82_deg"])


@pytest.mark.parametrize("c", REF["cases"], ids=[c["utc"][:10] for c in REF["cases"]])
def test_sun_direction_matches_astropy_within_low_precision_bound(c):
    # Astronomical Almanac low-precision Sun: ~0.01 deg; the frame difference (mean-of-date vs GCRS, precession up to
    # ~0.5 deg in 35 years) is part of the documented approximation, so the bound is 0.6 deg
    u = core.compute_sun_vector_eci(datetime.fromisoformat(c["utc"]))
    assert abs(math.sqrt(sum(x * x for x in u)) - 1.0) < 1e-12
    ang = math.degrees(math.acos(max(-1.0, min(1.0, sum(a * b for a, b in zip(u, c["sun_unit_gcrs"]))))))
    assert ang < 0.6, (c["utc"], ang)


def test_sun_direction_at_j2000_is_tight():
    c = next(c for c in REF["cases"] if c["utc"].startswith("2000-01-01"))
    u = core.compute_sun_vector_eci(datetime.fromisoformat(c["utc"]))
    ang = math.degrees(math.acos(sum(a * b for a, b in zip(u, c["sun_unit_gcrs"]))))
    assert ang < 0.02, ang          # no precession at J2000: only the 0.01 deg formula error remains


def _u_j2(r):
    x, y, z = r
    rm = math.sqrt(x * x + y * y + z * z)
    return -core.MU_EARTH * core.J2_EARTH * core.R_EARTH ** 2 / (2 * rm ** 3) * (3 * z * z / (rm * rm) - 1)


@pytest.mark.parametrize("r", [(7.0e6, 0.0, 0.0), (4.0e6, 3.0e6, 5.0e6), (-2.0e6, 6.5e6, -1.5e6), (1.0e5, 2.0e5, 7.1e6)])
def test_j2_acceleration_is_the_gradient_of_the_j2_potential(r):
    # _u_j2 is the J2 term of the gravitational POTENTIAL V = mu/r [1 - J2 (Re/r)^2 P2(sin phi)], so a_J2 = +grad V
    # (first draft used -grad: the test was wrong, not the code — an equatorial point must feel an extra INWARD pull)
    h = 1.0
    num = []
    for k in range(3):
        rp, rm_ = list(r), list(r)
        rp[k] += h
        rm_[k] -= h
        num.append((_u_j2(rp) - _u_j2(rm_)) / (2 * h))
    a = core.accel_j2_zonal(r)
    if r[2] == 0.0:
        assert a[0] * r[0] < 0                         # physical sanity: equatorial J2 pull points inward
    for x, y in zip(a, num):
        # central difference with h = 1 m at 7000 km: error ~1e-8 of the vector norm (small polar x/y need the norm scale)
        assert abs(x - y) < 1e-7 * math.sqrt(sum(v * v for v in num)), (a, num)


def test_constants_are_the_published_values():
    assert core.MU_EARTH == 3.986004418e14            # IERS 2010 / WGS-84 GM
    assert core.R_EARTH == 6378137.0                  # WGS-84 a
    assert core.OMEGA_EARTH == 7.2921159e-5           # IERS 2010 nominal mean rate
    assert core.AU_METERS == 1.495978707e11           # IAU 2012 Resolution B2
    assert core.SPEED_OF_LIGHT == 299792458.0         # SI definition
    assert core.J2_EARTH == 1.08262668e-3             # EGM-96 class value used by Vallado
    assert core.P_RAD_1AU == 4.56e-6                  # 1361 W/m^2 / c, rounded


def test_default_spacecraft_properties():
    p = core.SpacecraftProperties()
    assert (p.mass_kg, p.drag_area_m2, p.drag_coeff, p.srp_area_m2, p.srp_coeff) == (1000.0, 5.0, 2.2, 5.0, 1.8)


def test_state_properties_on_distinct_components():
    s = core.OrbitState(datetime.fromisoformat("2026-01-01T00:00:00+00:00"), (1.0e6, 2.0e6, 6.0e6), (1.0e3, -7.0e3, 2.0e3))
    assert s.radius == math.sqrt(1e12 + 4e12 + 36e12) and s.speed == math.sqrt(1e6 + 49e6 + 4e6)
    assert s.specific_energy == 0.5 * s.speed ** 2 - core.MU_EARTH / s.radius
