# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 S.T.A.R. Aerospace & Phoenix Research
"""
star_orbit: High-fidelity numerical orbit propagation federated with S.T.A.R. timescales.
"""

from .core import (
    MU_EARTH,
    R_EARTH,
    J2_EARTH,
    SpacecraftProperties,
    OrbitState,
    propagate_orbit,
    compute_gmst_rad,
    compute_sun_vector_eci,
)

__all__ = [
    "MU_EARTH",
    "R_EARTH",
    "J2_EARTH",
    "SpacecraftProperties",
    "OrbitState",
    "propagate_orbit",
    "compute_gmst_rad",
    "compute_sun_vector_eci",
]
