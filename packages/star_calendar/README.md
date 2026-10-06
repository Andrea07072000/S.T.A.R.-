# star_calendar — calendar dates and Julian day numbers, exactly

Julian Day Number of a calendar date and back, in the Julian, the (proleptic) Gregorian and the civil calendar, with
integer arithmetic only. Standard library only.

```python
import star_calendar as sc
sc.jdn(2000, 1, 1)                       # 2451545
sc.calendar_date(2299160)                # (1582, 10, 4): the next day is (1582, 10, 15)
sc.julian_date(1957, 10, 4, 19, 26, 24)  # (2436115.5, 0.81): day and fraction kept apart
```

## Requirements
- R1 `jdn(year, month, day, calendar)` and `calendar_date(jdn, calendar)` for `"gregorian"`, `"julian"` and `"auto"`
  (Julian up to 1582-10-04, Gregorian from 1582-10-15); astronomical year numbering; valid from JDN 0 to 9999-12-31.
- R2 `julian_date(...)` returns the pair (JD at the preceding midnight, fraction of day): the sum is the Julian Date and
  the pair keeps a nanosecond that a single float would lose. `weekday(jdn)` (0 = Monday), `day_of_year(...)`.
- R3 Measured: the same day number as ERFA, CPython `datetime` and NAIF SPICE (MIXED calendar) on 9014 dates, zero
  mismatches, including years B.C. and every day around the 1582 switch.
- R4 Every function returns integers (or the documented pair) or raises `ValueError`: non-integer or boolean year,
  month, day or day number; a date that does not exist in the calendar (29 February 1900 Gregorian, 1582-10-05 to
  1582-10-14 civil); an unknown calendar; a time outside the day; anything outside the valid range.

## Evidence
- Published: Meeus, Astronomical Algorithms, chapter 7 (JD 0, 333-01-27, the 1582 switch, 1957-10-04, 2000-01-01).
- `crosscheck_calendar.py`: three implementations, each in its own interpreter, first probed on the published dates.
  The probe on year 333 showed that SPICE's default calendar is the proleptic Gregorian, not the mixed one.
- Structure: every day number has one date and dates follow each other; leap years of both calendars; 1582 had 355 days.

## What is NOT claimed
A calendar, not a time scale: no leap seconds, no UTC/TT/TDB conversion, no time zones, no local adoption dates of
the Gregorian calendar (the civil switch is the papal one of October 1582).
