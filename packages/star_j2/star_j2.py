"""star_j2 - secular effect of the Earth's oblateness on an orbit (S.T.A.R., 2026-10-06). Standard library only.

First-order secular rates in J2 (mean elements; no J2 squared, no other harmonics, no drag):
  raan_rate_deg_day(a_km, e, inc_deg)        regression of the node          -1.5 J2 (Re/p)^2 n cos i
  argp_rate_deg_day(a_km, e, inc_deg)        rotation of the line of apsides  0.75 J2 (Re/p)^2 n (5 cos^2 i - 1)
  mean_anomaly_rate_deg_day(a_km, e, inc_deg)  n [1 + 0.75 J2 (Re/p)^2 sqrt(1 - e^2) (3 cos^2 i - 1)]
  nodal_period_s(a_km, e, inc_deg)           time between two ascending-node crossings
  sun_synchronous_inclination_deg(a_km, e=0.0)  inclination whose node follows the mean Sun (360 deg per tropical year)
  CRITICAL_INCLINATION_DEG                   63.4349...: the perigee does not rotate (5 cos^2 i = 1)
with n = sqrt(mu / a^3) and p = a (1 - e^2). Constants: EGM96/WGS-84 (mu, Re, J2), overridable by keyword.
Accuracy: the neglected terms are of relative order J2. Measured (crosscheck_j2.py): node rate within 0.31 % of Orekit's
Eckstein-Hechler theory and within 0.38 % of a numerical integration with J2; perigee rate within 0.013 deg/day.
Refusals (ValueError): non-numeric, boolean or non-finite input, a <= 0, e outside [0, 1), inclination outside
[0, 180], a perigee inside the Earth, non-positive constants, an orbit too high to be sun-synchronous.
"""
from __future__ import annotations

import math
import numbers

__all__ = ["raan_rate_deg_day", "argp_rate_deg_day", "mean_anomaly_rate_deg_day", "nodal_period_s",
           "sun_synchronous_inclination_deg", "CRITICAL_INCLINATION_DEG"]
__version__ = "0.1.0"
MU = 398600.4418                 # km^3/s^2
RE = 6378.137                    # km
J2 = 1.082626683e-3
DAY_S = 86400.0
TROPICAL_YEAR_DAYS = 365.2421897
SUN_RATE_DEG_DAY = 360.0 / TROPICAL_YEAR_DAYS
CRITICAL_INCLINATION_DEG = math.degrees(math.acos(math.sqrt(0.2)))


def _num(*values) -> None:
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e300 < float(v) < 1e300    # NaN fails both
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError("inputs must be finite real numbers")


def _common(a_km, e, mu, re, j2):
    """Mean motion (rad/s) and the factor J2 (Re/p)^2 after validating the orbit and the constants."""
    _num(a_km, e, mu, re, j2)
    if mu <= 0.0 or re <= 0.0 or j2 <= 0.0:
        raise ValueError("mu, re and j2 must be positive")
    if a_km <= 0.0:
        raise ValueError("semi-major axis must be positive")
    if not 0.0 <= e < 1.0:
        raise ValueError("eccentricity must be within [0, 1)")
    if a_km * (1.0 - e) < re:
        raise ValueError("the perigee is inside the Earth")
    p = a_km * (1.0 - e * e)
    return math.sqrt(mu / a_km) / a_km, j2 * (re / p) ** 2


def _cos_inc(inc_deg) -> float:
    _num(inc_deg)
    if not 0.0 <= inc_deg <= 180.0:
        raise ValueError("inclination must be within [0, 180] deg")
    return math.cos(math.radians(inc_deg))


def raan_rate_deg_day(a_km: float, e: float, inc_deg: float, *, mu: float = MU, re: float = RE, j2: float = J2) -> float:
    n, k = _common(a_km, e, mu, re, j2)
    return math.degrees(-1.5 * k * n * _cos_inc(inc_deg)) * DAY_S


def argp_rate_deg_day(a_km: float, e: float, inc_deg: float, *, mu: float = MU, re: float = RE, j2: float = J2) -> float:
    n, k = _common(a_km, e, mu, re, j2)
    c = _cos_inc(inc_deg)
    return math.degrees(0.75 * k * n * (5.0 * c * c - 1.0)) * DAY_S


def mean_anomaly_rate_deg_day(a_km: float, e: float, inc_deg: float, *, mu: float = MU, re: float = RE, j2: float = J2) -> float:
    n, k = _common(a_km, e, mu, re, j2)
    c = _cos_inc(inc_deg)
    return math.degrees(n * (1.0 + 0.75 * k * math.sqrt(1.0 - e * e) * (3.0 * c * c - 1.0))) * DAY_S


def nodal_period_s(a_km: float, e: float, inc_deg: float, *, mu: float = MU, re: float = RE, j2: float = J2) -> float:
    rate = mean_anomaly_rate_deg_day(a_km, e, inc_deg, mu=mu, re=re, j2=j2) + argp_rate_deg_day(a_km, e, inc_deg, mu=mu, re=re, j2=j2)
    return 360.0 / rate * DAY_S


def sun_synchronous_inclination_deg(a_km: float, e: float = 0.0, *, mu: float = MU, re: float = RE, j2: float = J2) -> float:
    n, k = _common(a_km, e, mu, re, j2)
    cos_i = -math.radians(SUN_RATE_DEG_DAY) / DAY_S / (1.5 * k * n)
    if cos_i < -1.0:
        raise ValueError("no sun-synchronous inclination exists for this orbit (too high)")
    return math.degrees(math.acos(cos_i))
