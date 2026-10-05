# star-tdb

TDB - TT for a TT Julian date, geocentre. Standard library only.

## Requirements
- R1 `tdb_minus_tt(jd_tt) -> seconds`, USNO Circular 179 (Kaplan 2005) eq. 2.6, 7 terms.
- R2 Accuracy within 10 microseconds of the full Fairhead & Bretagnon series over 1600-2200.
- R3 Outside 1600-2200 raises `ValueError` (no extrapolation beyond stated validity).

## How it is verified
ERFA `dtdb` (full series, different method): XC-012 13/13 AGREE, max difference 9.0 us; reference values frozen in
the tests; scan of 1600-2200 every 37 days: max 9.0 us.

## Not supported / not claimed
Topocentric terms (observer position), sub-microsecond accuracy, dates outside 1600-2200.
