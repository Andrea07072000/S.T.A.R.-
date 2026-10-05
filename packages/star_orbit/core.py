# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 S.T.A.R.
"""
star_orbit.core: Cowell high-fidelity numerical perturbation propagator
federated with star_timescales time-standard oracles.

Enforces S.T.A.R. strict domain validity:
- Refuses naive datetimes (requires timezone-aware UTC datetime).
- Refuses propagation epochs beyond verified leap-second table validity.
- Evaluates Earth J2 zonal geopotential, dynamic atmospheric drag, and Solar Radiation Pressure.
"""

import math
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional, Any

# Federated import from S.T.A.R. Core
try:
    from star_timescales import (
        julian_date,
        modified_julian_date,
        tt_minus_utc,
        tai_minus_utc,
        LeapSecondTableError,
        NaiveDatetimeError,
    )
except ImportError as err:
    raise ImportError(f"Cannot federate star_timescales: {err}")

try:
    from star_weather import (
        compute_drag_acceleration,
        compute_srp_acceleration,
        SpaceWeatherIndices,
    )
except ImportError:
    compute_drag_acceleration = None
    compute_srp_acceleration = None
    SpaceWeatherIndices = None

# ==============================================================================
# PHYSICAL CONSTANTS (WGS-84 / EGM96 / IAU)
# ==============================================================================
MU_EARTH = 3.986004418e14        # Earth gravitational parameter [m^3 / s^2]
R_EARTH = 6378137.0             # Earth equatorial radius [m]
OMEGA_EARTH = 7.2921159e-5      # Earth rotation rate [rad / s]
P_RAD_1AU = 4.56e-6             # Solar radiation pressure at 1 AU [N / m^2]
AU_METERS = 1.495978707e11      # Astronomical Unit [m]
SPEED_OF_LIGHT = 299792458.0    # Speed of light [m / s]
J2_EARTH = 1.08262668e-3        # Earth second zonal harmonic (J2)


@dataclass(frozen=True)
class SpacecraftProperties:
    mass_kg: float = 1000.0
    drag_area_m2: float = 5.0
    drag_coeff: float = 2.2
    srp_area_m2: float = 5.0
    srp_coeff: float = 1.8


@dataclass(frozen=True)
class OrbitState:
    epoch: datetime
    r: Tuple[float, float, float]  # ECI position [m]
    v: Tuple[float, float, float]  # ECI velocity [m/s]

    @property
    def radius(self) -> float:
        return math.sqrt(self.r[0]**2 + self.r[1]**2 + self.r[2]**2)

    @property
    def speed(self) -> float:
        return math.sqrt(self.v[0]**2 + self.v[1]**2 + self.v[2]**2)

    @property
    def specific_energy(self) -> float:
        return 0.5 * (self.speed**2) - (MU_EARTH / self.radius)


def compute_gmst_rad(epoch: datetime) -> float:
    """Computes Greenwich Mean Sidereal Time in radians using star_timescales Julian Date."""
    jd = julian_date(epoch)
    d = jd - 2451545.0
    # IAU GMST formula in degrees
    gmst_deg = (280.46061837 + 360.98564736629 * d) % 360.0
    return math.radians(gmst_deg)


def compute_sun_vector_eci(epoch: datetime) -> Tuple[float, float, float]:
    """Computes approximate Sun position unit vector in ECI frame for epoch."""
    jd = julian_date(epoch)
    n = jd - 2451545.0
    # Mean longitude and mean anomaly of the Sun
    L = math.radians((280.460 + 0.9856474 * n) % 360.0)
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    # Ecliptic longitude
    lambda_sun = L + math.radians(1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)  # Obliquity of ecliptic
    
    ux = math.cos(lambda_sun)
    uy = math.cos(eps) * math.sin(lambda_sun)
    uz = math.sin(eps) * math.sin(lambda_sun)
    return (ux, uy, uz)


def accel_two_body(r: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Two-body central Newtonian acceleration."""
    r_mag = math.sqrt(r[0]**2 + r[1]**2 + r[2]**2)
    factor = -MU_EARTH / (r_mag**3)
    return (factor * r[0], factor * r[1], factor * r[2])


def accel_j2_zonal(r: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Acceleration due to Earth oblateness (J2 harmonic)."""
    x, y, z = r
    r_mag = math.sqrt(x**2 + y**2 + z**2)
    r2 = r_mag**2
    z2 = z**2
    factor = (1.5 * J2_EARTH * MU_EARTH * (R_EARTH**2)) / (r_mag**5)
    
    ax = factor * x * (5.0 * z2 / r2 - 1.0)
    ay = factor * y * (5.0 * z2 / r2 - 1.0)
    az = factor * z * (5.0 * z2 / r2 - 3.0)
    return (ax, ay, az)


def total_acceleration(
    epoch: datetime,
    r: Tuple[float, float, float],
    v: Tuple[float, float, float],
    props: SpacecraftProperties,
    include_j2: bool = True,
    include_drag: bool = False,
    include_srp: bool = False,
    weather_indices: Optional[Any] = None,
) -> Tuple[float, float, float]:
    """Evaluates total instantaneous vector acceleration on the spacecraft."""
    ax, ay, az = accel_two_body(r)
    
    if include_j2:
        jx, jy, jz = accel_j2_zonal(r)
        ax += jx
        ay += jy
        az += jz

    if include_drag and compute_drag_acceleration is None:
        raise RuntimeError("include_drag=True but star_weather is not installed: refusing to silently drop the force")
    if include_drag:
        dx, dy, dz = compute_drag_acceleration(
            r_eci=r,
            v_eci=v,
            mass_kg=props.mass_kg,
            drag_area_m2=props.drag_area_m2,
            cd=props.drag_coeff,
            indices=weather_indices,
        )
        ax += dx
        ay += dy
        az += dz

    if include_srp and compute_srp_acceleration is None:
        raise RuntimeError("include_srp=True but star_weather is not installed: refusing to silently drop the force")
    if include_srp:
        sx, sy, sz = compute_srp_acceleration(
            epoch=epoch,
            r_eci=r,
            mass_kg=props.mass_kg,
            srp_area_m2=props.srp_area_m2,
            cr=props.srp_coeff,
        )
        ax += sx
        ay += sy
        az += sz
        
    return (ax, ay, az)


def rk4_step(
    epoch: datetime,
    r: Tuple[float, float, float],
    v: Tuple[float, float, float],
    dt: float,
    props: SpacecraftProperties,
    include_j2: bool = True,
    include_drag: bool = False,
    include_srp: bool = False,
    weather_indices: Optional[Any] = None,
) -> Tuple[datetime, Tuple[float, float, float], Tuple[float, float, float]]:
    """Single Runge-Kutta 4th order fixed-step integration step."""
    # k1
    k1_v = total_acceleration(epoch, r, v, props, include_j2, include_drag, include_srp, weather_indices)
    k1_r = v
    
    # k2
    half_dt = 0.5 * dt
    epoch_half = epoch + timedelta(seconds=half_dt)
    r_k2 = (r[0] + k1_r[0] * half_dt, r[1] + k1_r[1] * half_dt, r[2] + k1_r[2] * half_dt)
    v_k2 = (v[0] + k1_v[0] * half_dt, v[1] + k1_v[1] * half_dt, v[2] + k1_v[2] * half_dt)
    k2_v = total_acceleration(epoch_half, r_k2, v_k2, props, include_j2, include_drag, include_srp, weather_indices)
    k2_r = v_k2
    
    # k3
    r_k3 = (r[0] + k2_r[0] * half_dt, r[1] + k2_r[1] * half_dt, r[2] + k2_r[2] * half_dt)
    v_k3 = (v[0] + k2_v[0] * half_dt, v[1] + k2_v[1] * half_dt, v[2] + k2_v[2] * half_dt)
    k3_v = total_acceleration(epoch_half, r_k3, v_k3, props, include_j2, include_drag, include_srp, weather_indices)
    k3_r = v_k3
    
    # k4
    epoch_full = epoch + timedelta(seconds=dt)
    r_k4 = (r[0] + k3_r[0] * dt, r[1] + k3_r[1] * dt, r[2] + k3_r[2] * dt)
    v_k4 = (v[0] + k3_v[0] * dt, v[1] + k3_v[1] * dt, v[2] + k3_v[2] * dt)
    k4_v = total_acceleration(epoch_full, r_k4, v_k4, props, include_j2, include_drag, include_srp, weather_indices)
    k4_r = v_k4
    
    r_next = (
        r[0] + (dt / 6.0) * (k1_r[0] + 2.0 * k2_r[0] + 2.0 * k3_r[0] + k4_r[0]),
        r[1] + (dt / 6.0) * (k1_r[1] + 2.0 * k2_r[1] + 2.0 * k3_r[1] + k4_r[1]),
        r[2] + (dt / 6.0) * (k1_r[2] + 2.0 * k2_r[2] + 2.0 * k3_r[2] + k4_r[2]),
    )
    v_next = (
        v[0] + (dt / 6.0) * (k1_v[0] + 2.0 * k2_v[0] + 2.0 * k3_v[0] + k4_v[0]),
        v[1] + (dt / 6.0) * (k1_v[1] + 2.0 * k2_v[1] + 2.0 * k3_v[1] + k4_v[1]),
        v[2] + (dt / 6.0) * (k1_v[2] + 2.0 * k2_v[2] + 2.0 * k3_v[2] + k4_v[2]),
    )
    return (epoch_full, r_next, v_next)


def propagate_orbit(
    initial_state: OrbitState,
    duration_sec: float,
    step_sec: float = 30.0,
    props: Optional[SpacecraftProperties] = None,
    include_j2: bool = True,
    include_drag: bool = False,
    include_srp: bool = False,
    weather_indices: Optional[Any] = None,
) -> List[OrbitState]:
    """
    Propagates orbit from initial_state over duration_sec.
    Enforces star_timescales validation on start and end epochs.
    """
    if props is None:
        props = SpacecraftProperties()
        
    # Validation gate: throws NaiveDatetimeError or LeapSecondTableError if invalid
    _ = tt_minus_utc(initial_state.epoch)
    final_epoch = initial_state.epoch + timedelta(seconds=duration_sec)
    _ = tt_minus_utc(final_epoch)

    history = [initial_state]
    current_epoch = initial_state.epoch
    current_r = initial_state.r
    current_v = initial_state.v
    
    elapsed = 0.0
    while elapsed < duration_sec:
        dt = min(step_sec, duration_sec - elapsed)
        current_epoch, current_r, current_v = rk4_step(
            current_epoch, current_r, current_v, dt, props,
            include_j2=include_j2,
            include_drag=include_drag,
            include_srp=include_srp,
            weather_indices=weather_indices,
        )
        elapsed += dt
        history.append(OrbitState(epoch=current_epoch, r=current_r, v=current_v))
        
    return history
