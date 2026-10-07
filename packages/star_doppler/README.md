# star_doppler — range, range rate and one-way Doppler shift

The distance between two moving points, how fast it changes, and the frequency received over that link. Standard
library only.

```python
import star_doppler as dp
rng, rate = dp.range_and_rate((0, 0, 0), (0, 0, 0), (3, 4, 0), (1, 0, 0))    # (5.0, 0.6)
dp.received_frequency(2.2e9, 7.5)                 # 2199944962.61 Hz: an S-band carrier from a source receding at 7.5 km/s
dp.received_frequency(2.2e9, 7.5, relativistic=False)   # 2199944961.92 Hz: the first-order formula, 0.69 Hz lower
```

## Requirements
- R1 `range_and_rate(r_observer, v_observer, r_target, v_target)` returns the distance and the component of the
  relative velocity along the line of sight, positive when the two move apart. Any frame and units, the same for all.
- R2 `received_frequency(frequency, range_rate, relativistic=True)` returns f sqrt((1 − b)/(1 + b)) with
  b = range_rate / c, or the first-order f (1 − b) with `relativistic=False`; `C_KM_S` = 299792.458 km/s.
- R3 Measured on 600 pairs of states and range rates up to 0.9 c: range, range rate and both frequencies agree with
  NAIF SPICE (`vnorm`, `dvnorm`), astropy's Doppler equivalencies, NumPy and mpmath at 40 digits within 8.3e-16 of
  their natural scale (the relative speed for the range rate).
- R4 Every function returns floats or raises `ValueError`: vectors that are not three finite numbers within 1e15,
  coincident positions, a frequency that is not positive and finite, a range rate that reaches the speed of light,
  `relativistic` that is not a bool.

## Evidence
- Published: the SI value of the speed of light; the longitudinal relativistic Doppler factor. By hand: at 0.6 c the
  factor is exactly 0.5.
- `crosscheck_doppler.py`: SPICE, astropy, NumPy and mpmath, each in its own interpreter.

## What is NOT claimed
A geometric, instantaneous, one-way result: no light-time correction (the states must already refer to the right
instants), no two-way or coherent turn-around ratio, no transverse relativistic term (the relativistic formula is exact
only for motion along the line of sight; the neglected term is of order (v/c)², the same order as the difference
between the two formulas), no gravitational shift, no troposphere or ionosphere, no oscillator error. For a low orbit
those omissions are of the order of a hertz at S band: enough to plan a receiver bandwidth, not to do orbit
determination.
