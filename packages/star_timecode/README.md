# star_timecode — CCSDS ASCII time codes A and B, strict

Reads and writes the two ASCII time codes of CCSDS 301.0-B-4 (calendar date or day of year, `T`, UTC time of day,
optional fraction, optional `Z`) and refuses every text that is not exactly one of them. Standard library only.

```python
import star_timecode as tc
tc.parse("1988-01-18T17:20:43.123456Z")        # (1988, 1, 18, 17, 20, 43, '123456')
tc.parse("1988-018T17:20:43.123456Z")          # the same fields, from the day-of-year form
tc.format_b(2026, 10, 7, 2, 45, 10)            # '2026-280T02:45:10Z'
tc.parse("2026-10-07 02:45:10")                # ValueError: a space is not the letter T
```

## Requirements
- R1 `parse(text)` accepts code A `YYYY-MM-DDThh:mm:ss[.d...][Z]` and code B `YYYY-DDDThh:mm:ss[.d...][Z]` and
  returns (year, month, day, hour, minute, second, fraction). The fraction is returned as its string of digits (up
  to 12): nothing passes through a float, and a code read and written again is the same text.
- R2 `format_a` and `format_b` write the two codes from the same fields; `day_of_year` and `month_day` convert between
  the two date forms with the Gregorian leap-year rule, years 0001 to 9999.
- R3 Measured on 600 instants written in both codes: calendar fields, microseconds and day of year equal to CPython
  `datetime` and `numpy.datetime64` on all 600 and to astropy on the 331 between 1900 and 2100. Of 40 malformed or
  out-of-range texts, all 40 are refused.
- R4 Every function returns its result or raises `ValueError`: wrong shape (widths, separators, case, spaces, signs,
  offsets, non-ASCII digits), a date or time that does not exist, second 60 anywhere but 23:59, arguments of the
  wrong type.

## Evidence
- Published: the two examples of CCSDS 301.0-B-4 section 3.5.1; the Gregorian rule on 1900, 2000, 2100, 2400.
- `crosscheck_timecode.py`: CPython, NumPy and astropy, each in its own interpreter. The same run counts how many of
  the 40 malformed texts each library's ISO parser accepts: 10 (`datetime.fromisoformat`), 14 (`numpy.datetime64`),
  12 (astropy `isot`). Those parsers read ISO 8601 more broadly than the CCSDS codes by design; the count says what a
  caller who needs the strict form must check for itself.

## What is NOT claimed
Syntax and calendar only. Second 60 is accepted at 23:59 of any date: whether a leap second really occurred there is
a question for a leap-second table (see `star_timescales` in this repository), not for this module. No time zones or
offsets (the codes are UTC), no truncated forms (date only, no seconds), no conversion to seconds, Julian dates or
other time scales, no years before 0001 or after 9999. The limit of 12 fraction digits is this module's, not the
standard's.
