# star_horizon — hour angle and declination ⇄ azimuth and elevation

Where an object is in the local sky, from its hour angle and declination and the observer's latitude, and back;
plus the parallactic angle. Geometry only. Standard library only.

```python
import star_horizon as sh
sh.hadec_to_azel(64.352133, -6.719892, 38.921389)        # (248.0337, 15.1249): Venus, Meeus Example 13.b
sh.azel_to_hadec(248.0337, 15.1249, 38.921389)           # back to hour angle and declination
sh.parallactic_angle_deg(64.352133, -6.719892, 38.921389)
```

## Requirements
- R1 `hadec_to_azel(ha, dec, lat)` returns azimuth from North through East in [0, 360) and elevation; hour angle
  is positive West of the meridian. Reproduces Meeus Example 13.b.
- R2 `azel_to_hadec(az, el, lat)` is its inverse, with the hour angle in (-180, 180];
  `parallactic_angle_deg(ha, dec, lat)` is the angle at the object between the pole and the zenith, in (-180, 180].
- R3 Measured on 600 cases (100 down to 1e-6 deg from the zenith, 100 at latitudes down to 1e-6 deg from a pole),
  in both directions: within 1.1e-13 deg of ERFA and of a SPICE rotation; parallactic angle identical to ERFA.
- R4 Every function returns finite floats or raises `ValueError`: non-numeric, boolean, NaN or infinite input,
  hour angle or azimuth outside [-360, 360], declination, elevation or latitude outside [-90, 90].

## Evidence
- Published: Meeus, Astronomical Algorithms, Example 13.b; meridian, pole and East/West-point cases by hand.
- `crosscheck_horizon.py`: ERFA and SPICE, each in its own interpreter, each probed on the published example.

## What is NOT claimed
No refraction, parallax, aberration, polar motion or deflection of the vertical: this is the geometric direction.
The parallactic angle is compared with one library (ERFA), with the same formula: the agreement shows the same
convention, not an independent derivation. The SPICE lineage uses SPICE routines composed in the driver. At the
zenith or nadir the azimuth is undefined, at a celestial pole the hour angle is undefined, at the zenith the
parallactic angle is undefined: 0 is returned there.
