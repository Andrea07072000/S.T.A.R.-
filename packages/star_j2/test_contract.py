"""Refusals of star_j2 with hostile inputs (NaN, inf, huge integers, booleans, text, impossible orbits).
Verifies: R4 (README).

Every function returns a finite float or raises ValueError: never NaN, never a rate for an orbit that cannot exist."""
import math
from fractions import Fraction

import pytest

import star_j2 as j

NAN, INF = float("nan"), float("inf")
BAD = [NAN, INF, -INF, 10 ** 400, -10 ** 400, 1e300, -1e300, True, False, "1", None, 1j, [1.0], (1.0,)]
RATES = (j.raan_rate_deg_day, j.argp_rate_deg_day, j.mean_anomaly_rate_deg_day, j.nodal_period_s)
GOOD = (7000.0, 0.01, 51.6)


def test_the_hostile_set_and_the_constants_are_pinned():
    assert len(BAD) == 14 and j.__version__ == "0.1.0" and len(RATES) == 4
    assert (j.MU, j.RE, j.J2, j.DAY_S, j.TROPICAL_YEAR_DAYS) == (398600.4418, 6378.137, 1.082626683e-3, 86400.0, 365.2421897)
    assert j.__all__ == ["raan_rate_deg_day", "argp_rate_deg_day", "mean_anomaly_rate_deg_day", "nodal_period_s",
                         "sun_synchronous_inclination_deg", "CRITICAL_INCLINATION_DEG"]
    assert j.CRITICAL_INCLINATION_DEG == pytest.approx(63.43494882292201, abs=1e-12)


@pytest.mark.parametrize("f", RATES)
def test_every_argument_and_constant_refuses_every_hostile_value(f):
    assert isinstance(f(*GOOD), float) and math.isfinite(f(*GOOD))
    for bad in BAD:
        for i in range(3):
            args = list(GOOD)
            args[i] = bad
            with pytest.raises(ValueError):
                f(*args)
        for key in ("mu", "re", "j2"):
            with pytest.raises(ValueError):
                f(*GOOD, **{key: bad})


def test_sun_synchronous_refuses_hostile_values():
    for bad in BAD:
        with pytest.raises(ValueError):
            j.sun_synchronous_inclination_deg(bad)
        with pytest.raises(ValueError):
            j.sun_synchronous_inclination_deg(7000.0, bad)
        for key in ("mu", "re", "j2"):
            with pytest.raises(ValueError):
                j.sun_synchronous_inclination_deg(7000.0, 0.0, **{key: bad})


@pytest.mark.parametrize("a, e, inc, why", [
    (0.0, 0.0, 50, "semi-major axis"), (-7000.0, 0.0, 50, "semi-major axis"), (7000.0, -1e-9, 50, "eccentricity"),
    (7000.0, 1.0, 50, "eccentricity"), (7000.0, 1.5, 50, "eccentricity"), (6378.136, 0.0, 50, "perigee"),
    (7000.0, 0.09, 50, "perigee"), (7000.0, 0.0, -1e-9, "inclination"), (7000.0, 0.0, 180.000001, "inclination")])
def test_impossible_orbits_are_refused(a, e, inc, why):
    for f in RATES:
        with pytest.raises(ValueError, match=why):
            f(a, e, inc)


@pytest.mark.parametrize("key", ["mu", "re", "j2"])
def test_constants_must_be_positive(key):
    for bad in (0, 0.0, -0.0, -1.0, -1e-300):
        for f in RATES:
            with pytest.raises(ValueError, match="positive"):
                f(*GOOD, **{key: bad})
        with pytest.raises(ValueError, match="positive"):
            j.sun_synchronous_inclination_deg(7000.0, **{key: bad})


def test_limits_and_the_orbit_too_high_to_be_sun_synchronous():
    for args in ((6378.137, 0.0, 0.0), (6378.137, 0.0, 180.0), (1e9, 0.99, 90), (7000, 0, 51), (Fraction(7000), 0, Fraction(103, 2))):
        for f in RATES:
            assert math.isfinite(f(*args))
    assert j.raan_rate_deg_day(7000, 0, 51) == j.raan_rate_deg_day(7000.0, 0.0, 51.0)
    with pytest.raises(ValueError, match="too high"):
        j.sun_synchronous_inclination_deg(12400.0)
    with pytest.raises(ValueError, match="too high"):
        j.sun_synchronous_inclination_deg(42164.0)
    with pytest.raises(ValueError, match="perigee"):
        j.sun_synchronous_inclination_deg(6000.0)
    with pytest.raises(ValueError, match="eccentricity"):
        j.sun_synchronous_inclination_deg(7000.0, 1.0)
    assert 90.0 < j.sun_synchronous_inclination_deg(6378.137) < 180.0
