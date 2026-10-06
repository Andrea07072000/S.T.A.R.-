"""star_coverage - what a satellite sees of a spherical Earth, and from where it is seen (S.T.A.R., 2026-10-06).
Standard library only.

For a satellite at altitude h above a sphere of radius R and a ground point that sees it at elevation e:
  central_angle_deg(h, e)   Earth-central angle between the sub-satellite point and the ground point
  nadir_angle_deg(h, e)     angle at the satellite between the nadir and the ground point
  slant_range(h, e)         distance satellite - ground point (same unit as h and R)
  coverage_fraction(h, e)   fraction of the sphere from which the satellite is at elevation >= e
  footprint_area(h, e)      area of that cap (unit of R squared)
  elevation_deg(h, lam)     elevation of the satellite from a point at central angle lam (negative below the horizon)
The three angles of the triangle centre - ground point - satellite always satisfy
  central angle + nadir angle + elevation = 90 degrees.
Default radius 6378.137 km (WGS-84 equatorial); pass radius= for another body or unit.
Model limits: a SPHERE, no refraction, no terrain, no oblateness (on the real Earth the horizon distance changes by up
to about 0.3 % with latitude). Refusals (ValueError): non-numeric, boolean or non-finite input, altitude <= 0,
radius <= 0, elevation outside [0, 90] where a minimum elevation is expected, central angle outside [0, 180].
"""
from __future__ import annotations

import math
import numbers

__all__ = ["central_angle_deg", "nadir_angle_deg", "slant_range", "coverage_fraction", "footprint_area", "elevation_deg"]
__version__ = "0.1.0"
EARTH_RADIUS_KM = 6378.137


def _num(*values) -> None:
    for v in values:
        try:
            ok = not isinstance(v, bool) and isinstance(v, numbers.Real) and -1e150 < float(v) < 1e150      # NaN fails both
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError("inputs must be finite real numbers")


def _body(altitude, radius) -> float:
    """Validated ratio R / (R + h), in (0, 1)."""
    _num(altitude, radius)
    if radius <= 0.0:
        raise ValueError("radius must be positive")
    if altitude <= 0.0:
        raise ValueError("altitude must be positive")
    ratio = radius / (radius + altitude)
    if not 0.0 < ratio < 1.0:
        raise ValueError("altitude is negligible or overwhelming against the radius: the geometry is not resolvable")
    return ratio


def _elev(min_elevation_deg) -> float:
    _num(min_elevation_deg)
    if not 0.0 <= min_elevation_deg <= 90.0:
        raise ValueError("minimum elevation must be within [0, 90] deg")
    return math.radians(min_elevation_deg)


def nadir_angle_deg(altitude: float, min_elevation_deg: float = 0.0, *, radius: float = EARTH_RADIUS_KM) -> float:
    ratio = _body(altitude, radius)
    return math.degrees(math.asin(ratio * math.cos(_elev(min_elevation_deg))))


def slant_range(altitude: float, min_elevation_deg: float = 0.0, *, radius: float = EARTH_RADIUS_KM) -> float:
    _body(altitude, radius)
    e = _elev(min_elevation_deg)
    # (R+h)^2 - R^2 cos^2 e = h (2R + h) + R^2 sin^2 e, and the difference sqrt(...) - R sin e is rationalised:
    # written with R + h the altitude loses its digits when it is small (measured: 1.7e-7 relative at h = 1 mm)
    k = altitude * (2.0 * radius + altitude)
    rs = radius * math.sin(e)
    return k / (math.sqrt(k + rs * rs) + rs)


def central_angle_deg(altitude: float, min_elevation_deg: float = 0.0, *, radius: float = EARTH_RADIUS_KM) -> float:
    rho = slant_range(altitude, min_elevation_deg, radius=radius)
    # with the ground point on the x axis the satellite is at (R + rho sin e, rho cos e): atan2 keeps full precision
    # both for a satellite skimming the ground and for one far away (an arc-sine saturates at 90 deg there)
    e = math.radians(min_elevation_deg)
    return math.degrees(math.atan2(rho * math.cos(e), radius + rho * math.sin(e)))


def coverage_fraction(altitude: float, min_elevation_deg: float = 0.0, *, radius: float = EARTH_RADIUS_KM) -> float:
    lam = math.radians(central_angle_deg(altitude, min_elevation_deg, radius=radius))
    return min(0.5, math.sin(lam / 2.0) ** 2)                       # (1 - cos lam) / 2 without cancellation; never above half


def footprint_area(altitude: float, min_elevation_deg: float = 0.0, *, radius: float = EARTH_RADIUS_KM) -> float:
    fraction = coverage_fraction(altitude, min_elevation_deg, radius=radius)          # validates before radius is used
    return 4.0 * math.pi * radius * radius * fraction                                 # finite: inputs are below 1e150


def elevation_deg(altitude: float, central_angle: float, *, radius: float = EARTH_RADIUS_KM) -> float:
    _body(altitude, radius)
    _num(central_angle)
    if not 0.0 <= central_angle <= 180.0:
        raise ValueError("central angle must be within [0, 180] deg")
    lam = math.radians(central_angle)
    # cos(lam) - R/(R+h) = h/(R+h) - 2 sin^2(lam/2): no cancellation for a low satellite seen near its sub-point
    return math.degrees(math.atan2(altitude / (radius + altitude) - 2.0 * math.sin(lam / 2.0) ** 2, math.sin(lam)))
