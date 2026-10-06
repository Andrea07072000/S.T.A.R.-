"""star_atmosphere against the values printed in "U.S. Standard Atmosphere, 1976" (NOAA-S/T 76-1562).
Verifies: R1, R2, R3 (README).

Published: (a) the defining table of the layers - base geopotential altitude, temperature and pressure of each layer;
(b) rows of the main table at round GEOMETRIC altitudes (temperature to 0.001 K, pressure and density to five digits).
The comparison with fluids and hapsira on 308 altitudes is in crosscheck_atmosphere.py."""
import math

import pytest

import star_atmosphere as a

# geopotential altitude (m), temperature (K), pressure (Pa) at the base of each layer and at the top of the model
BASES = [(0.0, 288.15, 101325.0), (11000.0, 216.65, 22632.06), (20000.0, 216.65, 5474.889), (32000.0, 228.65, 868.0187),
         (47000.0, 270.65, 110.9063), (51000.0, 270.65, 66.93887), (71000.0, 214.65, 3.956420)]
# geometric altitude (m), temperature (K), pressure (Pa), density (kg/m3) as printed
ROWS = [(0, 288.150, 1.01325e5, 1.2250), (1000, 281.651, 8.9876e4, 1.1117), (5000, 255.676, 5.4048e4, 7.3643e-1),
        (10000, 223.252, 2.6499e4, 4.1351e-1), (20000, 216.650, 5.5293e3, 8.8910e-2), (30000, 226.509, 1.1970e3, 1.8410e-2),
        (50000, 270.650, 7.9779e1, 1.0269e-3), (80000, 198.639, 1.0524, 1.8458e-5)]


@pytest.mark.parametrize("h, t, p", BASES)
def test_published_layer_bases(h, t, p):
    got = a.ussa1976(a.geometric_m(h))
    assert abs(got[0] - t) < 1e-9 and abs(got[1] / p - 1) < 2e-7              # pressures printed to seven digits


@pytest.mark.parametrize("z, t, p, rho", ROWS)
def test_published_rows_at_geometric_altitude(z, t, p, rho):
    got = a.ussa1976(z)
    assert abs(got[0] - t) < 5.1e-4                                           # printed to 0.001 K
    assert abs(got[1] / p - 1) < 1.1e-4 and abs(got[2] / rho - 1) < 6e-5      # one unit in the fifth printed digit


def test_sea_level_values_and_speed_of_sound():
    t, p, rho, c = a.ussa1976(0)
    assert (t, p) == (288.15, 101325.0) and abs(rho - 1.2250) < 5e-5 and abs(c - 340.294) < 5e-4      # printed: 340.294 m/s
    assert abs(a.ussa1976(11019.1)[3] - 295.069) < 1e-3 and abs(a.ussa1976(50000)[3] - 329.799) < 1e-3


def test_geopotential_conversion_and_its_inverse():
    assert a.geopotential_m(0) == 0.0 and abs(a.geopotential_m(86000) - 84852.0) < 0.05              # printed: 84 852 m
    assert abs(a.geometric_m(11000) - 11019.1) < 0.05 and abs(a.geometric_m(47000) - 47350.1) < 0.05  # printed Z of the bases
    assert abs(a.geometric_m(71000) - 71802.0) < 0.05 and a.geometric_m(a.H_MAX) == 86000.0 and a.geometric_m(a.H_MIN) == -5000.0
    for z in (-5000.0, -1.0, 0.0, 1.0, 8848.86, 30000.0, 85999.999, 86000.0):
        assert abs(a.geometric_m(a.geopotential_m(z)) - z) < 1e-8
    assert a.geopotential_m(10000) == pytest.approx(6356766.0 * 10000 / 6366766.0, rel=1e-15)


def test_ideal_gas_law_and_hydrostatic_balance_hold_everywhere():
    for i in range(0, 861):
        z = i * 100.0
        t, p, rho, c = a.ussa1976(z)
        assert rho == pytest.approx(p * a.M0 / (a.R_STAR * t), rel=1e-14) and c == pytest.approx(math.sqrt(1.4 * a.R_STAR * t / a.M0), rel=1e-14)
    for z in (500.0, 9000.0, 15000.0, 25000.0, 40000.0, 49000.0, 60000.0, 78000.0):
        dz = 1.0
        dp = a.ussa1976(z + dz)[1] - a.ussa1976(z - dz)[1]
        g = a.G0 * (a.R_EARTH / (a.R_EARTH + z)) ** 2                          # gravity at geometric altitude
        assert dp / (2 * dz) == pytest.approx(-a.ussa1976(z)[2] * g, rel=2e-6)


def test_profile_is_continuous_at_the_layer_boundaries_and_pressure_decreases():
    for hb, _ in a.LAYERS[1:]:
        z = a.geometric_m(hb)
        below, above = a.ussa1976(z - 1e-6), a.ussa1976(z + 1e-6)
        assert all(abs(x / y - 1) < 1e-8 for x, y in zip(below, above))
    previous = a.ussa1976(-5000.0)[1]
    for i in range(1, 911):
        p = a.ussa1976(-5000.0 + i * 100.0)[1]
        assert p < previous
        previous = p
    assert abs(a.ussa1976(-5000.0)[0] - (288.15 + 0.0065 * 5003.936)) < 1e-6 and abs(a.ussa1976(86000)[0] - 186.946) < 1e-3


def test_temperature_gradient_of_each_layer():
    for (hb, lapse), top in zip(a.LAYERS, [h for h, _ in a.LAYERS[1:]] + [a.H_MAX]):
        z1, z2 = a.geometric_m(hb + 0.25 * (top - hb)), a.geometric_m(hb + 0.75 * (top - hb))
        slope = (a.ussa1976(z2)[0] - a.ussa1976(z1)[0]) / (0.5 * (top - hb))
        assert slope == pytest.approx(lapse, abs=1e-12)
    assert [round(l * 1000, 1) for _, l in a.LAYERS] == [-6.5, 0.0, 1.0, 2.8, 0.0, -2.8, -2.0]
