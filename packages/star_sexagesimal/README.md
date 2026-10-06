# star_sexagesimal — degrees ⇄ degrees/minutes/seconds and hours/minutes/seconds

Splitting an angle into sexagesimal fields and joining them back, with the rounding done once on the whole angle so
that a field never shows 60. Standard library only.

```python
import star_sexagesimal as sx
sx.deg_to_dms(-23.4392911, 3)          # ('-', 23, 26, 21, 448): -23 deg 26' 21.448"
sx.deg_to_hms(267.248917, 4)           # ('+', 17, 48, 59, 7401): 17h 48m 59.7401s
sx.dms_to_deg('-', 14, 43, 8.2)        # -14.718944...
sx.hms_to_deg('+', 17, 48, 59.74)      # 267.248917...
```

## Requirements
- R1 `deg_to_dms(deg, decimals)` and `deg_to_hms(deg, decimals)` return (sign, whole, minutes, seconds, fraction)
  as a '+'/'-' sign and four integers, `fraction` in units of 10**-decimals second; rounding to the nearest unit,
  ties away from zero, once on the whole angle. Reproduce 23° 26' 21.448" and 17h 48m 59.74s (Meeus).
- R2 `dms_to_deg` and `hms_to_deg` join the fields; 15° = 1 h. No wrapping: 360° is 360° and 24 h.
- R3 Measured on 600 angles (100 within 1e-9 deg of a whole arcminute) and 600 sets of fields: rounded fields
  identical to ERFA in 1200 of 1200, never a 60; joined angle within 1.2e-13 deg of ERFA and astropy; unrounded
  seconds within 5e-7 s of astropy (the rounding step at six decimals).
- R4 Every function returns its result or raises `ValueError`: non-numeric, boolean, NaN or infinite input, an angle
  outside [-360, 360], decimals not an integer in 0…6, a sign other than '+' or '-', degrees not an integer in 0…360
  (hours 0…24), minutes not an integer in 0…59, seconds outside [0, 60), a total above 360° (24 h).

## Evidence
- Published: the IAU 1976 obliquity 23° 26' 21.448" = 23.4392911° and Meeus, Astronomical Algorithms, Example 13.b.
- `crosscheck_sexagesimal.py`: ERFA and astropy, each in its own interpreter, each probed on the published values.

## What is NOT claimed
No formatting to text and no parsing of text: fields in, fields out. No wrapping into [0, 360) or [0, 24 h).
At most six decimals of a second. A binary floating-point angle that is not exactly on a tie is rounded as the
float it is, not as the decimal it was typed as.
