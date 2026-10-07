# Published values the tests of star_timecode may cite (checked by the reviewer against the computation)

1. CCSDS 301.0-B-4, Time Code Formats, section 3.5.1 (ASCII calendar segmented time codes), examples:
   code A "1988-01-18T17:20:43.123456Z" and code B "1988-018T17:20:43.123456Z" are the same instant (18 January is day 018).
   parse of either == (1988, 1, 18, 17, 20, 43, "123456"); format_a of those fields gives the first text, format_b the second.
2. The Gregorian leap-year rule: 1900 and 2100 are not leap years, 2000 and 2400 are; 2016-12-31 ended with a positive leap second (IERS Bulletin C 52),
   written "2016-12-31T23:59:60Z".

Values derivable by hand (write the derivation in a comment):
- parse(text) returns a tuple (year, month, day, hour, minute, second, fraction): six ints and the fraction as a str of digits, "" when absent.
  parse("2026-10-07T02:45:10.250Z") == (2026, 10, 7, 2, 45, 10, "250"); the terminator Z is optional: parse("2026-10-07T02:45:10") == (2026, 10, 7, 2, 45, 10, "");
  code B: parse("2026-280T02:45:10Z") == (2026, 10, 7, 2, 45, 10, "") [31+28+31+30+31+30+31+31+30 = 273 days before October, 273 + 7 = 280];
  the fraction is kept as written: "250" is not "25"; parse("2026-10-07T02:45:10.000Z")[6] == "000"; 12 digits accepted: parse("2024-366T00:00:00.000000000001")[6] == "000000000001";
  parse("2024-366T00:00:00Z")[:3] == (2024, 12, 31); parse("2024-060T00:00:00Z")[:3] == (2024, 2, 29); parse("2023-060T00:00:00Z")[:3] == (2023, 3, 1);
  parse("0001-001T00:00:00Z") == (1, 1, 1, 0, 0, 0, ""); parse("9999-12-31T23:59:59Z")[:3] == (9999, 12, 31);
  the leap second: parse("2016-12-31T23:59:60Z") == (2016, 12, 31, 23, 59, 60, "") (accepted at 23:59 of ANY date: the module does not hold the leap-second table);
- format_a(2026, 10, 7, 2, 45, 10, "250") == "2026-10-07T02:45:10.250Z"; format_a(2026, 10, 7, 2, 45, 10) == "2026-10-07T02:45:10Z" (no point without digits);
  format_b(2026, 10, 7, 2, 45, 10) == "2026-280T02:45:10Z"; format_b(2024, 3, 1, 0, 0, 0) == "2024-061T00:00:00Z"; format_b(2023, 3, 1, 0, 0, 0) == "2023-060T00:00:00Z";
  format_a(1, 1, 1, 0, 0, 0) == "0001-01-01T00:00:00Z" and format_b(1, 1, 1, 0, 0, 0) == "0001-001T00:00:00Z" (zero padding); format_a(2016, 12, 31, 23, 59, 60) ==
  "2016-12-31T23:59:60Z"; the formatters always write the terminator Z;
- round trips: parse(format_a(*f)) == f and parse(format_b(*f)) == f for any valid fields f; format_a(*parse(t)) == t for any code A text t ending in Z;
- day_of_year(2026, 1, 1) == 1; day_of_year(2026, 12, 31) == 365; day_of_year(2024, 12, 31) == 366; day_of_year(2024, 3, 1) == 61; day_of_year(2023, 3, 1) == 60;
  day_of_year(2000, 3, 1) == 61 (leap); day_of_year(1900, 3, 1) == 60 and day_of_year(2100, 3, 1) == 60 (not leap); day_of_year(2026, 10, 7) == 280;
- month_day(2026, 280) == (10, 7); month_day(2024, 60) == (2, 29); month_day(2023, 60) == (3, 1); month_day(2026, 1) == (1, 1); month_day(2026, 365) == (12, 31);
  month_day(2024, 366) == (12, 31); month_day(year, day_of_year(year, m, d)) == (m, d) for every date.

Limits (state them): MAX_FRACTION_DIGITS == 12; years 1 to 9999. Refusals (ValueError):
- parse, not a str: None, 20261007, bytes ("must be a str");
- parse, wrong shape ("not a CCSDS ASCII time code"): lower-case "2026-10-07t02:45:10Z" and "2026-10-07T02:45:10z"; a space instead of T; leading or trailing spaces or a
  trailing newline; "2026-10-07T02:45Z" (no seconds); "2026-1-07T02:45:10Z", "2026-10-7T02:45:10Z", "2026-10-07T2:45:10Z" (widths); "20261007T024510Z" (basic format);
  "2026-10-07T02:45:10+00:00" (an offset); "ZZ"; a sign; "2026-10-07" (date only); "2026-10-07T02:45:10.Z" (a point with no digits); 13 fraction digits; a comma as the
  decimal mark; "2026/10/07T02:45:10Z"; "2026-W41-3T02:45:10Z" (week date); "26-10-07T02:45:10Z"; "12026-10-07T02:45:10Z"; "2026-0280T02:45:10Z"; full-width digits;
- parse, right shape but impossible value: "2026-02-29T00:00:00Z" and "1900-02-29T00:00:00Z" ("day"); "2026-04-31T00:00:00Z"; "2026-13-01T00:00:00Z" and
  "2026-00-10T00:00:00Z" ("month"); "2026-10-00T00:00:00Z"; "2026-366T00:00:00Z" and "2026-000T00:00:00Z" ("day of year"; "2024-366T00:00:00Z" is accepted);
  "0000-01-01T00:00:00Z" ("year"); "2026-10-07T24:00:00Z" ("hour"); "2026-10-07T02:60:10Z" ("minute"); "2026-10-07T12:00:60Z" and "2026-10-07T23:58:60Z" (second 60
  outside 23:59) and "2026-10-07T23:59:61Z" ("second");
- formatters and day functions: an argument that is a float (2026.0), a bool, a str, None; values out of range as above (format_b(2026, 2, 29, 0, 0, 0),
  day_of_year(2026, 4, 31), month_day(2026, 366), month_day(2026, 0), year 0 or 10000); a fraction that is not a str (25), has a non-digit ("2.5", "-5", " 5"),
  non-ASCII digits, or 13 digits ("fraction must be a string").
