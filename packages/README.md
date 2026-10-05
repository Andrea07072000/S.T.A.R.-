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
- installation **from its own release tag** in a fresh environment, tests run outside the source tree, on Windows and
  Linux.

## What is here

| Package | What it does | Notable evidence |
|---|---|---|
| `star_audit` | **Independent auditors of other space libraries**: geodesy, leap seconds, SGP4, TEME→GCRS frames, TDB−TT, GMST, orbital elements, CCSDS TM frames, CCSDS Space Packets, TLE ingestion | each auditor is first validated on a published value; it measures agreement, model families and what a library silently accepts |
| `star_telemetry` | CCSDS AOS/TM transfer frames and Space Packets (Python) | field-exact against spacepackets and ccsdspy on 300 frames; real NASA Europa Clipper telemetry (ccsdspy test data) |
| `conjunction_screen_sgp4` | All-vs-all satellite conjunction screening with SGP4 | rejects and **counts** malformed TLEs (a risk our own TLE audit found) |
| `star_cdm` | CCSDS 508.0 Conjunction Data Message parser + component-level consistency checks | RTN projection agrees with Orekit to < 1e-6 m |
| `star_orbit` | Cowell propagator (J2, drag, SRP) | GMST vs ERFA, Sun direction vs astropy, J2 vs the gradient of the potential |
| `star_elements`, `star_lambert` | State ↔ classical elements; Lambert problem | agree with Vallado, hapsira and skyfield to 1e-11; Lambert vs hapsira (Izzo) on 24 geometries |
| `star_geodesy`, `star_sidereal`, `star_tdb` | ECEF ↔ geodetic, sidereal time, TDB−TT | published examples + independent libraries |

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
- Our own code was not spared: the same cross-checks found and fixed defects in our CCSDS randomizer, in our TM frame
  decoder (Python and C) and in our screening pipeline.

## What we do NOT claim
No flight heritage, no certification, no "NASA-grade". Hardware results elsewhere in the project are on emulators and
simulators, not on physical hardware. An audit reports agreement and model dependence, not which library is "right".

## Help us
Run the tests, try the auditors on your library, open an issue when a number here is wrong. Reproductions by people
outside S.T.A.R. are the evidence we value most.
