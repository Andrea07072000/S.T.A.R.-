# S.T.A.R. packages — space-engineering software that has to prove itself

Every package here was released only after its evidence was in place, and every package is re-tested by GitHub on each
push ([packages workflow](../.github/workflows/packages.yml)) — on a machine that is not ours. If a claim below stops
being true, that workflow turns red in public.

**How a package earns a place here**
- tests against **published reference values** (Vallado, CCSDS blue books, Curtis, SGP4-VER, NASA F Prime frames…);
- comparison with **independent implementations** written by other people (ERFA/astropy, skyfield, Orekit, hapsira,
  python-sgp4, spacepackets, ccsdspy, pyorbital…);
- **mutation testing**: we deliberately break the code hundreds of times and check that the tests notice
  (score ≥ 0.80 required; most are above 0.85);
- one license for everything: **Apache-2.0**;
- installation **from its own release tag** in a fresh environment, tests run outside the source tree, on Windows and
  Linux.

## What is here

| Package | What it does | Notable evidence |
|---|---|---|
| `star_audit` | **Independent auditors of other space libraries**: geodesy, leap seconds, SGP4, TEME→GCRS frames, TDB−TT, GMST, orbital elements, Kepler's equation, Lambert solvers, CCSDS TM frames, CCSDS Space Packets, TLE ingestion | each auditor is first validated on a published value; it measures agreement, model families and what a library silently accepts |
| `star_crosscheck` | Cross-check engine: runs the same computation through independent implementations and reports AGREE / DISAGREE / INSUFFICIENT / DEGRADED, never a silent pass | 13 campaigns (time scales, geodesy, SGP4, CCSDS, Lambert, elements, TDB, GMST...) with recorded evidence |
| `star_telemetry_c` | The CCSDS AOS/TM frame check in C99 (no dynamic memory), for flight-like targets | field-equal to the Python reference on 305 frames (5 NASA F Prime frames + 300 corrupted); every truncation of every frame parsed under AddressSanitizer + UBSan; built with `-Werror` on x86_64 and, under qemu-user, aarch64 and riscv64 in this repository's CI |
| `star_telemetry` | CCSDS AOS/TM transfer frames and Space Packets (Python) | field-exact against spacepackets and ccsdspy on 300 frames; real NASA Europa Clipper telemetry (ccsdspy test data) |
| `conjunction_screen_sgp4` | All-vs-all satellite conjunction screening with SGP4 | rejects and **counts** malformed TLEs (a risk our own TLE audit found) |
| `star_cdm` | CCSDS 508.0 Conjunction Data Message parser + component-level consistency checks | RTN projection agrees with Orekit to < 1e-6 m |
| `star_orbit` | Cowell propagator (J2, drag, SRP) | GMST vs ERFA, Sun direction vs astropy, J2 vs the gradient of the potential |
| `star_maneuver` | Vis-viva, Hohmann, bi-elliptic, plane change, combined burn | published values (Vallado sec. 6.3 crossovers); invalid input (r > 2a, NaN, mu <= 0) raises instead of returning a number |
| `star_elements`, `star_lambert` | State ↔ classical elements; Lambert problem | agree with Vallado, hapsira and skyfield to 1e-11; Lambert vs hapsira (Izzo) on 24 geometries |
| `star_geodesy`, `star_sidereal`, `star_tdb` | ECEF ↔ geodetic, sidereal time, TDB−TT | published examples + independent libraries |
| `star_kepler` | Two-body propagation with universal variables (no orbit singularity, bounded iterations) | 4.7e-7 km on 450 closed-form orbits, level with hapsira, Orekit and NAIF prop2b |
| `star_topo` | Look angles from a ground site: ECEF to/from East-North-Up and azimuth/elevation/range | EPSG Guidance Note 7-2 example to 0.3 mm; pymap3d, PROJ and PyGeodesy within 18 nm |
| `star_sun` | Low-precision Sun vector (1950-2050), orbit beta angle, cylindrical eclipse test | within 0.0097 deg of JPL DE440 (apparent) and astropy; states that the series includes aberration |
| `star_geodesic` | Geodesic distance and azimuths on WGS-84, direct and inverse | Flinders Peak - Buninyong line to 0.14 mm; PROJ, GeographicLib and PyGeodesy within 0.08 mm on 840 problems |
| `star_atmosphere` | U.S. Standard Atmosphere 1976 below 86 km | published layer pressures within 2e-7; fluids within 4e-15; refuses altitudes outside the model |
| `star_quaternion` | Unit quaternions and rotation matrices with one stated convention | NAIF SPICE and SciPy within 9e-16; non-unit quaternions are refused, not silently normalised |
| `star_euler` | Euler angles for the twelve axis sequences, gimbal lock reported | SciPy and NAIF SPICE within 6e-16 on all twelve sequences |
| `star_j2` | Secular J2 rates, sun-synchronous and critical inclination | within 0.31 % of Orekit's Eckstein-Hechler theory and 0.38 % of a numerical integration |
| `star_cw` | Relative motion near a circular orbit (Clohessy-Wiltshire) and two-impulse rendezvous | equal to the matrix exponential within 1.1e-13; distance from real two-body motion measured per separation |
| `star_iod` | Initial orbit determination from three positions: Gibbs and Herrick-Gibbs | Vallado Example 7-3; Orekit IodGibbs within 8e-9; measured domain of each method on 240 known orbits |
| `star_tle` | Strict reader of two-line element sets (Alpha-5 included) | fields equal to python-sgp4 and Orekit within 6e-14; refuses 147 of 174 malformed sets (Orekit 145, python-sgp4 0) |
| `star_coverage` | Coverage geometry of a satellite over a spherical body | pymap3d and PROJ within 1e-13; precise from 1 mm of altitude to 1e12 km |
| `star_calendar` | Calendar dates and Julian day numbers in exact integer arithmetic | identical to ERFA, CPython datetime and NAIF SPICE on 9014 dates, years B.C. and the 1582 switch included |
| `star_ellipsoid` | WGS-84 ellipsoid: radii of curvature, auxiliary latitudes, meridian arc | pymap3d and PyGeodesy to rounding; meridian arc within 4e-9 m |
| `star_era` | Earth Rotation Angle (IAU 2000) and Greenwich Mean Sidereal Time (IAU 2006) from two-part Julian Dates | SOFA validation values to 1e-13 rad; ERFA and Skyfield within 4e-8 arcsec |
| `star_moon` | Low-precision geocentric Moon position (1950-2050) | Vallado Example 5-3 to 0.4 m; measured within 0.36 deg and 1200 km of JPL DE440 on 2002 dates |
| `star_precession` | IAU 1976 precession between J2000 and the mean equator and equinox of date | SOFA validation values to 1e-15; ERFA within 1.2e-16; PyEphem within 0.21 arcsec |

## What the audits found (factual, reproducible)
- **TLE ingestion**: python-sgp4 `Satrec.twoline2rv` and skyfield `EarthSatellite` accept every malformed TLE in our
  corpus (bad checksum, wrong line number, satellite-number mismatch, truncated) — python-sgp4 documents this tolerance
  and offers `sgp4.io.verify_checksum`; Orekit rejects all of them. Callers should validate TLEs themselves.
- **TEME→GCRS**: Orekit follows the IAU-1976/1980 model (+ frame bias) while astropy/skyfield follow IAU 2006/2000A;
  the two families differ by up to ~12 m at GEO radius over 1990–2050. A model choice, not a defect.
- **Orbital elements, singular orbits**: four libraries use four incompatible conventions for circular/equatorial
  orbits (zeroed angle, the Vallado sentinel 999999.1 rad, a computed value, a refusal).
- **Space Packets**: three decoders reject every length defect; packets with Packet Version Number ≠ 0 are accepted by
  two of them.
- **Kepler's equation** (5 solvers against a 40-digit truth, eccentricity up to 0.9999): hapsira, Orekit and our
  solver agree to 3e-12 rad; one solver returns an unconverged value (about -1.6e27 rad) at e = 0.9999 after printing a
  message; NAIF `conics` loses precision near e = 1 unless the mean anomaly is given in (-pi, pi] (a usage note).
- **Lambert solvers** (4 solvers against the velocity of 315 known orbits): all agree to 1e-10 .. 3e-7 km/s - once the
  direction flag is set from the geometry. The flag does not mean the same thing everywhere: in one solver it is the
  direction of motion, in two others the same kind of flag selects the short way, and leaving it at `True` returns the
  other solution on every transfer beyond 180 degrees (up to 91 km/s, no exception).
- **Input validation** (found by probing every error requirement with NaN, infinity, zero and degenerate inputs): our
  propagator looped forever on a zero step, our screening answered "no conjunction" for a NaN threshold, our
  cross-check accepted an infinite tolerance, our CDM parser accepted `NaN` and `1_000` as numbers. All fixed, each
  with a contract test.
- Our own code was not spared: the same cross-checks found and fixed defects in our CCSDS randomizer, in our TM frame
  decoder (Python and C) and in our screening pipeline.

## What we do NOT claim
No flight heritage, no certification, no "NASA-grade". Hardware results elsewhere in the project are on emulators and
simulators, not on physical hardware. An audit reports agreement and model dependence, not which library is "right".

## Help us
Run the tests, try the auditors on your library, open an issue when a number here is wrong. Reproductions by people
outside S.T.A.R. are the evidence we value most.
