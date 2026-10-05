# star-audit

Independent accuracy audit of ECEF -> geodetic conversions in third-party libraries, per altitude band.

## Requirements
- R1 `audit_function(fn)` / `run_external(python, code)`: 450 points (10 latitudes x 5 longitudes x 9 altitudes from
  0 to 36,000 km) with KNOWN geodetic truth; the library converts their exact ECEF; errors are measured against truth.
- R2 Envelope per altitude band: max latitude error (deg), height error (m), 3-D position error (m); worst case.
- R3 The library runs in its own interpreter (`run_external`); a failing library run raises, never returns a score.
- Dependency: star-geodesy >= 0.1.0 (exact reference: forward transform, iterative inverse to 1e-14 rad).

## How it is verified
The auditor is tested against itself: an exact library scores < 1 micrometre; injected defects (25 cm height error
above 1000 km; 1e-6 deg latitude bias) are measured with the injected size in the right band.

## First audit (2026-10-04, default calls)
pymap3d 3.2.0 ecef2geodetic: worst 3-D error 80.7 m at 36,000 km (1.56 m at 5,000 km; 0.3 mm at 400 km).
PROJ 9.8.1 via pyproj (EPSG:4978->4979): worst 0.39 m at 36,000 km (1.9 mm at 400 km).

## Not claimed
That these libraries are "wrong": they may be tuned for near-surface use; other call options were not audited.

## Leap-second audit (0.2.0, `leapsec_audit`)
- R4 `audit(python, driver)`: drives a time library ONLY through its documented UTC-string -> TAI-string API on 7 probes
  (incl. instants inside 23:59:60) and classifies OK / WRONG / REJECTED / PAST_TABLE_WARNED / PAST_TABLE_SILENT
  against a hand-written IERS Bulletin C truth.
- First audit (2026-10-04): ERFA 2.0.1.5, astropy and skyfield all OK on the 6 probes with truth; beyond the table
  (2035) skyfield extrapolates silently, ERFA and astropy warn.

## SGP4 audit (0.3.0, `sgp4_audit`)
- R5 `audit(command, driver, cases)` vs Vallado SGP4-VER (33 cases, 667 epochs; fixtures with provenance): per-case max
  3-D error, median, refusals. Cases are paired by ORDER (NORAD 20413 appears twice: short window and 3.5-year arc).
- First audit (2026-10-04): python-sgp4 2.27 (Vallado lineage, validates the probe) max 0.12 mm; Orekit 13.1 median
  8e-9 km but differs on Vallado's special cases (20413 long arc 27,924 km, 33333 near-parabolic 3,398 km, 33335 GEO
  0.05 km); pyorbital explicitly refuses deep-space (24 cases) and bad-checksum TLEs.

## TEME -> GCRS frame audit (0.4.0, `frame_audit`)
- R6 `audit(impls, cases)`: every implementation runs in its own interpreter (driver `teme_to_gcrs(utc, r_km)`);
  probe validation first: Vallado's published TEME->GCRF example (2004-04-06 07:51:28.386009 UTC) must be reproduced
  to < 1 m; then pairwise divergence envelopes per year 1980-2050 on LEO and GEO vectors, and refusals.
- First audit (2026-10-04), 5 implementations / 4 lineages (`run_frame_audit.py`): astropy 8.0.1 and skyfield agree
  to 6 mm and reproduce Vallado to 4 mm; Orekit 13.1 reproduces Vallado to 0.72 m and differs from them by 3-12 m at
  GEO (1990-2050). Isolated with model implementations built from ERFA primitives: Orekit = IAU-1976/1980 (FK5)
  + frame bias to <= 0.54 m. A model choice, not a defect (DISC-FRAME-001, explained).
- Not claimed: which model is "right" for a user; the audit measures agreement and model dependence.

## CCSDS TM frame-decoder audit (0.5.0, `ccsds_audit`)
- R7 `audit(impls, cases)`: deterministic corpus (seed 20261004, sha256-pinned) of 40 valid TM frames (CCSDS 132.0-B,
  every header option: OCF, secondary header 1..8 octets) and 260 copies with 1..4 bit flips in header, data or FECF.
  Probe validation: an implementation counts only if it decodes every valid frame field-exact; a driver exception is
  never a credible rejection. Reports silent acceptance of bad-FECF frames, CRC collisions and acceptance disagreements.
- First audit (2026-10-04, `run_ccsds_audit.py`): spacepackets 0.32.0 and star_telemetry 0.2.3 (independent
  lineages): 40/40 exact, 260/260 corrupted rejected, 0 disagreements. Control: the superseded star_telemetry 0.2.1 is
  caught on 40/40 valid frames (VC count read from the master-channel octet; OCF/secondary header left in the data).
- Not claimed: coverage of AOS/USLP frames or of decoders not installed here.

## TT -> TDB audit (0.6.0, `tdb_audit`)
- R8 `audit(impls, epochs)`: each implementation in its own interpreter (`tdb_minus_tt(jd_tt)`); probe validation:
  every epoch within 50 us of the published low-precision formula (Explanatory Supplement, 0.001657 sin g +
  0.000014 sin 2g); pairwise envelopes over 401 epochs 1900-2100, per century; refusals exclude.
- First audit (2026-10-05, `run_tdb_audit.py`), 6 implementations, 3 model families: ERFA dtdb = astropy
  (Fairhead-Bretagnon); skyfield = star_tdb = a model of USNO Circular 179 eq. 2.6 written from the paper (0.0 s
  between them), 7.0 us from ERFA; SPICE DELTET (Kepler) 34.8 us from ERFA and 0.39 us from the low-precision formula.
- Probe defect found and fixed before any claim: subtracting two float JDs in the skyfield driver (~40 us resolution)
  produced a 20 us 'divergence'; the paper model exposed it.
- Not claimed: which model a user needs; the audit measures agreement and model dependence.

## GMST audit (0.7.0, `gmst_audit`)
- R9 `audit(impls, epochs)`: each implementation in its own interpreter (`gmst_deg(jd_ut1)`); probe validation on
  Vallado's published Example 3-5 (GMST = 152.578787810 deg at 1992-08-20 12:14:00 UT1) within 0.1 arcsec;
  wrap-safe pairwise envelopes in arcsec over 201 epochs 1950-2050, per half-century; refusals exclude.
- First audit (2026-10-05, `run_gmst_audit.py`), 7 implementations, 2 model families: IAU 1982 (ERFA gmst82,
  python-sgp4 gstime, pyorbital, star_sidereal) agree within 0.11 mas and reproduce Vallado to 1e-5 arcsec;
  IAU 2006 (ERFA gmst06, astropy, skyfield) agree within 0.06 mas; the families differ by up to 0.151 arcsec.
- Not claimed: which model a user needs (SGP4/TEME users must stay on IAU 1982).

## Orbital-elements audit (0.8.0, `elements_audit`)
- R10 `audit(impls, cases)`: rv -> (p, e, i, RAAN, argp, nu) per implementation in its own interpreter; probe validation
  on Vallado's Example 2-5 (tolerances 0.01 km / 1e-5 / 0.01 deg, sized on the printed digits); seeded, sha256-pinned
  corpus of 60 regular + 20 singular (near-circular, near-equatorial, both) states; regular cases compared with the
  generating truth and pairwise; singular cases: each implementation's CONVENTION (0, sentinel, NaN, value, refusal).
- First audit (2026-10-05, `run_elements_audit.py`): python-sgp4/Vallado, hapsira, skyfield, star_elements all
  validated, all within 3.6e-11 km and 3e-12 deg of the truth on regular cases. Singular conventions differ:
  hapsira zeroes the undefined angle, Vallado's rv2coe returns the sentinel 999999.1 rad for argp (circular AND
  equatorial), skyfield returns computed values, star_elements refuses circular orbits.
- Not claimed: which convention is right; the audit makes them visible before data is exchanged between tools.

## TLE ingestion audit (0.9.0, `tle_audit`)
- R11 `audit(impls, cases)`: what TLE readers accept. Reference = the format rule (checksum mod 10 with '-' = 1, line
  numbers, equal satellite numbers, 69 columns). Corpus: the 29 well-formed SGP4-VER TLEs plus 6 derived kinds
  (field_digit, checksum, line_number, satnum_mismatch, truncated = must reject; resummed = well-formed, must accept),
  sha256-pinned. Probe validation: every valid TLE accepted and its inclination read within 1e-4 deg.
- First audit (2026-10-05, `run_tle_audit.py`): python-sgp4 Satrec.twoline2rv and skyfield EarthSatellite accept
  145/145 malformed TLEs (tolerant by design: python-sgp4 offers sgp4.io.verify_checksum separately); pyorbital checks
  the checksum but accepts wrong line numbers and satellite-number mismatches (58/58); Orekit (isFormatOK) rejects all.
  Consequence for S.T.A.R.: conjunction_screen_sgp4 0.2.0 now validates TLEs and counts rejections.

## CCSDS Space Packet audit (`packet_audit`)
- R12 `audit(impls, cases)`: what Space Packet decoders accept (CCSDS 133.0-B rule: version '000', length field =
  data octets - 1). Corpus (sha256 of the rounded corpus pinned): 40 valid + 10 idle (accept) and 4 x 40 defective
  (version, truncated, trailing, header_only: reject). Probe validation: every valid packet decoded field-exact.
- First audit (2026-10-05, `run_packet_audit.py`): spacepackets, ccsdspy and star_telemetry 0.2.5 reject every length
  defect; spacepackets and ccsdspy accept version != 0 (40/40); star_telemetry rejects it since 0.2.4 (fix prompted by
  this audit).
