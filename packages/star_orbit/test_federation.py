# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 S.T.A.R.
"""
test_federation.py: Automated verification suite for star_orbit federated with star_timescales.
Verifies: R1 (README).
"""

import math
from datetime import datetime, timezone
import pytest

# Ensure imports work from prototype and STAR-public

from star_timescales import LeapSecondTableError, NaiveDatetimeError, tt_minus_utc
from star_orbit import (
    OrbitState,
    propagate_orbit,
    MU_EARTH,
    R_EARTH,
    J2_EARTH,
    compute_gmst_rad,
    compute_sun_vector_eci,
)


def test_refusal_on_naive_datetime():
    """Requirement: S.T.A.R. must refuse naive datetimes without timezone."""
    naive_epoch = datetime(2026, 10, 2, 12, 0, 0)
    initial_state = OrbitState(
        epoch=naive_epoch,
        r=(7000000.0, 0.0, 0.0),
        v=(0.0, 7546.0, 0.0)
    )
    with pytest.raises(NaiveDatetimeError):
        propagate_orbit(initial_state, duration_sec=300.0)


def test_refusal_on_expired_table_epoch():
    """Requirement: S.T.A.R. must refuse epochs beyond verified leap second table."""
    future_epoch = datetime(2035, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    initial_state = OrbitState(
        epoch=future_epoch,
        r=(7000000.0, 0.0, 0.0),
        v=(0.0, 7546.0, 0.0)
    )
    with pytest.raises(LeapSecondTableError):
        propagate_orbit(initial_state, duration_sec=300.0)


def test_energy_conservation_keplerian():
    """Requirement: In pure two-body problem, relative energy error must be < 1e-7 over 1 orbit."""
    epoch = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
    r_mag = 7000000.0  # 7000 km radius
    v_circ = math.sqrt(MU_EARTH / r_mag)
    initial_state = OrbitState(
        epoch=epoch,
        r=(r_mag, 0.0, 0.0),
        v=(0.0, v_circ, 0.0)
    )
    
    period = 2.0 * math.pi * math.sqrt((r_mag**3) / MU_EARTH)
    traj = propagate_orbit(initial_state, duration_sec=period, step_sec=10.0, include_j2=False)
    
    e0 = traj[0].specific_energy
    ef = traj[-1].specific_energy
    rel_error = abs((ef - e0) / e0)
    
    assert rel_error < 1.0e-7, f"Energy drift too large: {rel_error}"
    # Circular orbit radius should return to initial value within 0.1 meters
    rf = traj[-1].radius
    assert abs(rf - r_mag) < 0.1, f"Radius drift: {abs(rf - r_mag)} meters"


def test_j2_zonal_precession():
    """
    Requirement: J2 perturbation must induce secular nodal precession matching
    analytical celestial mechanics formula within <= 1.0% relative tolerance over 10 orbits:
    dOmega/dt = -1.5 * n * J2 * (Re / p)^2 * cos(i)
    """
    epoch = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
    # Circular inclined orbit (i = 45 deg, r = 7000 km, e = 0, p = r)
    r_mag = 7000000.0
    inc = math.radians(45.0)
    v_circ = math.sqrt(MU_EARTH / r_mag)
    period = 2.0 * math.pi * math.sqrt(r_mag**3 / MU_EARTH)
    n = math.sqrt(MU_EARTH / r_mag**3)

    initial_state = OrbitState(
        epoch=epoch,
        r=(r_mag, 0.0, 0.0),
        v=(0.0, v_circ * math.cos(inc), v_circ * math.sin(inc))
    )

    # Propagate across 10 full orbits (step = 10s for high RK4 integration fidelity)
    num_orbits = 10
    duration = num_orbits * period
    traj = propagate_orbit(initial_state, duration_sec=duration, step_sec=10.0, include_j2=True)

    def extract_raan(state: OrbitState) -> float:
        rx, ry, rz = state.r
        vx, vy, vz = state.v
        # Angular momentum h = r x v
        hx = ry * vz - rz * vy
        hy = rz * vx - rx * vz
        # Ascending node vector N = K x h = (-hy, hx, 0)
        nx = -hy
        ny = hx
        return math.atan2(ny, nx)

    omega_0 = extract_raan(traj[0])
    omega_f = extract_raan(traj[-1])
    # Unwrapped measured precession angle
    delta_omega_measured = (omega_f - omega_0 + math.pi) % (2.0 * math.pi) - math.pi

    # Analytical first-order secular rate
    d_omega_dt_theory = -1.5 * n * J2_EARTH * ((R_EARTH / r_mag) ** 2) * math.cos(inc)
    delta_omega_theory = d_omega_dt_theory * duration

    rel_error = abs(delta_omega_measured - delta_omega_theory) / abs(delta_omega_theory)

    # Mandatory epistemic criterion: relative error <= 1.0%
    assert rel_error <= 0.01, (
        f"J2 precession mismatch: measured={delta_omega_measured:.6e} rad, "
        f"theory={delta_omega_theory:.6e} rad, rel_error={rel_error * 100:.3f}% > 1.0%"
    )


def test_time_conversions_and_sun():
    """Requirement: Exact sidereal time and Sun vector are calculated."""
    epoch = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
    gmst = compute_gmst_rad(epoch)
    assert 0.0 <= gmst <= 2.0 * math.pi
    
    sun_u = compute_sun_vector_eci(epoch)
    sun_norm = math.sqrt(sun_u[0]**2 + sun_u[1]**2 + sun_u[2]**2)
    assert abs(sun_norm - 1.0) < 1.0e-6


def test_drag_and_solar_storm_altitude_decay():
    """Requirement: Atmospheric drag decreases energy; solar storms dramatically amplify altitude loss."""
    pytest.importorskip("star_weather", reason="optional extra: drag/SRP need star_weather (not packaged yet)")
    from star_weather import SpaceWeatherIndices
    from star_orbit import SpacecraftProperties

    epoch = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
    # Low LEO orbit: 300 km altitude (where drag is strong)
    r_mag = R_EARTH + 300000.0
    v_circ = math.sqrt(MU_EARTH / r_mag)
    initial_state = OrbitState(epoch=epoch, r=(r_mag, 0.0, 0.0), v=(0.0, v_circ, 0.0))

    # Large satellite cross section: 20 m^2, mass 500 kg
    props = SpacecraftProperties(mass_kg=500.0, drag_area_m2=20.0, drag_coeff=2.2)

    # 1. Quiet Sun simulation over 2 hours
    duration = 7200.0
    quiet_weather = SpaceWeatherIndices(epoch=epoch, f107_sfu=70.0, kp_index=1.0)
    traj_quiet = propagate_orbit(
        initial_state,
        duration_sec=duration,
        step_sec=20.0,
        props=props,
        include_j2=False,
        include_drag=True,
        weather_indices=quiet_weather,
    )

    # Energy must decay (become more negative) due to drag work
    e0 = traj_quiet[0].specific_energy
    ef_quiet = traj_quiet[-1].specific_energy
    assert ef_quiet < e0, f"Drag did not dissipate energy: e0={e0}, ef={ef_quiet}"
    delta_r_quiet = traj_quiet[0].radius - traj_quiet[-1].radius
    assert delta_r_quiet > 0.0, f"Expected altitude drop, got {delta_r_quiet} m"

    # 2. Severe Solar Storm simulation: F10.7=220, Kp=8.0
    storm_weather = SpaceWeatherIndices(epoch=epoch, f107_sfu=220.0, kp_index=8.0)
    traj_storm = propagate_orbit(
        initial_state,
        duration_sec=duration,
        step_sec=20.0,
        props=props,
        include_j2=False,
        include_drag=True,
        weather_indices=storm_weather,
    )
    delta_r_storm = traj_storm[0].radius - traj_storm[-1].radius

    # Solar storm altitude decay must be at least 15x greater than quiet sun
    surge_ratio = delta_r_storm / delta_r_quiet
    assert surge_ratio > 15.0, f"Expected storm surge ratio > 15x, got {surge_ratio:.2f}x"


if __name__ == "__main__":
    print("Running star_orbit federation verification suite...")
    test_refusal_on_naive_datetime()
    print(" [PASS] test_refusal_on_naive_datetime")
    test_refusal_on_expired_table_epoch()
    print(" [PASS] test_refusal_on_expired_table_epoch")
    test_energy_conservation_keplerian()
    print(" [PASS] test_energy_conservation_keplerian")
    test_j2_zonal_precession()
    print(" [PASS] test_j2_zonal_precession")
    test_time_conversions_and_sun()
    print(" [PASS] test_time_conversions_and_sun")
    test_drag_and_solar_storm_altitude_decay()
    print(" [PASS] test_drag_and_solar_storm_altitude_decay")
    print("\nALL FEDERATION TESTS QUALIFIED (6/6 PASSED)!")


def test_requested_force_without_module_is_an_error(monkeypatch):
    import star_orbit.core as core
    monkeypatch.setattr(core, "compute_drag_acceleration", None)
    state = core.OrbitState(epoch=datetime(2026, 10, 2, tzinfo=timezone.utc), r=(7.0e6, 0.0, 0.0), v=(0.0, 7546.0, 0.0))
    with pytest.raises(RuntimeError):
        core.propagate_orbit(state, duration_sec=60.0, step_sec=10.0, include_drag=True)
