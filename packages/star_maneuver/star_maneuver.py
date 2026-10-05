import math

# 2026-10-05, probe of R3 with hostile inputs: vis_viva returned a COMPLEX number for r > 2a (a point beyond the
# apoapsis of the ellipse), combined_dv(7.5, nan, 0.1) returned 0.0, a negative mu produced delta-v values, and
# NaN/inf propagated silently. All are invalid input and now raise ValueError.


def _finite(*xs):
    if not all(map(math.isfinite, xs)):
        raise ValueError("inputs must be finite")


def _positive_mu(mu):
    _finite(mu)
    if mu <= 0:
        raise ValueError("mu must be positive")


def vis_viva(r_km, a_km, mu=398600.4418):
    _finite(r_km, a_km)
    _positive_mu(mu)
    if r_km <= 0 or a_km <= 0:
        raise ValueError("radii must be positive")
    if r_km > 2 * a_km:
        raise ValueError("r > 2a: the point is beyond the apoapsis of an ellipse with this semi-major axis")
    return (mu * (2 / r_km - 1 / a_km)) ** 0.5


def hohmann(r1_km, r2_km, mu=398600.4418):
    _finite(r1_km, r2_km)
    _positive_mu(mu)
    if r1_km <= 0 or r2_km <= 0:
        raise ValueError("radii must be positive")
    a_transfer = (r1_km + r2_km) / 2
    v1 = vis_viva(r1_km, a_transfer, mu)
    v2 = vis_viva(r2_km, a_transfer, mu)
    v_circular1 = vis_viva(r1_km, r1_km, mu)
    v_circular2 = vis_viva(r2_km, r2_km, mu)
    dv1 = abs(v1 - v_circular1)
    dv2 = abs(v_circular2 - v2)
    dv_total = dv1 + dv2
    tof_s = (math.pi * (a_transfer ** 3 / mu) ** 0.5)
    return {"dv1": dv1, "dv2": dv2, "dv_total": dv_total, "tof_s": tof_s}


def plane_change(v_kms, di_rad):
    """Pure inclination change at constant speed: dv = 2 v sin(di/2)."""
    _finite(v_kms, di_rad)
    if v_kms < 0:
        raise ValueError("speed must be non-negative")
    return 2 * v_kms * math.sin(abs(di_rad) / 2)


def combined_dv(v1_kms, v2_kms, di_rad):
    """Single burn changing speed v1 -> v2 and plane by di (law of cosines)."""
    _finite(v1_kms, v2_kms, di_rad)
    if v1_kms < 0 or v2_kms < 0:
        raise ValueError("speeds must be non-negative")
    return math.sqrt(max(0.0, v1_kms ** 2 + v2_kms ** 2 - 2 * v1_kms * v2_kms * math.cos(di_rad)))


def bielliptic(r1_km, r2_km, rb_km, mu=398600.4418):
    """Three-burn bi-elliptic transfer between circular coplanar orbits via apoapsis rb >= max(r1, r2)."""
    _finite(r1_km, r2_km, rb_km)
    _positive_mu(mu)
    if r1_km <= 0 or r2_km <= 0 or rb_km <= 0:
        raise ValueError("radii must be positive")
    if rb_km < max(r1_km, r2_km):
        raise ValueError("rb must be >= max(r1, r2)")
    a1, a2 = (r1_km + rb_km) / 2, (r2_km + rb_km) / 2
    dv1 = abs(vis_viva(r1_km, a1, mu) - vis_viva(r1_km, r1_km, mu))
    dv2 = abs(vis_viva(rb_km, a2, mu) - vis_viva(rb_km, a1, mu))
    dv3 = abs(vis_viva(r2_km, a2, mu) - vis_viva(r2_km, r2_km, mu))
    tof_s = math.pi * ((a1 ** 3 / mu) ** 0.5 + (a2 ** 3 / mu) ** 0.5)
    return {"dv1": dv1, "dv2": dv2, "dv3": dv3, "dv_total": dv1 + dv2 + dv3, "tof_s": tof_s}
