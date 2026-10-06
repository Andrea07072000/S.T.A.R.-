# Published values the tests of star_sexagesimal may cite (checked by the reviewer against the computation)

1. IAU 1976 obliquity of the ecliptic at J2000.0: 23 deg 26' 21.448" = 84381.448" = 23.4392911 deg (Meeus, Astronomical
   Algorithms, ch. 22 and Example 13.a). deg_to_dms(23.4392911, 3) == ('+', 23, 26, 21, 448); dms_to_deg('+', 23, 26, 21.448)
   equals 84381.448 / 3600 (tolerance 1e-12 deg) and 23.4392911 within 2e-8 deg (the decimal is printed to 7 places).
2. Meeus Example 13.b: right ascension 17h 48m 59.74s = 267.248917 deg (printed to 6 places: tolerance 5e-7 deg),
   declination -14 deg 43' 08.2" = -14.718944 deg (tolerance 5e-7 deg).
   deg_to_hms(267.248917, 4) == ('+', 17, 48, 59, 7401); deg_to_dms(-14.718944, 1) == ('-', 14, 43, 8, 2).

Behaviour of the module (state it, do not call it published):
- fields are integers; `fraction` counts units of 10**-decimals second; rounding once on the whole angle, ties away from zero;
- a field never shows 60: deg_to_dms(0.9999999, 3) == ('+', 1, 0, 0, 0); deg_to_dms(59.9996 / 3600, 3) == ('+', 0, 1, 0, 0);
- sign is '+' or '-'; an angle that rounds to zero has sign '+': deg_to_dms(-1e-9, 3) == ('+', 0, 0, 0, 0);
  deg_to_dms(-0.5, 0) == ('-', 0, 30, 0, 0) keeps the sign of an angle between 0 and -1 deg;
- no wrapping: deg_to_dms(360, 3) == ('+', 360, 0, 0, 0); deg_to_hms(360, 4) == ('+', 24, 0, 0, 0); deg_to_hms(-180, 0) == ('-', 12, 0, 0, 0);
- 15 deg = 1 hour, 1 deg = 240 seconds of time: deg_to_hms(15.0, 0) == ('+', 1, 0, 0, 0); hms_to_deg('+', 1, 0, 0) == 15.0;
- by hand: 1.5 deg = 1 deg 30' 0"; 0.0125 deg = 45" ; 10.2625 deg = 10 deg 15' 45"; 1 arcsec = 1/3600 deg;
- ties away from zero: deg_to_dms(0.5 / 3600, 0) == ('+', 0, 0, 1, 0) and deg_to_dms(-0.5 / 3600, 0) == ('-', 0, 0, 1, 0)
  (0.5/3600 times 3600 is exactly 0.5 in binary floating point);
- join then split is the identity on fields whose seconds have at most `decimals` decimals;
- refusals: see the module docstring; note that seconds == 60 is refused, and that 360 deg 0' 1" (a total above 360 deg) is refused,
  as is 24h 0m 1s.
