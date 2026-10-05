# star-sidereal

Greenwich mean sidereal time (IAU 1982 model) and local mean sidereal time. Standard library only.

## Requirements
- R1 `gmst82_deg(jd_ut1_day, jd_ut1_frac=0.0)` -> degrees in [0, 360), Vallado eq. 3-47 (Aoki et al. 1982).
- R2 `lst_deg(jd_day, jd_frac, east_longitude_deg)` -> degrees in [0, 360).
- R3 Non-finite input raises `ValueError`. Input is UT1 (not UTC): the caller applies DUT1.

## How it is verified
Vallado Example 3-5 (GMST 152.578787810 deg, LST 48.578787810 deg) to 1e-7 deg; J2000 noon value; XC-013 vs ERFA
gmst82: 19/19 AGREE, max difference 1e-9 deg.

## Not supported / not claimed
IAU 2000/2006 (Earth rotation angle based) sidereal time, apparent sidereal time (equation of the equinoxes), UTC->UT1.
