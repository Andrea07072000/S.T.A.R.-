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
| `star_albers` | Albers equal-area conic | Albers equal-area conic projection, forward, inverse and both scale factors, for cones in either hemisphere and the tangent cone; within 1.9e-6 m of PROJ and 9.1e-7 m of PyGeodesy on 600 cases; reproduces Snyder's published coordinates and scale factors and refuses degenerate cones |
| `star_coords` | Spherical and cylindrical to rectangular coordinates | Spherical and cylindrical coordinates to rectangular and back; agrees with ERFA, SPICE and astropy to 3e-16 relative and 6e-14 deg on 600 cases in both directions, close to the axis included, and refuses out-of-range input |
| `star_ecliptic` | Mean obliquity and equatorial-ecliptic directions | Mean obliquity of the ecliptic (IAU 2006 and IAU 1980) and conversion of directions between equatorial and ecliptic frames; agrees with ERFA, astropy and SPICE to 1.1e-13 deg and with ERFA and skyfield to 1.5e-11 arcsec on 600 cases, and refuses out-of-range input |
| `star_epoch` | Julian and Besselian epochs | Julian and Besselian epochs to and from two-part Julian Dates; agrees with ERFA to 5e-13 yr, with skyfield and five SPICE constants to 3e-10 day on 600 dates and 600 epochs, and refuses out-of-range input |
| `star_galactic` | Equatorial-galactic directions | Galactic longitude and latitude from equatorial directions and back, in the Hipparcos (ICRS) and IAU 1958 (B1950) definitions; agrees with ERFA, astropy and SPICE to 1.1e-13 deg on 600 directions in both directions and refuses out-of-range input |
| `star_gasdynamics` | Isentropic flow and normal shock | Isentropic flow ratios, Mach number from area ratio on either branch and normal-shock jump of a calorically perfect gas; within 1.2e-15 of scikit-aero and fluids on 600 cases for the relations they provide; reproduces the NACA Report 1135 tables; density, temperature and total-pressure ratios across the shock rest on the published table and the conservation laws only |
| `star_horizon` | Hour angle and declination to azimuth and elevation | Azimuth and elevation from hour angle, declination and latitude, the inverse, and the parallactic angle; agrees with ERFA and a SPICE rotation to 1.1e-13 deg on 600 cases in both directions and refuses out-of-range input |
| `star_interp` | Lagrange interpolation of tabulated data | Value and first derivative of the interpolating polynomial through 2 to 20 tabulated points, in barycentric form; within 7e-15 of exact rational arithmetic on 600 tables, closer to the exact value than SciPy (1.2e-14) and NumPy (7e-11) on the same tables; extrapolation refused |
| `star_lcc` | Lambert conformal conic | Lambert conformal conic projection, forward, inverse and scale factor, for cones in either hemisphere and the tangent cone; within 8e-7 m per Earth radius of PROJ and 7e-6 m of PyGeodesy on 600 cases; reproduces Snyder's published example and refuses degenerate cones |
| `star_mat3` | 3x3 matrix operations | Transpose, exact determinant and inverse, products and a proper-rotation test for 3x3 matrices; determinant and inverse identical to exact rational arithmetic on 575 matrices including condition numbers up to 1e8 (where SPICE's inverse is off by 6e-6 and NumPy's by 9e-10); singular matrices refused |
| `star_mercator` | Mercator and Web Mercator | Mercator projection on the ellipsoid with optional latitude of true scale, forward, inverse and scale factor, and Web Mercator; within 6e-8 m of PROJ, 7.5e-9 m of PyGeodesy's isometric latitude and 3e-8 m of both for Web Mercator on 600 cases; reproduces Snyder's published x and scale factor |
| `star_polar` | Polar stereographic and UPS | Polar stereographic projection at either pole with any parallel of true scale, forward, inverse and scale factor, and the UPS grid; within 7e-8 m of PROJ and 5e-9 m of PyGeodesy on 600 cases; reproduces Snyder's published example and refuses out-of-range input |
| `star_poly` | Real roots of quadratics and cubics | Distinct real roots of quadratics and cubics with the number of roots decided in exact arithmetic and each root isolated by exact-sign bisection, plus Horner evaluation; on 640 polynomials the count equals SymPy's exact count and every root equals the exact root rounded to a float; reproduces the classic cancellation example |
| `star_quadrature` | Gauss-Legendre quadrature | Gauss-Legendre nodes and weights for 1 to 32 points, each node the float nearest to the true root (exact coefficients, exact-sign bisection) and each weight evaluated exactly and rounded once; fixed-rule integration and Legendre polynomials with derivative; all 528 nodes and weights equal SymPy's 40-digit values rounded to a float |
| `star_rootfind` | Bracketed roots to the last float | Root of a real function inside a bracket by bisection over the floats (no tolerance, at most 64 evaluations after the two ends, the result within one float of the change of sign) and a scan for every change of sign over equal pieces; 600 problems in six families, Kepler's equation included, agree with mpmath at 50 digits, SciPy brentq and fluids brenth within 2.1e-15 relative |
| `star_sexagesimal` | Sexagesimal angles | Degrees to and from degrees/minutes/seconds and hours/minutes/seconds with one rounding on the whole angle; rounded fields identical to ERFA on 1200 of 1200 cases, joined angles within 1.2e-13 deg of ERFA and astropy, and out-of-range input refused |
| `star_sigma` | N-sigma coverage in 1, 2 and 3 dimensions | Coverage, tail probability and inverse of n sigma for a Gaussian error in one, two and three dimensions, and the normal distribution function and quantile; within 1.9e-13 relative of mpmath at 40 digits and 2.4e-13 of SciPy on 600 cases, tails included; reproduces the published normal and chi-square tables |
| `star_sphere` | Separation, position angle and offset on the sphere | Angular separation, position angle and offset point for directions on the sphere, accurate from 1e-12 deg to the antipode; agrees with ERFA and astropy to 3e-14 deg on 600 pairs and refuses out-of-range angles |
| `star_twobody` | Sizes and speeds of a Keplerian ellipse | Period, mean motion, circular and escape speed, apsis radii and speeds and specific energy of a two-body ellipse; within 4e-14 relative of SPICE for any gravitational parameter and 2.6e-14 of hapsira on 600 orbits; reproduces the geostationary orbit and refuses non-elliptic input |
| `star_units` | Conversion with exact definitions and a dimension check | Conversion between 64 units of ten dimensions and four temperature scales from exact definitions held as fractions; identical to SciPy within 4.5e-16 on all 416 ordered pairs and to astropy within 2.3e-16 on 328; a conversion between different dimensions (force and impulse, mass and force) is refused |
| `star_utm` | Transverse Mercator and UTM | Transverse Mercator and UTM coordinates, forward and inverse, by Krueger's series; within 2e-7 m of PROJ and PyGeodesy on 600 points in their zone and 2.5e-7 m of PROJ up to 12 deg from the central meridian; reproduces Snyder's published example and refuses out-of-range input |
| `star_vec3` | Three-dimensional vector operations | Dot, cross and triple product, length, distance, unit vector, accurate angle between directions, projection and rejection of three-dimensional vectors; within 6e-16 of SPICE and ERFA and 8e-15 of NumPy on 600 triples of vectors, nearly parallel pairs included; malformed vectors and zero directions refused |
| `star_wrap` | Angle reduction, difference and circular mean | Reduction of angles to [0, 360) and [-180, 180), shortest signed difference and circular mean; identical to astropy, within 2.4e-10 deg of ERFA and 6e-14 deg of SciPy on 600 angles and 600 samples, every result inside its range, undefined means refused |
| `star_chebyshev` | Chebyshev series with derivative | Value and first derivative of a Chebyshev series by Clenshaw's recurrence, on [-1, 1] or on an interval given by midpoint and radius (the convention of ephemeris segments); 600 series agree with CSPICE chbval/chbder and NumPy within 1e-14 and with mpmath at 40 digits within 5e-14 of the natural scale of the sum; reproduces the NAIF documentation example |
| `star_crc` | Cyclic redundancy checks, bit by bit | The CRC-16 of CCSDS transfer frames, CRC-16/XMODEM, CRC-32, CRC-32C and any Rocksoft-model CRC of 8 to 64 bits computed through the defining shift register; on 499 messages and nine variants identical to fastcrc (4491 values), to CPython binascii and zlib (1497) and to a polynomial division over GF(2) in SymPy (1611); reproduces the nine catalogue check values |
| `star_doppler` | Range, range rate and one-way Doppler shift | Range and range rate between two states and the frequency received over that link, by the longitudinal relativistic formula or the first-order one; on 600 pairs of states and range rates up to 0.9 c the results agree with NAIF SPICE (vnorm, dvnorm), astropy's Doppler equivalencies, NumPy and mpmath at 40 digits within 8.3e-16 of their natural scale |
| `star_linefit` | Least-squares line and correlation, correctly rounded | Least-squares straight line, standard errors of slope and intercept, residual standard deviation and Pearson correlation computed exactly in rational arithmetic and rounded once; on 500 datasets all six results are identical to the exact rational value from SymPy; reproduces the five certified values of the NIST Norris dataset to 1e-13 relative |
| `star_quantile` | Median, quantiles, IQR and MAD, correctly rounded | Median, Hyndman-Fan type 7 quantile, interquartile range and median absolute deviation computed exactly in rational arithmetic and rounded once; on 500 datasets (2000 values) every value is identical to the exact rational value from SymPy, and NumPy, SciPy and CPython statistics agree within 7e-16 of the largest value |
| `star_rotframe` | State between an inertial and a rotating frame | Position and velocity between an inertial frame and a frame rotating about z at a given angle and rate, transport term included, in both directions; on 600 states there and back the results agree with NAIF SPICE (rav2xf), SciPy and astropy within 5.2e-16 of &#124;r&#124; and of &#124;v&#124; + &#124;rate&#124; &#124;r&#124; |
| `star_slerp` | Interpolation of attitudes along the shortest arc | Spherical linear interpolation between unit quaternions along the shorter rotation, and interpolation in a table of attitudes at given times; on 600 pairs of attitudes the largest component difference is 4.4e-16 from SciPy Slerp and 3.3e-16 from a route through NAIF SPICE rotation matrices, axis and angle |
| `star_stats` | Summary statistics, correctly rounded | Mean, sample and population variance and standard deviation, root mean square and weighted mean computed exactly in rational arithmetic and rounded once, independent of the order of the values; on 500 datasets all seven statistics are identical to mpmath at 400 digits rounded once and to CPython's statistics module where it has them; reproduces the NIST NumAcc1 and NumAcc2 reference datasets |
| `star_tabint` | Integrals of tabulated data, correctly rounded | Trapezoid rule on any strictly increasing grid, its running integral and the composite Simpson rule for equally spaced samples, each evaluated exactly in rational arithmetic and rounded once; on 500 tables (1750 values) every value is identical to the exact rational value from SymPy, and NumPy and SciPy agree within 3.3e-16 of the sum of the absolute panel areas |
| `star_timecode` | CCSDS ASCII time codes A and B | Strict reader and writer of the CCSDS 301.0-B-4 ASCII time codes A (calendar) and B (day of year), with the fraction kept as its digits; fields equal to CPython datetime and numpy.datetime64 on 600 instants and to astropy on the 331 between 1900 and 2100; refuses all 40 malformed or out-of-range texts of the corpus, of which the ISO parsers of those libraries accept 10 to 14 |

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
